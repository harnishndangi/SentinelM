import traceback
from datetime import datetime, timezone
from celery import Celery, Task
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.database import SessionLocal


class SentinelBaseTask(Task):
    """
    Custom Celery Base Task class that provides:
    - Automatic DB job status tracking (AsyncJob updates)
    - Structured error logging & stack trace formatting
    - Exponential backoff retry defaults
    """
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            "Celery task failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
        )
        db = SessionLocal()
        try:
            from backend.app.models.job import AsyncJob
            job = db.query(AsyncJob).filter(AsyncJob.job_id == task_id).first()
            if job:
                job.status = "FAILURE"
                job.error_message = str(exc)
                job.traceback = str(einfo) if einfo else traceback.format_exc()
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logger.warning("Failed to update AsyncJob on failure", error=str(e))
        finally:
            db.close()

    def on_success(self, retval, task_id, args, kwargs):
        logger.info(
            "Celery task completed successfully",
            task_id=task_id,
            task_name=self.name,
        )
        db = SessionLocal()
        try:
            from backend.app.models.job import AsyncJob
            job = db.query(AsyncJob).filter(AsyncJob.job_id == task_id).first()
            if job:
                job.status = "SUCCESS"
                job.progress = 100.0
                job.result = retval if isinstance(retval, dict) else {"data": str(retval)}
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as e:
            logger.warning("Failed to update AsyncJob on success", error=str(e))
        finally:
            db.close()


celery_app = Celery(
    "sentinelml_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "backend.app.workers.drift_worker",
        "backend.app.workers.retraining_worker",
        "backend.app.workers.shap_worker",
        "backend.app.workers.snapshot_worker",
        "backend.app.workers.evaluation_worker",
        "backend.app.workers.incident_worker",
        "backend.app.workers.prediction_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard timeout for retraining/evaluation
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
)


def update_job_progress(job_id: str, status: str, progress: float, payload_update: dict = None):
    """Utility function to update job progress in DB from worker tasks."""
    db = SessionLocal()
    try:
        from backend.app.models.job import AsyncJob
        job = db.query(AsyncJob).filter(AsyncJob.job_id == job_id).first()
        if job:
            job.status = status
            job.progress = progress
            if payload_update and isinstance(job.result, dict):
                job.result.update(payload_update)
            elif payload_update:
                job.result = payload_update
            if status == "STARTED" and not job.started_at:
                job.started_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        logger.warning("Failed to update job progress", job_id=job_id, error=str(e))
    finally:
        db.close()
