"""
FastAPI Router for Application-Level Canary & Shadow Deployment Management and Progressive Promotion.

Exposes:
- GET /api/v1/canary/config
- POST /api/v1/canary/config
- GET /api/v1/canary/metrics
- GET /api/v1/canary/notifications
- POST /api/v1/canary/promote
- POST /api/v1/canary/progressive-promotion/start
- POST /api/v1/canary/progressive-promotion/advance
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from ml.evaluation.canary import CanaryConfigManager, ALLOWED_CANARY_PERCENTAGES
from ml.evaluation.quality_gate import ModelQualityGate
from ml.evaluation.progressive_promotion import (
    ProgressivePromotionManager,
    ProgressivePromotionState,
    PromotionThresholds,
)
from ml.registry.model_registry import ModelRegistry

router = APIRouter(prefix="/canary", tags=["Canary & Shadow Deployment"])


class UpdateCanaryConfigRequest(BaseModel):
    enabled: Optional[bool] = Field(default=None, description="Toggle active canary/shadow evaluation")
    mode: Optional[str] = Field(default=None, description="Deployment mode: 'CANARY' or 'SHADOW'")
    canary_percentage: Optional[int] = Field(default=None, description="Percentage of traffic routed to candidate model (0, 5, 10, 25, 50, 100)")
    candidate_version_id: Optional[str] = Field(default=None, description="Target candidate model version ID")
    production_version_id: Optional[str] = Field(default=None, description="Target production model version ID")


class PromoteCanaryRequest(BaseModel):
    model_name: Optional[str] = Field(default="FraudDetector", description="Model name to promote")
    candidate_version: Optional[str] = Field(default=None, description="Candidate version string to promote to production")
    candidate_version_id: Optional[str] = Field(default=None, description="Candidate version ID to promote to production")
    force: Optional[bool] = Field(default=False, description="Force promotion bypassing quality gate checks")


class StartProgressivePromotionRequest(BaseModel):
    model_name: str = Field(default="FraudDetector", description="Model name to promote")
    candidate_version: str = Field(..., description="Candidate version string")
    incident_id: Optional[str] = Field(default=None, description="Associated operational incident ID")


class AdvanceProgressivePromotionRequest(BaseModel):
    state: ProgressivePromotionState = Field(..., description="Current progressive promotion state payload")
    candidate_live_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Optional live evaluation metrics")


@router.get(
    "/config",
    status_code=status.HTTP_200_OK,
    summary="Get Canary & Shadow Configuration",
    description="Retrieves current application-level canary routing mode, candidate version ID, and traffic split percentage.",
)
def get_canary_config():
    """Returns active canary deployment configuration."""
    manager = CanaryConfigManager()
    return manager.get_config()


@router.post(
    "/config",
    status_code=status.HTTP_200_OK,
    summary="Update Canary & Shadow Configuration",
    description="Configures inside-FastAPI traffic splitting percentages (0, 5, 10, 25, 50, 100), deployment mode ('CANARY' or 'SHADOW'), and candidate version ID.",
)
def update_canary_config(request: UpdateCanaryConfigRequest):
    """Updates canary deployment configuration."""
    manager = CanaryConfigManager()
    try:
        updated_config = manager.update_config(
            enabled=request.enabled,
            mode=request.mode,
            canary_percentage=request.canary_percentage,
            candidate_version_id=request.candidate_version_id,
            production_version_id=request.production_version_id,
        )
        return updated_config
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Get Comparative Canary & Shadow Metrics",
    description="Returns real-time comparative performance metrics, latency p95, and prediction agreement rate for Production vs Candidate.",
)
def get_canary_metrics():
    """Returns comparative metrics for Production vs Candidate models."""
    manager = CanaryConfigManager()
    return manager.metrics.get_summary()


@router.get(
    "/notifications",
    status_code=status.HTTP_200_OK,
    summary="Get Frontend Canary & Rollback Notifications",
    description="Retrieves active notification stream for frontend UI (e.g. rollback alerts, stage advancements).",
)
def get_canary_notifications():
    """Returns frontend notifications."""
    manager = CanaryConfigManager()
    return manager.get_notifications()


@router.post(
    "/promote",
    status_code=status.HTTP_200_OK,
    summary="Promote Candidate Model to Production",
    description="Evaluates quality gate and promotes candidate model to 100% Production status in the Model Registry.",
)
def promote_canary_candidate(
    request: PromoteCanaryRequest,
    db: Session = Depends(get_db),
):
    """Promotes candidate model version to PRODUCTION after quality gate check."""
    manager = CanaryConfigManager()
    config = manager.get_config()

    cand_ver_id = request.candidate_version_id or config.candidate_version_id
    if not cand_ver_id and not request.candidate_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidate version specified for promotion.",
        )

    registry = ModelRegistry(db)
    model_name = request.model_name or "FraudDetector"

    # Evaluate Quality Gate if not forced
    if not request.force:
        cand_dict = None
        if request.candidate_version:
            cand_dict = registry.get_model_version(model_name, request.candidate_version)
        elif cand_ver_id:
            mver_obj = registry.version_repo.get(cand_ver_id)
            if mver_obj:
                cand_dict = mver_obj.to_registry_dict()

        if not cand_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate model version not found in registry.",
            )

        prod_dict = registry.get_production_model(model_name)
        cand_metrics = cand_dict.get("metrics", {})
        prod_metrics = prod_dict.get("metrics", {}) if prod_dict else None

        gate = ModelQualityGate()
        gate_res = gate.evaluate(
            candidate_metrics=cand_metrics,
            production_metrics=prod_metrics,
            artifact_path=cand_dict.get("artifact_path"),
        )

        if not gate_res.passed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "MODEL PROMOTION REJECTED",
                    "rejection_reasons": gate_res.rejection_reasons,
                    "evaluations": gate_res.evaluations,
                },
            )

    version_str = request.candidate_version
    if not version_str and cand_ver_id:
        mver_obj = registry.version_repo.get(cand_ver_id)
        if mver_obj:
            version_str = mver_obj.version

    if not version_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not resolve version string for candidate.")

    promoted_ver = registry.promote_model(model_name=model_name, version=version_str, target_status="PRODUCTION")

    manager.update_config(
        enabled=False,
        mode="SHADOW",
        canary_percentage=0,
        candidate_version_id=None,
        production_version_id=promoted_ver.get("id"),
    )

    return {
        "status": "CANDIDATE APPROVED & PROMOTED TO PRODUCTION",
        "model_name": model_name,
        "promoted_version": version_str,
        "details": promoted_ver,
    }


@router.post(
    "/progressive-promotion/start",
    status_code=status.HTTP_200_OK,
    summary="Start Progressive Promotion Pipeline",
    description="Starts progressive promotion workflow (Quality Gate -> Shadow -> Canary 10% -> 25% -> 50% -> 100%).",
)
def start_progressive_promotion(
    request: StartProgressivePromotionRequest,
    db: Session = Depends(get_db),
):
    """Initiates progressive promotion starting with Step 1: Offline Quality Gate."""
    promo_mgr = ProgressivePromotionManager(db)
    try:
        state = promo_mgr.start_promotion_pipeline(
            model_name=request.model_name,
            candidate_version=request.candidate_version,
            incident_id=request.incident_id,
        )
        return state
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/progressive-promotion/advance",
    status_code=status.HTTP_200_OK,
    summary="Advance Progressive Promotion Stage or Rollback",
    description="Evaluates stage metrics and advances stage (Shadow -> Canary 10% -> 25% -> 50% -> 100%) or triggers immediate ROLLBACK.",
)
def advance_progressive_promotion(
    request: AdvanceProgressivePromotionRequest,
    db: Session = Depends(get_db),
):
    """Advances progressive promotion state or executes immediate rollback on degradation."""
    promo_mgr = ProgressivePromotionManager(db)
    try:
        updated_state = promo_mgr.advance_stage(
            state=request.state,
            candidate_live_metrics=request.candidate_live_metrics,
        )
        return updated_state
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


from backend.app.models.job import AsyncJob
from backend.app.workers.evaluation_worker import evaluate_candidate_task


class EvaluateCandidateAsyncRequest(BaseModel):
    candidate_version_id: str = Field(..., description="Candidate model version ID to evaluate")
    production_version_id: Optional[str] = Field(default=None, description="Current production model version ID")
    force_promote: Optional[bool] = Field(default=False, description="Force promotion bypassing quality gate")


@router.post(
    "/evaluate/async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue Asynchronous Candidate Model Evaluation & Canary Promotion",
    description="Queues candidate quality gate evaluation and canary traffic deployment into background Celery worker.",
)
def evaluate_candidate_async(
    request: EvaluateCandidateAsyncRequest,
    db: Session = Depends(get_db),
):
    """Queues candidate evaluation into background Celery worker."""
    task = evaluate_candidate_task.delay(
        candidate_version_id=request.candidate_version_id,
        production_version_id=request.production_version_id,
        force_promote=request.force_promote,
    )

    job_rec = AsyncJob(
        job_id=task.id,
        task_type="candidate_evaluation",
        status="QUEUED",
        progress=0.0,
        payload={
            "candidate_version_id": request.candidate_version_id,
            "production_version_id": request.production_version_id,
            "force_promote": request.force_promote,
        },
    )
    db.add(job_rec)
    db.commit()

    return {
        "job_id": task.id,
        "candidate_version_id": request.candidate_version_id,
        "status": "QUEUED",
        "message": "Candidate model evaluation task queued successfully in background Celery worker.",
    }

