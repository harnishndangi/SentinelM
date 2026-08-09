"""
Unit tests for SentinelML Production Drift Simulator API & Engine.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.drift import DriftEvent
from ml.registry.model_registry import ModelRegistry
from ml.simulator.drift_simulator import DriftSimulatorState


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session."""
    db_file = tmp_path / "test_simulator.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    registry = ModelRegistry(session)
    registry.register_candidate(
        model_name="FraudDetector",
        version="v1.0.0",
        algorithm="XGBoost",
    )

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(test_db):
    """TestClient with database session override."""
    def _override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db
    DriftSimulatorState().reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_high_transaction_amount_simulation(client, test_db):
    """Verifies POST /api/v1/simulator/drift with HIGH_TRANSACTION_AMOUNT scenario."""
    payload = {
        "scenario": "HIGH_TRANSACTION_AMOUNT",
        "intensity": 0.85,
        "records": 1000,
    }
    response = client.post("/api/v1/simulator/drift", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["scenario"] == "HIGH_TRANSACTION_AMOUNT"
    assert data["intensity"] == 0.85
    assert data["records_simulated"] == 1000
    assert data["status"] == "COMPLETED"

    result = data["drift_analysis_result"]
    assert result["is_actionable"] is True
    assert result["overall_status"] in ["HIGH", "CRITICAL"]

    # Verify real DriftEvent created in DB
    drift_event = test_db.query(DriftEvent).filter(DriftEvent.id == result["drift_event_id"]).first()
    assert drift_event is not None
    assert drift_event.is_actionable is True


def test_mobile_device_shift_simulation(client):
    """Verifies MOBILE_DEVICE_SHIFT scenario triggers categorical drift."""
    payload = {
        "scenario": "MOBILE_DEVICE_SHIFT",
        "intensity": 0.9,
        "records": 800,
    }
    res = client.post("/api/v1/simulator/drift", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "MOBILE_DEVICE_SHIFT"
    assert data["drift_analysis_result"]["is_actionable"] is True


def test_multi_feature_drift_simulation(client):
    """Verifies MULTI_FEATURE_DRIFT scenario triggers critical model drift."""
    payload = {
        "scenario": "MULTI_FEATURE_DRIFT",
        "intensity": 0.95,
        "records": 1000,
    }
    res = client.post("/api/v1/simulator/drift", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario"] == "MULTI_FEATURE_DRIFT"
    assert data["drift_analysis_result"]["overall_status"] in ["HIGH", "CRITICAL"]


def test_simulator_status_endpoint(client):
    """Verifies GET /api/v1/simulator/status returns current active simulation state."""
    client.post("/api/v1/simulator/drift", json={"scenario": "NEW_REGION", "intensity": 0.8, "records": 500})

    res = client.get("/api/v1/simulator/status")
    assert res.status_code == 200
    status_data = res.json()

    assert status_data["is_active"] is True
    assert status_data["active_scenario"] == "NEW_REGION"
    assert status_data["intensity"] == 0.8
    assert status_data["total_simulated_records"] >= 500
    assert status_data["latest_drift_status"] is not None


def test_simulator_reset_endpoint(client):
    """Verifies POST /api/v1/simulator/reset restores baseline distributions."""
    # First trigger drift
    client.post("/api/v1/simulator/drift", json={"scenario": "HIGH_TRANSACTION_AMOUNT", "intensity": 0.8, "records": 500})

    # Reset
    res = client.post("/api/v1/simulator/reset")
    assert res.status_code == 200
    reset_data = res.json()
    assert reset_data["status"] == "RESET"

    # Check status endpoint after reset
    status_res = client.get("/api/v1/simulator/status")
    assert status_res.status_code == 200
    s_data = status_res.json()
    assert s_data["is_active"] is False
    assert s_data["active_scenario"] is None
    assert s_data["latest_drift_status"]["overall_status"] == "NONE"
