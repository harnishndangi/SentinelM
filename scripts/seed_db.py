"""
Development Seed Script for SentinelML Database.
Populates initial sample models, versions, and metrics.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import SessionLocal, engine, Base
from backend.app.services.model_service import ModelService
from backend.app.core.enums import ModelVersionStatus
from backend.app.core.logging import setup_logging, logger


def seed():
    setup_logging()
    logger.info("Initializing database tables for seed execution...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        service = ModelService(db)

        # 1. Create FraudDetector model
        logger.info("Creating FraudDetector ML Model...")
        model = service.create_model(
            name="FraudDetector",
            description="Real-time financial transaction anomaly and fraud detection model.",
            framework="scikit-learn",
            task_type="classification",
        )

        # 2. Create version 1 with PRODUCTION status
        logger.info("Creating ModelVersion 1 in PRODUCTION status...")
        version = service.create_model_version(
            model_id=model.id,
            version="1",
            status=ModelVersionStatus.PRODUCTION,
            artifact_uri="s3://sentinelml-artifacts/models/FraudDetector/v1/model.joblib",
            parameters={
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42,
            },
        )

        # 3. Add sample metrics
        logger.info("Adding sample evaluation metrics...")
        sample_metrics = {
            "precision": 0.92,
            "recall": 0.93,
            "f1": 0.91,
            "roc_auc": 0.97,
            "pr_auc": 0.94,
        }

        for metric_name, value in sample_metrics.items():
            service.add_metric(
                model_version_id=version.id,
                metric_name=metric_name,
                metric_value=value,
                split="test",
            )

        logger.info("Database seeding completed successfully!", model=model.name, version=version.version)

    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed()
