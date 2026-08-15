from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from backend.app.dependencies import get_db
from backend.app.models.job import AsyncJob
from backend.app.core.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["Background Job Status Tracking"])


class JobStatusResponse(BaseModel):
    job_id: str
    task_type: str
    status: str
    progress: float
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Background Job Execution Status",
    description="Retrieves real-time status, progress, results, or error details for an asynchronous Celery task by job ID.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves current execution status of a background job."""
    job = db.query(AsyncJob).filter(AsyncJob.job_id == job_id).first()

    # Query Celery result backend as secondary fallback / real-time status check
    celery_result = AsyncResult(job_id, app=celery_app)
    celery_status = celery_result.status if celery_result else None

    if not job:
        if celery_status and celery_status != "PENDING":
            return JobStatusResponse(
                job_id=job_id,
                task_type="celery_task",
                status=celery_status,
                progress=100.0 if celery_status == "SUCCESS" else 0.0,
                result=celery_result.result if isinstance(celery_result.result, dict) else {"data": str(celery_result.result)},
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Background job '{job_id}' not found.",
        )

    # Sync status from Celery if DB status is PENDING/STARTED and Celery finished
    effective_status = job.status
    if celery_status in ["SUCCESS", "FAILURE", "REVOKED"] and job.status not in ["SUCCESS", "FAILURE"]:
        effective_status = celery_status

    return JobStatusResponse(
        job_id=job.job_id,
        task_type=job.task_type,
        status=effective_status,
        progress=job.progress,
        payload=job.payload,
        result=job.result,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get(
    "",
    response_model=List[JobStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="List Recent Background Jobs",
    description="Retrieves operational history of asynchronous background tasks.",
)
def list_jobs(
    limit: int = 20,
    task_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists recent background jobs."""
    query = db.query(AsyncJob)
    if task_type:
        query = query.filter(AsyncJob.task_type == task_type)
    if status_filter:
        query = query.filter(AsyncJob.status == status_filter)

    jobs = query.order_by(AsyncJob.created_at.desc()).limit(limit).all()

    return [
        JobStatusResponse(
            job_id=j.job_id,
            task_type=j.task_type,
            status=j.status,
            progress=j.progress,
            payload=j.payload,
            result=j.result,
            error_message=j.error_message,
            created_at=j.created_at.isoformat() if j.created_at else None,
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
        )
        for j in jobs
    ]
