"""
Unit tests for SentinelML Root Cause Analysis (RCA) Engine & API.
"""
import pytest
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.incident import Incident
from ml.explainability.root_cause import RootCauseAnalyzer
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session."""
    db_file = tmp_path / "test_rca.db"
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


def test_root_cause_analyzer_calculation():
    """Verifies RootCauseAnalyzer metrics shift, SHAP ranking, and segment degradation."""
    np.random.seed(42)

    # Train a simple XGBoost model
    X_train = pd.DataFrame({
        "amount": np.random.exponential(50.0, 500),
        "device_age": np.random.uniform(30, 500, 500),
        "distance": np.random.exponential(10.0, 500),
    })
    y_train = (X_train["amount"] > 120.0).astype(int)

    model = XGBClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # Create baseline reference vs shifted current production datasets
    ref_df = pd.DataFrame({
        "amount": np.random.exponential(50.0, 500),
        "device_age": np.random.uniform(30, 500, 500),
        "distance": np.random.exponential(10.0, 500),
        "region": np.random.choice(["north_america", "europe"], size=500),
        "is_fraud": y_train,
    })
    ref_df["prediction"] = model.predict(ref_df[["amount", "device_age", "distance"]])

    cur_df = pd.DataFrame({
        "amount": np.random.lognormal(mean=5.5, sigma=0.8, size=500),  # Heavy drift
        "device_age": np.random.uniform(30, 500, 500),
        "distance": np.random.exponential(10.0, 500),
        "region": np.random.choice(["north_america", "offshore_island"], size=500, p=[0.2, 0.8]),
        "is_fraud": np.random.choice([0, 1], size=500, p=[0.7, 0.3]),
    })
    cur_df["prediction"] = model.predict(cur_df[["amount", "device_age", "distance"]])

    analyzer = RootCauseAnalyzer()
    rca_res = analyzer.analyze_root_cause(
        model_name="FraudDetector",
        model_version="v1.0.0",
        ref_df=ref_df,
        cur_df=cur_df,
        model=model,
    )

    assert "model" in rca_res
    assert "performance_change" in rca_res
    assert "contributors" in rca_res
    assert "affected_segments" in rca_res

    # Amount or region should be in top root cause contributors
    top_features = [c["feature"] for c in rca_res["contributors"]]
    assert any(f in top_features for f in ["amount", "transaction_amount", "region"])
    assert rca_res["contributors"][0]["contribution"] > 0.0

    # Affected segments must identify offshore_island / region segment
    assert len(rca_res["affected_segments"]) > 0
    seg_fields = [s["segment_field"] for s in rca_res["affected_segments"]]
    assert "region" in seg_fields or "transaction_value_range" in seg_fields


def test_incident_rca_api_and_db_persistence(client, test_db):
    """
    Verifies creating an incident, calling POST /api/v1/incidents/{id}/rca endpoint,
    and verifying rca_result is persisted in PostgreSQL/SQLite Incident table.
    """
    session, model_ver_id = test_db

    # Create incident via POST /api/v1/incidents
    create_res = client.post(
        "/api/v1/incidents",
        json={
            "model_version_id": model_ver_id,
            "title": "Model Performance Drop & Feature Shift",
            "description": "F1 score degraded by 12% following distribution shift",
            "severity": "HIGH",
        },
    )
    assert create_res.status_code == 201, create_res.text
    inc_id = create_res.json()["id"]

    # Execute RCA endpoint
    rca_res = client.post(f"/api/v1/incidents/{inc_id}/rca")
    assert rca_res.status_code in [200, 202], rca_res.text
    rca_data = rca_res.json()

    if rca_res.status_code == 202:
        assert "job_id" in rca_data
        assert rca_data["incident_id"] == inc_id
        from backend.app.workers.incident_worker import generate_incident_report_task
        generate_incident_report_task(incident_id=inc_id, db_session=session)

    # Verify rca_result saved in Incident DB record
    inc_db = session.query(Incident).filter(Incident.id == inc_id).first()
    assert inc_db is not None
    assert "model" in inc_db.rca_result


    # Fetch incident via GET endpoint
    get_res = client.get(f"/api/v1/incidents/{inc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["rca_result"] is not None
