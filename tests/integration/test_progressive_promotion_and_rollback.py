"""
Integration tests for Progressive Model Promotion and Automatic Rollback Engine.
Covering:
1. Successful progressive promotion (Quality Gate -> Shadow -> Canary 10% -> 25% -> 50% -> 100% Production).
2. Failed canary rollback (Deactivates candidate, restores production model, updates registry & deployment,
   creates audit log, adds incident event, notifies frontend, preserves artifacts).
3. Progressive promotion REST APIs.
"""

import os
import joblib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models.model import ModelVersion
from backend.app.models.deployment import Deployment
from backend.app.models.audit import AuditLog
from backend.app.models.incident import Incident, IncidentEvent
from backend.app.core.enums import ModelVersionStatus, DeploymentStatus, IncidentSeverity, IncidentStatus
from ml.registry.model_registry import ModelRegistry
from ml.evaluation.canary import CanaryConfigManager
from ml.evaluation.progressive_promotion import (
    ProgressivePromotionManager,
    PromotionThresholds,
)


class DummyModel:
    def predict(self, X):
        return [0] * len(X)
    def predict_proba(self, X):
        return [[0.8, 0.2]] * len(X)


@pytest.fixture
def test_db_environment(tmp_path):
    """
    Sets up an isolated SQLite database, fake model artifacts on disk, and ModelVersions for testing.
    """
    db_file = tmp_path / "test_progressive_rollback.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    # Create fake model artifacts on disk
    model_dir_v1 = tmp_path / "models" / "v1"
    model_dir_v2 = tmp_path / "models" / "v2"
    model_dir_v1.mkdir(parents=True, exist_ok=True)
    model_dir_v2.mkdir(parents=True, exist_ok=True)

    artifact_v1_path = str(model_dir_v1 / "model.joblib")
    artifact_v2_path = str(model_dir_v2 / "model.joblib")

    joblib.dump(DummyModel(), artifact_v1_path)
    joblib.dump(DummyModel(), artifact_v2_path)

    # Register initial production model v1.0.0
    registry = ModelRegistry(session)
    v1_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.0.0",
        algorithm="XGBoost",
        artifact_path=artifact_v1_path,
        metrics={"pr_auc": 0.85, "recall": 0.80, "f1": 0.78, "precision": 0.76, "prediction_latency_ms": 12.0},
    )
    registry.promote_model("FraudDetector", "v1.0.0", target_status=ModelVersionStatus.PRODUCTION)

    # Register candidate model v1.1.0
    v2_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.1.0",
        algorithm="XGBoost",
        artifact_path=artifact_v2_path,
        metrics={"pr_auc": 0.89, "recall": 0.84, "f1": 0.81, "precision": 0.79, "prediction_latency_ms": 10.0},
    )

    # Create associated Incident in DB
    incident = Incident(
        model_version_id=v1_dict["model_id"],
        title="Drift Incident for Progressive Promotion Test",
        description="Testing automated recovery and canary promotion",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.RETRAINING,
    )
    session.add(incident)
    session.commit()
    session.refresh(incident)

    try:
        yield session, v1_dict, v2_dict, incident.id, artifact_v1_path, artifact_v2_path
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(test_db_environment):
    """TestClient with database session override."""
    session, _, _, _, _, _ = test_db_environment

    def _override_get_db():
        yield session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_successful_progressive_promotion_flow(test_db_environment):
    """
    Verifies full successful progressive promotion:
    Quality Gate -> Shadow -> Canary 10% -> Canary 25% -> Canary 50% -> 100% Production.
    """
    session, v1_dict, v2_dict, incident_id, _, _ = test_db_environment

    promo_mgr = ProgressivePromotionManager(session)
    canary_mgr = CanaryConfigManager()

    # Step 1: Start Promotion Pipeline (passes Quality Gate -> transitions to SHADOW)
    state = promo_mgr.start_promotion_pipeline(
        model_name="FraudDetector",
        candidate_version="v1.1.0",
        incident_id=incident_id,
    )
    assert state.status == "IN_PROGRESS"
    assert state.current_stage == "SHADOW"
    assert canary_mgr.get_config().mode == "SHADOW"

    # Step 2: Advance to Canary 10%
    state = promo_mgr.advance_stage(state)
    assert state.current_stage == "CANARY_10"
    assert canary_mgr.get_config().canary_percentage == 10

    # Step 3: Advance to Canary 25%
    state = promo_mgr.advance_stage(state)
    assert state.current_stage == "CANARY_25"
    assert canary_mgr.get_config().canary_percentage == 25

    # Step 4: Advance to Canary 50%
    state = promo_mgr.advance_stage(state)
    assert state.current_stage == "CANARY_50"
    assert canary_mgr.get_config().canary_percentage == 50

    # Step 5: Advance to 100% Production
    state = promo_mgr.advance_stage(state)
    assert state.current_stage == "PROMOTED_100"
    assert state.status == "COMPLETED"

    # Check ModelRegistry shows v1.1.0 as PRODUCTION
    prod_model = ModelRegistry(session).get_production_model("FraudDetector")
    assert prod_model is not None
    assert prod_model["version"] == "v1.1.0"


