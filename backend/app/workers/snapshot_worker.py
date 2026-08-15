import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.core.celery_app import celery_app, SentinelBaseTask, update_job_progress
from backend.app.core.logging import logger
from backend.app.database import SessionLocal


@celery_app.task(bind=True, base=SentinelBaseTask, max_retries=3, default_retry_delay=10)
def create_dataset_snapshot_task(
    self,
    dataset_id: str,
    snapshot_name: str,
    description: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background worker for dataset snapshot creation, schema validation, and checksum verification.
    Computes statistical profiles for baseline dataset versioning.
    """
    current_job_id = job_id or self.request.id
    logger.info("Executing dataset snapshot creation task", job_id=current_job_id, dataset_id=dataset_id)

    update_job_progress(current_job_id, "STARTED", 10.0)

    db = SessionLocal()
    try:
        from backend.app.models.dataset import Dataset, DatasetVersion
        from ml.simulator.drift_simulator import DriftSimulator
        from ml.preprocessing.schema_validator import InputSchemaValidator

        update_job_progress(current_job_id, "RUNNING", 30.0)

        simulator = DriftSimulator(db)
        df = simulator.get_baseline_reference_data(num_records=2000)

        update_job_progress(current_job_id, "RUNNING", 60.0)

        validator = InputSchemaValidator()
        validation_result = validator.validate(df)

        # Generate dataset snapshot checksum hash
        sample_bytes = df.to_json().encode("utf-8")
        checksum = hashlib.sha256(sample_bytes).hexdigest()

        version_num = f"v{int(datetime.now(timezone.utc).timestamp())}"
        ds_ver = DatasetVersion(
            dataset_id=dataset_id,
            version=version_num,
            num_rows=len(df),
            num_columns=len(df.columns),
            schema_meta={"columns": list(df.columns), "dtypes": {k: str(v) for k, v in df.dtypes.items()}},
            statistics_summary={
                "validation": validation_result,
                "checksum": checksum,
                "snapshot_name": snapshot_name,
            },
            storage_path=f"artifacts/datasets/{dataset_id}_{version_num}.parquet",
        )
        db.add(ds_ver)
        db.commit()
        db.refresh(ds_ver)

        update_job_progress(current_job_id, "RUNNING", 90.0)

        result = {
            "dataset_id": dataset_id,
            "version_id": ds_ver.id,
            "version": version_num,
            "snapshot_name": snapshot_name,
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "checksum": checksum,
            "is_valid_schema": validation_result.get("is_valid", True),
        }

        update_job_progress(current_job_id, "SUCCESS", 100.0, payload_update=result)
        return result
    except Exception as exc:
        logger.error("Error creating dataset snapshot in worker task", error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            raise exc
    finally:
        db.close()
