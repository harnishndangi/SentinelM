"""
Unit tests for FastAPI Fraud Prediction API & PredictionService.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.prediction import Prediction
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def test_db(tmp_path):
    """Isolated SQLite database for API testing."""
    db_file = tmp_path / "test_predict.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    # Pre-register a production model in the isolated test DB
    registry = ModelRegistry(session)
    registry.register_candidate(
        model_name="SentinelML-FraudDetection",
        version="v1.0.0",
        algorithm="LogisticRegression",
        artifact_path="artifacts/models/fraud_detector/v1/model.joblib",
    )
    registry.promote_model("SentinelML-FraudDetection", "v1.0.0", target_status="PRODUCTION")

    try:
        yield session, engine
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client_with_db(test_db):
    """FastAPI TestClient with overridden get_db dependency."""
    session, _ = test_db

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_predict_single_endpoint(client_with_db):
    """Verifies POST /api/v1/predict single transaction prediction endpoint."""
    payload = {
        "features": {
            "amount": 1500.0,
            "oldbalanceOrg": 5000.0,
            "newbalanceOrig": 3500.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 1500.0,
        }
    }
    response = client_with_db.post("/api/v1/predict", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert "prediction" in data
    assert data["prediction"] in [0, 1]
    assert "fraud_probability" in data
    assert 0.0 <= data["fraud_probability"] <= 1.0
    assert "model" in data
    assert "model_version" in data
    assert "prediction_id" in data
    assert data["prediction_id"].startswith("pred_")
    assert "latency_ms" in data
    assert data["latency_ms"] >= 0.0


def test_predict_batch_endpoint(client_with_db):
    """Verifies POST /api/v1/predict/batch endpoint."""
    payload = {
        "transactions": [
            {
                "transaction_id": "tx_101",
                "features": {"amount": 50.0, "oldbalanceOrg": 200.0, "newbalanceOrig": 150.0},
            },
            {
                "transaction_id": "tx_102",
                "features": {"amount": 950000.0, "oldbalanceOrg": 950000.0, "newbalanceOrig": 0.0},
            },
        ]
    }
    response = client_with_db.post("/api/v1/predict/batch", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_transactions"] == 2
    assert "batch_latency_ms" in data
    assert len(data["predictions"]) == 2
    assert data["predictions"][0]["prediction_id"].startswith("pred_")
    assert data["predictions"][1]["prediction_id"].startswith("pred_")


def test_prediction_persisted_to_db(test_db, client_with_db):
    """Verifies prediction records are persisted to DB."""
    session, _ = test_db
    payload = {"features": {"amount": 250.0, "oldbalanceOrg": 500.0, "newbalanceOrig": 250.0}}
    res = client_with_db.post("/api/v1/predict", json=payload)
    assert res.status_code == 200
    pred_id = res.json()["prediction_id"]

    db_record = session.query(Prediction).filter(Prediction.prediction_id == pred_id).first()
    assert db_record is not None
    assert db_record.input_features["amount"] == 250.0
    assert db_record.output_prediction["prediction"] in [0, 1]
