"""
Unit tests for SentinelML Model Registry Layer.

Tests model lifecycle transitions:
TRAINING -> CANDIDATE -> STAGING -> PRODUCTION -> ARCHIVED.

Verifies:
- Linking of MLflow run artifacts and parameters to PostgreSQL records.
- Single active production version rule per model.
- Automatic demotion of previous production version on new version promotion.
- AuditLog generation for every lifecycle event.
- Rollback and Archive operations.
"""
import uuid
import pytest
from sqlalchemy.orm import Session

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.database import Base
from backend.app.models.audit import AuditLog
from backend.app.models.model import ModelVersion
from backend.app.core.enums import ModelVersionStatus
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def db_session(tmp_path):
    """Provides a fresh isolated database session for testing."""
    db_file = tmp_path / "test_model_registry.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_register_candidate(db_session: Session):
    """Verifies candidate model registration and audit logging."""
    registry = ModelRegistry(db_session)
    model_name = f"FraudDetector-{uuid.uuid4().hex[:6]}"

    metrics = {"pr_auc": 0.95, "recall": 0.91, "f1": 0.93, "precision": 0.95}
    candidate = registry.register_candidate(
        model_name=model_name,
        version="v1.0.0",
        algorithm="XGBoost",
        artifact_path="/tmp/artifacts/xgboost_v1.joblib",
        dataset_version="v1.0.0",
        metrics=metrics,
        training_run_id="mlflow_run_001",
    )

    # Check model registry dictionary fields
    assert candidate["model_name"] == model_name
    assert candidate["version"] == "v1.0.0"
    assert candidate["algorithm"] == "XGBoost"
    assert candidate["status"] == "CANDIDATE"
    assert candidate["artifact_path"] == "/tmp/artifacts/xgboost_v1.joblib"
    assert candidate["dataset_version"] == "v1.0.0"
    assert candidate["training_run_id"] == "mlflow_run_001"
    assert candidate["metrics"]["pr_auc"] == pytest.approx(0.95)
    assert candidate["created_at"] is not None

    # Check AuditLog creation
    audit_logs = db_session.query(AuditLog).filter(AuditLog.action == "REGISTER_CANDIDATE").all()
    assert len(audit_logs) >= 1
    latest_log = audit_logs[-1]
    assert latest_log.resource_type == "MODEL_VERSION"
    assert latest_log.details["model_name"] == model_name


def test_get_candidate_models(db_session: Session):
    """Verifies candidate models listing."""
    registry = ModelRegistry(db_session)
    model_name = f"FraudDetector-{uuid.uuid4().hex[:6]}"

    registry.register_candidate(model_name=model_name, version="v1.0.0", algorithm="XGBoost")
    registry.register_candidate(model_name=model_name, version="v1.1.0", algorithm="LightGBM")

    candidates = registry.get_candidate_models(model_name=model_name)
    assert len(candidates) == 2
    versions = [c["version"] for c in candidates]
    assert "v1.0.0" in versions
    assert "v1.1.0" in versions


def test_single_active_production_and_promotion(db_session: Session):
    """
    Verifies that promoting a model to PRODUCTION demotes the existing active production version to STAGING.
    Enforces the single active PRODUCTION model rule.
    """
    registry = ModelRegistry(db_session)
    model_name = f"FraudDetector-{uuid.uuid4().hex[:6]}"

    registry.register_candidate(model_name=model_name, version="v1.0.0", algorithm="LogisticRegression")
    registry.register_candidate(model_name=model_name, version="v2.0.0", algorithm="XGBoost")

    # 1. Promote v1.0.0 to PRODUCTION
    prod1 = registry.promote_model(model_name=model_name, version="v1.0.0", target_status=ModelVersionStatus.PRODUCTION)
    assert prod1["status"] == "PRODUCTION"

    # Verify get_production_model returns v1.0.0
    current_prod = registry.get_production_model(model_name)
    assert current_prod is not None
    assert current_prod["version"] == "v1.0.0"

    # 2. Promote v2.0.0 to PRODUCTION
    prod2 = registry.promote_model(model_name=model_name, version="v2.0.0", target_status=ModelVersionStatus.PRODUCTION)
    assert prod2["status"] == "PRODUCTION"

    # Verify get_production_model now returns v2.0.0
    current_prod_updated = registry.get_production_model(model_name)
    assert current_prod_updated["version"] == "v2.0.0"

    # Verify v1.0.0 was demoted to STAGING
    ver1_obj = registry.version_repo.get_by_model_and_version(
        registry.model_repo.get_by_name(model_name).id, "v1.0.0"
    )
    assert ver1_obj.status == ModelVersionStatus.STAGING

    # Verify AuditLogs recorded for promotions and demotions
    promotion_logs = db_session.query(AuditLog).filter(AuditLog.action == "PROMOTE_MODEL").all()
    demotion_logs = db_session.query(AuditLog).filter(AuditLog.action == "DEMOTE_PRODUCTION_MODEL").all()

    assert len(promotion_logs) >= 2
    assert len(demotion_logs) >= 1
    assert demotion_logs[-1].details["version"] == "v1.0.0"


def test_rollback_model(db_session: Session):
    """Verifies production rollback capability to a prior version."""
    registry = ModelRegistry(db_session)
    model_name = f"FraudDetector-{uuid.uuid4().hex[:6]}"

    registry.register_candidate(model_name=model_name, version="v1.0.0", algorithm="RandomForest")
    registry.register_candidate(model_name=model_name, version="v2.0.0", algorithm="XGBoost")

    # Promote v1 then v2
    registry.promote_model(model_name=model_name, version="v1.0.0", target_status=ModelVersionStatus.PRODUCTION)
    registry.promote_model(model_name=model_name, version="v2.0.0", target_status=ModelVersionStatus.PRODUCTION)

    assert registry.get_production_model(model_name)["version"] == "v2.0.0"

    # Rollback to v1.0.0
    rolled_back = registry.rollback_model(model_name=model_name, target_version="v1.0.0")
    assert rolled_back["version"] == "v1.0.0"
    assert rolled_back["status"] == "PRODUCTION"

    assert registry.get_production_model(model_name)["version"] == "v1.0.0"

    # Verify AuditLog recorded for rollback
    rollback_logs = db_session.query(AuditLog).filter(AuditLog.action == "ROLLBACK_MODEL").all()
    assert len(rollback_logs) >= 1
    assert rollback_logs[-1].details["promoted_version"] == "v1.0.0"
    assert rollback_logs[-1].details["demoted_version"] == "v2.0.0"


def test_archive_model(db_session: Session):
    """Verifies archiving a model version."""
    registry = ModelRegistry(db_session)
    model_name = f"FraudDetector-{uuid.uuid4().hex[:6]}"

    registry.register_candidate(model_name=model_name, version="v1.0.0", algorithm="LightGBM")
    archived = registry.archive_model(model_name=model_name, version="v1.0.0")

    assert archived["status"] == "ARCHIVED"

    # Verify AuditLog recorded for archiving
    archive_logs = db_session.query(AuditLog).filter(AuditLog.action == "ARCHIVE_MODEL").all()
    assert len(archive_logs) >= 1
    assert archive_logs[-1].details["version"] == "v1.0.0"
