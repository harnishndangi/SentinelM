"""
Unit tests for SentinelML Incident Management Engine & REST API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.incident import Incident, IncidentEvent
from ml.drift.drift_engine import DriftEngine
from ml.registry.model_registry import ModelRegistry
from ml.simulator.drift_simulator import DriftSimulator


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session."""
    db_file = tmp_path / "test_incidents.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    registry = ModelRegistry(session)
    ver_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.0.0",
        algorithm="XGBoost",
    )
    model_ver_id = ver_dict["model_id"]

    try:
        yield session, model_ver_id
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(test_db):
    """TestClient with database session override."""
    session, _ = test_db

    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_automated_incident_creation_on_drift(test_db):
    """
    Verifies that when DriftEngine detects HIGH/CRITICAL drift,
    an Incident is automatically created with complete timeline events and RCA findings.
    """
    session, model_ver_id = test_db

    simulator = DriftSimulator(session)
    ref_df = simulator.get_baseline_reference_data(num_records=1000)
    cur_df = simulator.apply_drift_scenario(ref_df, scenario="MULTI_FEATURE_DRIFT", intensity=0.9)

    drift_engine = DriftEngine(db=session)
    report = drift_engine.run_drift_analysis(
        reference_data=ref_df,
        current_data=cur_df,
        model_version_id=model_ver_id,
        save_to_db=True,
    )

    assert report["overall_status"] in ["HIGH", "CRITICAL"]
    assert "incident_id" in report

    # Query DB for created incident
    inc_db = session.query(Incident).filter(Incident.id == report["incident_id"]).first()
    assert inc_db is not None
    assert inc_db.model_version_id == model_ver_id
    assert inc_db.status.value == "OPEN"
    assert inc_db.recommended_action == "RETRAIN_MODEL"
    assert inc_db.rca_result is not None

    # Query DB for timeline events
    events = session.query(IncidentEvent).filter(IncidentEvent.incident_id == inc_db.id).all()
    event_types = [e.event_type for e in events]

    assert "DRIFT_DETECTED" in event_types
    assert "INCIDENT_CREATED" in event_types
    assert "ROOT_CAUSE_STARTED" in event_types
    assert "ROOT_CAUSE_COMPLETED" in event_types


def test_incidents_api_endpoints(client, test_db):
    """
    Verifies GET /api/v1/incidents, GET /api/v1/incidents/{id},
    and POST /api/v1/incidents/{id}/resolve endpoints.
    """
    session, model_ver_id = test_db

    # Create incident manually via POST /api/v1/incidents
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "model_version_id": model_ver_id,
            "title": "Manual Performance Degradation Incident",
            "description": "F1 score dropped on production stream",
            "severity": "CRITICAL",
        },
    )
    assert create_res.status_code == 201
    inc_id = create_res.json()["id"]

    # 1. Test GET /api/v1/incidents list
    list_res = client.get("/api/v1/incidents")
    assert list_res.status_code == 200
    inc_list = list_res.json()
    assert len(inc_list) >= 1
    assert any(i["incident_id"] == inc_id for i in inc_list)

    # 2. Test GET /api/v1/incidents/{id} detail with timeline visualization payload
    get_res = client.get(f"/api/v1/incidents/{inc_id}")
    assert get_res.status_code == 200
    inc_detail = get_res.json()

    assert inc_detail["incident_id"] == inc_id
    assert inc_detail["model_name"] == "FraudDetector"
    assert inc_detail["model_version"] == "v1.0.0"
    assert inc_detail["status"] == "OPEN"
    assert "timeline" in inc_detail
    assert isinstance(inc_detail["timeline"], list)

    # 3. Test POST /api/v1/incidents/{id}/resolve endpoint
    resolve_res = client.post(
        f"/api/v1/incidents/{inc_id}/resolve",
        json={"notes": "Model retrained and deployed to production."},
    )
    assert resolve_res.status_code == 200
    resolved_detail = resolve_res.json()

    assert resolved_detail["status"] == "RESOLVED"
    assert resolved_detail["resolved_at"] is not None

    # Check updated timeline contains INCIDENT_RESOLVED event
    timeline_event_types = [e["event_type"] for e in resolved_detail["timeline"]]
    assert "INCIDENT_RESOLVED" in timeline_event_types