def test_failed_canary_rollback_execution(test_db_environment):
    """
    Verifies that when metrics deteriorate during canary evaluation, immediate rollback triggers:
    - Candidate deactivated
    - Previous production model restored
    - Registry updated
    - Deployment record updated (ROLLED_BACK)
    - Audit log created
    - Incident event created
    - Frontend notified
    - Production artifact NOT deleted on disk
    """
    session, v1_dict, v2_dict, incident_id, artifact_v1_path, _ = test_db_environment

    promo_mgr = ProgressivePromotionManager(session)
    canary_mgr = CanaryConfigManager()

    # 1. Start pipeline -> SHADOW
    state = promo_mgr.start_promotion_pipeline(
        model_name="FraudDetector",
        candidate_version="v1.1.0",
        incident_id=incident_id,
    )
    assert state.current_stage == "SHADOW"

    # 2. Advance to CANARY_10
    state = promo_mgr.advance_stage(state)
    assert state.current_stage == "CANARY_10"

    # 3. Simulate severe live metric degradation (PR-AUC drop and high error rate)
    degraded_live_metrics = {
        "pr_auc": 0.35,  # Below 0.50 threshold
        "error_rate": 0.20,  # Exceeds 5% max error rate
    }

    # 4. Advance stage with degraded metrics -> Triggers immediate ROLLBACK
    state = promo_mgr.advance_stage(state, candidate_live_metrics=degraded_live_metrics)

    # ASSERTIONS:
    # A. State updated to ROLLED_BACK
    assert state.status == "ROLLED_BACK"
    assert state.rollback_reason is not None
    assert "PR-AUC" in state.rollback_reason or "error rate" in state.rollback_reason

    # B. Candidate deactivated (canary config disabled)
    config = canary_mgr.get_config()
    assert config.enabled is False

    # C. ModelRegistry updated: Candidate marked FAILED, Previous Production restored
    registry = ModelRegistry(session)
    prod_model = registry.get_production_model("FraudDetector")
    assert prod_model is not None
    assert prod_model["version"] == "v1.0.0"

    cand_ver = session.query(ModelVersion).filter(ModelVersion.id == v2_dict["id"]).first()
    assert cand_ver.status.value == "FAILED"

    # D. Deployment updated to ROLLED_BACK for candidate, ACTIVE for production
    cand_dep = session.query(Deployment).filter(Deployment.model_version_id == v2_dict["id"]).first()
    assert cand_dep is not None
    assert cand_dep.status == DeploymentStatus.ROLLED_BACK

    prod_dep = session.query(Deployment).filter(Deployment.model_version_id == v1_dict["id"]).first()
    assert prod_dep is not None
    assert prod_dep.status == DeploymentStatus.ACTIVE

    # E. AuditLog created in DB
    audit_log = (
        session.query(AuditLog)
        .filter(AuditLog.action == "CANARY_ROLLBACK_EXECUTED")
        .first()
    )
    assert audit_log is not None
    assert audit_log.resource_id == v2_dict["id"]
    assert audit_log.details["candidate_version"] == "v1.1.0"
    assert audit_log.details["restored_production_version"] == "v1.0.0"

    # F. IncidentEvent added to DB timeline
    inc_event = (
        session.query(IncidentEvent)
        .filter(IncidentEvent.incident_id == incident_id, IncidentEvent.event_type == "CANARY_ROLLBACK_EXECUTED")
        .first()
    )
    assert inc_event is not None
    assert "v1.0.0" in inc_event.message

    # G. Frontend notification stored
    notifications = canary_mgr.get_notifications()
    assert len(notifications) >= 1
    assert any(n.get("type") == "CANARY_ROLLBACK" for n in notifications)

    # H. NEVER delete previous production model artifact on disk
    assert os.path.exists(artifact_v1_path) is True


def test_progressive_promotion_api_endpoints(client, test_db_environment):
    """
    Verifies REST APIs:
    POST /api/v1/canary/progressive-promotion/start
    POST /api/v1/canary/progressive-promotion/advance
    GET /api/v1/canary/notifications
    """
    _, _, _, incident_id, _, _ = test_db_environment

    # 1. Start Progressive Promotion via API
    start_res = client.post(
        "/api/v1/canary/progressive-promotion/start",
        json={
            "model_name": "FraudDetector",
            "candidate_version": "v1.1.0",
            "incident_id": incident_id,
        },
    )
    assert start_res.status_code == 200
    state_payload = start_res.json()
    assert state_payload["status"] == "IN_PROGRESS"
    assert state_payload["current_stage"] == "SHADOW"

    # 2. Advance stage via API
    advance_res = client.post(
        "/api/v1/canary/progressive-promotion/advance",
        json={
            "state": state_payload,
        },
    )
    assert advance_res.status_code == 200
    advanced_state = advance_res.json()
    assert advanced_state["current_stage"] == "CANARY_10"

    # 3. Fetch notifications via API
    notif_res = client.get("/api/v1/canary/notifications")
    assert notif_res.status_code == 200
    assert isinstance(notif_res.json(), list)
