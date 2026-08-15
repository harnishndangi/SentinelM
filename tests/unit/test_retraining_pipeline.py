"""
Unit and integration tests for SentinelML Automated Retraining Pipeline & REST API.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db, SessionLocal
from backend.app.models.incident import Incident, IncidentEvent
from backend.app.models.model import ModelVersion
from ml.registry.model_registry import ModelRegistry

from pipelines.retraining_flow import (
    automated_retraining_flow,
    get_run_state,
    acquire_retraining_lock,
    release_retraining_lock,
    update_run_state,
)


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session and default ModelVersion."""
    db_file = tmp_path / "test_retraining.db"
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


def test_retraining_lock_prevents_simultaneous_runs():
    """
    Verifies that lock management prevents concurrent retraining runs for the same incident.
    """
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    run_id_1 = f"run-1-{uuid.uuid4().hex[:8]}"
    run_id_2 = f"run-2-{uuid.uuid4().hex[:8]}"

    try:
        # Acquire lock for run 1
        assert acquire_retraining_lock(incident_id, run_id_1) is True

        # Attempt to acquire lock for run 2 on same incident (must fail)
        assert acquire_retraining_lock(incident_id, run_id_2) is False

    finally:
        # Release lock for run 1
        release_retraining_lock(incident_id, run_id_1)

    # Now run 2 should be able to acquire lock
    assert acquire_retraining_lock(incident_id, run_id_2) is True
    release_retraining_lock(incident_id, run_id_2)


def test_retraining_flow_execution():
    """
    Verifies full execution of automated_retraining_flow across all steps:
    Drift detected -> Incident created -> Dataset snapshot -> Data validation ->
    Feature preprocessing -> Candidate training -> Hyperparameter optimization ->
    Evaluation -> Candidate registration.
    """
    run_id = str(uuid.uuid4())
    res = automated_retraining_flow(model_type="xgboost", run_id=run_id)

    assert res is not None
    assert res["status"] == "COMPLETED"
    assert res["current_step"] == "Candidate Registration"
    assert "candidate_version" in res
    assert res["run_id"] == run_id

    # Check state store
    state = get_run_state(run_id)
    assert state is not None
    assert state["status"] == "COMPLETED"
    assert len(state["steps_completed"]) >= 8


def test_retraining_api_endpoints(client):
    """
    Verifies POST /api/v1/retraining/trigger and GET /api/v1/retraining/{run_id}.
    """
    # 1. Trigger retraining flow synchronously via API
    response = client.post(
        "/api/v1/retraining/trigger",
        json={
            "model_type": "xgboost",
            "async_execution": False,
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert "run_id" in data
    run_id = data["run_id"]
    assert data["message"] == "Automated retraining pipeline initiated successfully."

    # 2. Get retraining status via GET /api/v1/retraining/{run_id}
    status_res = client.get(f"/api/v1/retraining/{run_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["run_id"] == run_id
    assert status_data["status"] == "COMPLETED"

    # 3. Test 404 for invalid run_id
    invalid_res = client.get("/api/v1/retraining/nonexistent-run-id")
    assert invalid_res.status_code == 404


def test_retraining_api_duplicate_lock_conflict(client):
    """
    Verifies that triggering retraining for an incident that is already retraining
    returns HTTP 409 Conflict.
    """
    incident_id = f"inc-lock-test-{uuid.uuid4().hex[:8]}"
    existing_run_id = f"active-run-{uuid.uuid4().hex[:8]}"

    # Simulate active lock
    acquire_retraining_lock(incident_id, existing_run_id)

    try:
        response = client.post(
            "/api/v1/retraining/trigger",
            json={
                "incident_id": incident_id,
                "async_execution": False,
            },
        )
        assert response.status_code == 409
        assert f"Retraining job for incident '{incident_id}' is already in progress." in response.json()["detail"]
    finally:
        release_retraining_lock(incident_id, existing_run_id)
