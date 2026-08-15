from typing import List, Dict, Any, Optional
from backend.app.core.celery_app import celery_app, SentinelBaseTask, update_job_progress
from backend.app.core.logging import logger
from backend.app.database import SessionLocal


@celery_app.task(bind=True, base=SentinelBaseTask, max_retries=3, default_retry_delay=10)
def batch_prediction_task(
    self,
    records: List[Dict[str, Any]],
    model_version_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background worker for high-throughput batch predictions.
    Offloads large vector/matrix inference from HTTP request-response cycles.
    """
    current_job_id = job_id or self.request.id
    logger.info("Executing batch prediction task", job_id=current_job_id, num_records=len(records))

    update_job_progress(current_job_id, "STARTED", 10.0)

    db = SessionLocal()
    try:
        from backend.app.schemas.predict_schemas import BatchPredictionRequest, TransactionFeatures
        from backend.app.services.prediction_service import PredictionService

        update_job_progress(current_job_id, "RUNNING", 30.0)

        # Convert dictionary records into TransactionFeatures objects
        features_list = [TransactionFeatures(**rec) for rec in records]
        req = BatchPredictionRequest(
            transactions=features_list,
            model_version_id=model_version_id,
        )

        update_job_progress(current_job_id, "RUNNING", 60.0)

        service = PredictionService(db)
        batch_response = service.predict_batch(req)

        update_job_progress(current_job_id, "RUNNING", 90.0)

        results_data = batch_response.model_dump()
        summary = {
            "num_predictions": len(records),
            "model_version_id": batch_response.model_version_id,
            "predictions_sample": results_data.get("predictions", [])[:5],
            "execution_time_ms": results_data.get("execution_time_ms", 0.0),
        }

        update_job_progress(current_job_id, "SUCCESS", 100.0, payload_update=summary)
        return summary
    except Exception as exc:
        logger.error("Error executing batch prediction worker task", error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            raise exc
    finally:
        db.close()
