"""
FastAPI Router for SentinelML Automated Retraining Pipeline (Prefect Orchestrated).

Exposes:
- POST /api/v1/retraining/trigger
- GET /api/v1/retraining/{run_id}
"""
import uuid
import threading
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from pipelines.retraining_flow import (
    automated_retraining_flow,
    get_run_state,
    acquire_retraining_lock,
    update_run_state,
)

router = APIRouter(prefix="/retraining", tags=["Automated Retraining"])


class TriggerRetrainingRequest(BaseModel):
    incident_id: Optional[str] = Field(default=None, description="ID of active incident to trigger retraining for")
    model_version_id: Optional[str] = Field(default=None, description="Target model version ID")
    model_type: Optional[str] = Field(default="xgboost", description="ML model architecture type (e.g., xgboost, lightgbm, random_forest)")
    async_execution: Optional[bool] = Field(default=True, description="Whether to run pipeline asynchronously in background")


from backend.app.models.job import AsyncJob
from backend.app.workers.retraining_worker import retrain_model_task

class TriggerRetrainingResponse(BaseModel):
    run_id: str
    job_id: str
    incident_id: Optional[str] = None
    status: str
    current_step: str
    message: str


@router.post(
    "/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TriggerRetrainingResponse,
    summary="Trigger Automated Retraining Flow",
    description="Initiates Celery-queued, self-healing automated retraining flow for an incident or target model version.",
)
def trigger_retraining(
    request: TriggerRetrainingRequest,
    db: Session = Depends(get_db),
):
    """Triggers the self-healing automated retraining pipeline via Celery async worker."""
    run_id = str(uuid.uuid4())
    inc_id = request.incident_id

    # Check lock to prevent simultaneous retraining runs for the same incident
    if inc_id:
        locked = acquire_retraining_lock(inc_id, run_id)
        if not locked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Retraining job for incident '{inc_id}' is already in progress.",
            )

    update_run_state(
        run_id=run_id,
        current_step="Initializing Flow",
        status="QUEUED",
        incident_id=inc_id,
    )

    # Queue Celery task
    task = retrain_model_task.delay(
        run_id=run_id,
        incident_id=inc_id,
        model_version_id=request.model_version_id,
        model_type=request.model_type or "xgboost",
        job_id=run_id,
    )

    # Record in AsyncJob DB table
    job_rec = AsyncJob(
        job_id=task.id,
        task_type="model_retraining",
        status="QUEUED",
        progress=0.0,
        payload={
            "run_id": run_id,
            "incident_id": inc_id,
            "model_version_id": request.model_version_id,
            "model_type": request.model_type or "xgboost",
        },
    )
    db.add(job_rec)
    db.commit()

    return TriggerRetrainingResponse(
        run_id=run_id,
        job_id=task.id,
        incident_id=inc_id,
        status="QUEUED",
        current_step="Queued in Background Worker",
        message="Automated retraining pipeline queued successfully in Celery worker queue.",
    )



@router.get(
    "/{run_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Retraining Run Status",
    description="Retrieves real-time execution status, current step, metrics, and logs for a retraining flow run.",
)
def get_retraining_status(run_id: str):
    """Returns state of an automated retraining run by run_id."""
    state = get_run_state(run_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retraining run '{run_id}' not found.",
        )
    return state
