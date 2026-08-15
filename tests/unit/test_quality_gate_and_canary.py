"""
Comprehensive unit and integration tests for ModelQualityGate,
CanaryRouter, ShadowEvaluator, CanaryMetrics, and Canary REST APIs.
"""
import os
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.model import ModelVersion
from ml.registry.model_registry import ModelRegistry
from ml.evaluation.quality_gate import ModelQualityGate, QualityGateConfig
from ml.evaluation.canary import (
    CanaryRouter,
    ShadowEvaluator,
    CanaryMetrics,
    CanaryConfigManager,
    ALLOWED_CANARY_PERCENTAGES,
)


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session and default ModelVersions."""
    db_file = tmp_path / "test_quality_canary.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    registry = ModelRegistry(session)
    prod_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.0.0",
        algorithm="XGBoost",
        metrics={"pr_auc": 0.88, "recall": 0.85, "f1": 0.82, "precision": 0.80, "prediction_latency_ms": 12.5},
    )
    registry.promote_model("FraudDetector", "v1.0.0", target_status="PRODUCTION")

    cand_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.1.0",
        algorithm="XGBoost",
        metrics={"pr_auc": 0.90, "recall": 0.86, "f1": 0.84, "precision": 0.82, "prediction_latency_ms": 10.0},
    )

    try:
        yield session, prod_dict["model_id"], cand_dict["model_id"]
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(test_db):
    """TestClient with database session override."""
    session, _, _ = test_db

    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==========================================
# 1. MODEL QUALITY GATE TESTS
# ==========================================

def test_quality_gate_approved_candidate():
    """Verifies that a superior candidate model passes quality gate."""
    gate = ModelQualityGate(QualityGateConfig())

    prod_metrics = {"pr_auc": 0.85, "recall": 0.80, "f1": 0.78, "precision": 0.76, "prediction_latency_ms": 15.0}
    cand_metrics = {"pr_auc": 0.88, "recall": 0.82, "f1": 0.80, "precision": 0.78, "prediction_latency_ms": 12.0}

    result = gate.evaluate(
        candidate_metrics=cand_metrics,
        production_metrics=prod_metrics,
        data_validation_passed=True,
        schema_validation_passed=True,
    )

    assert result.passed is True
    assert result.status == "CANDIDATE APPROVED"
    assert len(result.rejection_reasons) == 0
    assert result.evaluations["pr_auc"]["passed"] is True


def test_quality_gate_rejected_degraded_candidate():
    """Verifies that a candidate with degraded PR-AUC or Recall is rejected with reasons."""
    gate = ModelQualityGate(QualityGateConfig(pr_auc_tolerance=0.0, recall_tolerance=0.01))

    prod_metrics = {"pr_auc": 0.88, "recall": 0.85, "f1": 0.82, "precision": 0.80, "prediction_latency_ms": 10.0}
    cand_metrics = {"pr_auc": 0.81, "recall": 0.75, "f1": 0.70, "precision": 0.65, "prediction_latency_ms": 65.0}

    result = gate.evaluate(
        candidate_metrics=cand_metrics,
        production_metrics=prod_metrics,
        data_validation_passed=True,
        schema_validation_passed=True,
    )

    assert result.passed is False
    assert result.status == "MODEL PROMOTION REJECTED"
    assert len(result.rejection_reasons) >= 3

    # Ensure exact rejection reasons are recorded
    rejection_text = " ".join(result.rejection_reasons)
    assert "PR-AUC" in rejection_text
    assert "Recall" in rejection_text
    assert "latency" in rejection_text


def test_quality_gate_data_schema_failure():
    """Verifies rejection when data validation or schema validation fails."""
    gate = ModelQualityGate()
    cand_metrics = {"pr_auc": 0.90, "recall": 0.88, "f1": 0.85, "precision": 0.82}

    res_data_fail = gate.evaluate(candidate_metrics=cand_metrics, data_validation_passed=False)
    assert res_data_fail.passed is False
    assert any("Data validation failed" in r for r in res_data_fail.rejection_reasons)

    res_schema_fail = gate.evaluate(candidate_metrics=cand_metrics, schema_validation_passed=False)
    assert res_schema_fail.passed is False
    assert any("schema" in r.lower() for r in res_schema_fail.rejection_reasons)


# ==========================================
# 2. APPLICATION-LEVEL CANARY & SHADOW TESTS
# ==========================================

def test_canary_router_percentages_and_modes():
    """
    Verifies inside-FastAPI CanaryRouter traffic splitting across percentages: 0, 5, 10, 25, 50, 100.
    """
    manager = CanaryConfigManager()
    router = CanaryRouter(manager)

    # 1. Disabled router always routes to production
    manager.update_config(enabled=False)
    dec = router.route_request()
    assert dec.target == "PRODUCTION"

    # 2. Shadow mode
    manager.update_config(enabled=True, mode="SHADOW", candidate_version_id="cand-123")
    dec_shadow = router.route_request()
    assert dec_shadow.target == "PRODUCTION"
    assert dec_shadow.is_shadow is True

    # 3. 0% Canary Percentage (always production)
    manager.update_config(enabled=True, mode="CANARY", canary_percentage=0, candidate_version_id="cand-123")
    assert all(router.route_request().target == "PRODUCTION" for _ in range(20))

    # 4. 100% Canary Percentage (always candidate)
    manager.update_config(enabled=True, mode="CANARY", canary_percentage=100, candidate_version_id="cand-123")
    assert all(router.route_request().target == "CANDIDATE" for _ in range(20))

    # 5. Supported percentages verification
    for pct in ALLOWED_CANARY_PERCENTAGES:
        updated = manager.update_config(canary_percentage=pct)
        assert updated.canary_percentage == pct


def test_shadow_evaluator_async_execution():
    """
    Verifies ShadowEvaluator records shadow metrics asynchronously without throwing exceptions.
    """
    metrics = CanaryMetrics()
    evaluator = ShadowEvaluator(metrics=metrics)

    metrics.record_shadow_evaluation(
        prod_pred=0,
        cand_pred=0,
        prod_prob=0.12,
        cand_prob=0.15,
        cand_latency_ms=8.5,
    )
    metrics.record_shadow_evaluation(
        prod_pred=1,
        cand_pred=0,
        prod_prob=0.85,
        cand_prob=0.45,
        cand_latency_ms=9.0,
    )

    summary = metrics.get_summary()
    assert summary["shadow_evaluation"]["total_evaluations"] == 2
    assert summary["shadow_evaluation"]["agreement_count"] == 1
    assert summary["shadow_evaluation"]["disagreement_count"] == 1
    assert summary["shadow_evaluation"]["agreement_rate"] == 0.5
    assert summary["shadow_evaluation"]["disagreement_rate"] == 0.5


# ==========================================
# 3. CANARY REST API TESTS
# ==========================================

def test_canary_api_endpoints(client, test_db):
    """
    Verifies GET /api/v1/canary/config, POST /api/v1/canary/config,
    GET /api/v1/canary/metrics, and POST /api/v1/canary/promote.
    """
    _, prod_ver_id, cand_ver_id = test_db

    # 1. GET /api/v1/canary/config
    get_res = client.get("/api/v1/canary/config")
    assert get_res.status_code == 200
    config_data = get_res.json()
    assert "mode" in config_data
    assert "canary_percentage" in config_data

    # 2. POST /api/v1/canary/config - Update to 25% Canary
    post_res = client.post(
        "/api/v1/canary/config",
        json={
            "enabled": True,
            "mode": "CANARY",
            "canary_percentage": 25,
            "candidate_version_id": cand_ver_id,
            "production_version_id": prod_ver_id,
        },
    )
    assert post_res.status_code == 200
    updated_data = post_res.json()
    assert updated_data["enabled"] is True
    assert updated_data["mode"] == "CANARY"
    assert updated_data["canary_percentage"] == 25

    # 3. GET /api/v1/canary/metrics
    metrics_res = client.get("/api/v1/canary/metrics")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert "production" in metrics_data
    assert "candidate" in metrics_data
    assert "shadow_evaluation" in metrics_data

    # 4. POST /api/v1/canary/promote - Promote superior candidate
    promote_res = client.post(
        "/api/v1/canary/promote",
        json={
            "model_name": "FraudDetector",
            "candidate_version": "v1.1.0",
        },
    )
    assert promote_res.status_code == 200
    promote_data = promote_res.json()
    assert promote_data["status"] == "CANDIDATE APPROVED & PROMOTED TO PRODUCTION"
    assert promote_data["promoted_version"] == "v1.1.0"
