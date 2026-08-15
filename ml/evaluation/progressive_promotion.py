"""
Progressive Model Promotion & Automatic Rollback Engine.

Workflow Sequence:
Candidate passes offline quality gate -> Shadow evaluation -> Canary 10% -> Evaluate ->
Canary 25% -> Evaluate -> Canary 50% -> Evaluate -> Promote to 100% PRODUCTION.

Immediate Rollback Trigger:
If metrics deteriorate beyond configured thresholds during any stage, rollback is executed immediately:
1. Deactivate candidate
2. Restore previous production model
3. Update ModelRegistry
4. Update Deployment status (ROLLED_BACK for candidate, ACTIVE for production)
5. Create AuditLog entry
6. Add IncidentEvent
7. Notify frontend via notification store / REST payload
8. NEVER delete previous production model artifact file on disk.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.models.model import ModelVersion
from backend.app.models.deployment import Deployment
from backend.app.models.audit import AuditLog
from backend.app.models.incident import Incident, IncidentEvent
from backend.app.core.enums import ModelVersionStatus, DeploymentStatus, IncidentEventType
from ml.registry.model_registry import ModelRegistry
from ml.evaluation.quality_gate import ModelQualityGate, QualityGateConfig, QualityGateResult
from ml.evaluation.canary import CanaryConfigManager, CanaryMetrics, RouterDecision

logger = logging.getLogger("sentinelml.progressive_promotion")

PROMOTION_STAGES = [
    "OFFLINE_QUALITY_GATE",
    "SHADOW",
    "CANARY_10",
    "CANARY_25",
    "CANARY_50",
    "PROMOTED_100",
]


class PromotionThresholds(BaseModel):
    """Configurable metrics degradation thresholds for canary/shadow evaluation."""
    max_disagreement_rate: float = Field(default=0.25, description="Max allowed disagreement rate in shadow mode (25%)")
    max_latency_p95_ms: float = Field(default=50.0, description="Max allowed 95th percentile latency in ms")
    max_error_rate: float = Field(default=0.05, description="Max allowed error rate (5%)")
    max_fraud_prob_diff: float = Field(default=0.20, description="Max allowed mean fraud probability divergence")


class ProgressivePromotionState(BaseModel):
    """Current state of progressive promotion pipeline."""
    model_name: str
    candidate_version_id: str
    candidate_version: str
    production_version_id: Optional[str] = None
    production_version: Optional[str] = None
    incident_id: Optional[str] = None
    current_stage: str = "OFFLINE_QUALITY_GATE"
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, ROLLED_BACK, REJECTED
    rollback_reason: Optional[str] = None
    stage_evaluations: Dict[str, Any] = {}
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProgressivePromotionManager:
    """
    Manages progressive promotion stages (Shadow -> Canary 10% -> 25% -> 50% -> 100%)
    and executes immediate rollback on metric degradation.
    """

    def __init__(
        self,
        db: Session,
        thresholds: Optional[PromotionThresholds] = None,
        quality_gate_config: Optional[QualityGateConfig] = None,
    ):
        self.db = db
        self.registry = ModelRegistry(db)
        self.thresholds = thresholds or PromotionThresholds()
        self.gate = ModelQualityGate(quality_gate_config)
        self.canary_manager = CanaryConfigManager()

    def start_promotion_pipeline(
        self,
        model_name: str,
        candidate_version: str,
        incident_id: Optional[str] = None,
    ) -> ProgressivePromotionState:
        """
        Initiates progressive promotion workflow starting with Step 1: Offline Quality Gate.
        """
        cand_dict = self.registry.get_model_version(model_name, candidate_version)
        if not cand_dict:
            raise ValueError(f"Candidate version '{candidate_version}' for model '{model_name}' not found.")

        cand_ver_id = cand_dict.get("id") or cand_dict.get("version_id") or cand_dict["model_id"]

        prod_dict = self.registry.get_production_model(model_name)
        prod_ver_id = (prod_dict.get("id") or prod_dict.get("version_id") or prod_dict.get("model_id")) if prod_dict else None
        prod_version_str = prod_dict["version"] if prod_dict else None

        state = ProgressivePromotionState(
            model_name=model_name,
            candidate_version_id=cand_ver_id,
            candidate_version=candidate_version,
            production_version_id=prod_ver_id,
            production_version=prod_version_str,
            incident_id=incident_id,
            current_stage="OFFLINE_QUALITY_GATE",
            status="IN_PROGRESS",
        )

        # Stage 1: Offline Quality Gate
        gate_res = self.gate.evaluate(
            candidate_metrics=cand_dict.get("metrics", {}),
            production_metrics=prod_dict.get("metrics", {}) if prod_dict else None,
            artifact_path=cand_dict.get("artifact_path"),
        )

        state.stage_evaluations["OFFLINE_QUALITY_GATE"] = gate_res.model_dump()

        if not gate_res.passed:
            state.status = "REJECTED"
            state.rollback_reason = f"Offline Quality Gate failed: {'; '.join(gate_res.rejection_reasons)}"
            logger.warning(f"Progressive promotion rejected at OFFLINE_QUALITY_GATE: {state.rollback_reason}")
            return state

        # Quality Gate Passed -> Transition to Stage 2: SHADOW
        state.current_stage = "SHADOW"
        self.canary_manager.update_config(
            enabled=True,
            mode="SHADOW",
            canary_percentage=0,
            candidate_version_id=cand_ver_id,
            production_version_id=prod_ver_id,
        )

        logger.info(f"Progressive promotion passed Quality Gate. Transitioned to SHADOW mode for candidate '{candidate_version}'.")
        return state

    def advance_stage(
        self,
        state: ProgressivePromotionState,
        candidate_live_metrics: Optional[Dict[str, Any]] = None,
    ) -> ProgressivePromotionState:
        """
        Evaluates current stage metrics and advances to next stage if healthy,
        or triggers immediate ROLLBACK if metrics deteriorate.
        """
        if state.status in ["COMPLETED", "ROLLED_BACK", "REJECTED"]:
            return state

        current_stage = state.current_stage
        canary_summary = self.canary_manager.metrics.get_summary()

        # Check for metric degradation in current stage
        degradation_reason = self._check_metric_degradation(current_stage, canary_summary, candidate_live_metrics)

        if degradation_reason:
            logger.error(f"Metric degradation detected at stage '{current_stage}': {degradation_reason}. Initiating ROLLBACK.")
            return self.execute_rollback(state=state, reason=degradation_reason)

        state.stage_evaluations[current_stage] = {
            "status": "PASSED",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "canary_summary": canary_summary,
        }

        # Advance to next stage in sequence
        if current_stage == "SHADOW":
            state.current_stage = "CANARY_10"
            self.canary_manager.update_config(enabled=True, mode="CANARY", canary_percentage=10)
            logger.info("Advanced progressive promotion to CANARY_10 stage.")

        elif current_stage == "CANARY_10":
            state.current_stage = "CANARY_25"
            self.canary_manager.update_config(enabled=True, mode="CANARY", canary_percentage=25)
            logger.info("Advanced progressive promotion to CANARY_25 stage.")

        elif current_stage == "CANARY_25":
            state.current_stage = "CANARY_50"
            self.canary_manager.update_config(enabled=True, mode="CANARY", canary_percentage=50)
            logger.info("Advanced progressive promotion to CANARY_50 stage.")

        elif current_stage == "CANARY_50":
            state.current_stage = "PROMOTED_100"
            state.status = "COMPLETED"

            # Promote candidate to 100% PRODUCTION in registry
            promoted_dict = self.registry.promote_model(
                model_name=state.model_name,
                version=state.candidate_version,
                target_status=ModelVersionStatus.PRODUCTION,
            )

            # Deactivate canary mode
            self.canary_manager.update_config(
                enabled=False,
                mode="SHADOW",
                canary_percentage=0,
                candidate_version_id=None,
                production_version_id=state.candidate_version_id,
            )

            logger.info(f"Progressive promotion complete. Candidate '{state.candidate_version}' promoted to 100% PRODUCTION.")

        state.updated_at = datetime.now(timezone.utc).isoformat()
        return state

    def _check_metric_degradation(
        self,
        current_stage: str,
        canary_summary: Dict[str, Any],
        live_metrics: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Evaluates whether candidate metrics deteriorate beyond configured thresholds.
        """
        shadow_info = canary_summary.get("shadow_evaluation", {})
        cand_info = canary_summary.get("candidate", {})

        # 1. Shadow Disagreement Rate check
        disagreement_rate = shadow_info.get("disagreement_rate", 0.0)
        eval_count = shadow_info.get("total_evaluations", 0)

        if current_stage == "SHADOW" and eval_count >= 3 and disagreement_rate > self.thresholds.max_disagreement_rate:
            return f"Shadow disagreement rate ({disagreement_rate:.2%}) exceeded maximum threshold ({self.thresholds.max_disagreement_rate:.2%})."

        # 2. Candidate Latency P95 check
        cand_p95 = cand_info.get("latency_p95_ms", 0.0)
        if cand_p95 > self.thresholds.max_latency_p95_ms:
            return f"Candidate 95th percentile latency ({cand_p95:.2f}ms) exceeded threshold ({self.thresholds.max_latency_p95_ms:.2f}ms)."

        # 3. Live Metrics drop check (if live metrics provided)
        if live_metrics:
            if live_metrics.get("pr_auc", 1.0) < 0.50:
                return "Candidate live PR-AUC dropped below critical threshold (0.50)."
            if live_metrics.get("error_rate", 0.0) > self.thresholds.max_error_rate:
                return f"Candidate live error rate ({live_metrics['error_rate']:.2%}) exceeded threshold ({self.thresholds.max_error_rate:.2%})."

        return None

    def execute_rollback(
        self,
        state: ProgressivePromotionState,
        reason: str,
    ) -> ProgressivePromotionState:
        """
        Executes immediate rollback:
        1. Deactivates candidate (disables canary config)
        2. Restores previous production model in registry
        3. Updates deployment record (ROLLED_BACK for candidate, ACTIVE for production)
        4. Creates AuditLog entry
        5. Adds IncidentEvent (if incident_id present or logs incident event)
        6. Stores notification for frontend UI
        7. NEVER deletes previous production model artifact file on disk.
        """
        logger.error(f"Executing immediate rollback for model '{state.model_name}' candidate '{state.candidate_version}': {reason}")

        # 1. Deactivate candidate (disable canary config)
        self.canary_manager.update_config(
            enabled=False,
            mode="SHADOW",
            canary_percentage=0,
            candidate_version_id=None,
            production_version_id=state.production_version_id,
        )

        # 2 & 3. Restore previous production model & update registry
        restored_ver_str = state.production_version
        if restored_ver_str:
            try:
                self.registry.promote_model(
                    model_name=state.model_name,
                    version=restored_ver_str,
                    target_status=ModelVersionStatus.PRODUCTION,
                )
            except Exception as e:
                logger.error(f"Error restoring previous production model '{restored_ver_str}': {e}")

        # Mark candidate model version status as FAILED in DB
        cand_mver = self.db.query(ModelVersion).filter(ModelVersion.id == state.candidate_version_id).first()
        if cand_mver:
            cand_mver.status = ModelVersionStatus.FAILED
            self.db.add(cand_mver)

        # 4. Update deployment records
        cand_dep = self.db.query(Deployment).filter(Deployment.model_version_id == state.candidate_version_id).first()
        if not cand_dep:
            cand_dep = Deployment(
                model_version_id=state.candidate_version_id,
                environment="canary",
                status=DeploymentStatus.ROLLED_BACK,
                terminated_at=datetime.now(timezone.utc),
            )
        else:
            cand_dep.status = DeploymentStatus.ROLLED_BACK
            cand_dep.terminated_at = datetime.now(timezone.utc)
        self.db.add(cand_dep)

        if state.production_version_id:
            prod_dep = self.db.query(Deployment).filter(Deployment.model_version_id == state.production_version_id).first()
            if not prod_dep:
                prod_dep = Deployment(
                    model_version_id=state.production_version_id,
                    environment="production",
                    status=DeploymentStatus.ACTIVE,
                )
            else:
                prod_dep.status = DeploymentStatus.ACTIVE
                prod_dep.terminated_at = None
            self.db.add(prod_dep)

        # 5. Create AuditLog entry
        audit_entry = AuditLog(
            action="CANARY_ROLLBACK_EXECUTED",
            resource_type="MODEL_VERSION",
            resource_id=state.candidate_version_id,
            details={
                "model_name": state.model_name,
                "candidate_version": state.candidate_version,
                "restored_production_version": restored_ver_str,
                "stage_failed": state.current_stage,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit_entry)

        # 6. Add IncidentEvent
        if state.incident_id:
            inc_evt = IncidentEvent(
                incident_id=state.incident_id,
                event_type="CANARY_ROLLBACK_EXECUTED",
                message=f"Canary evaluation failed at stage {state.current_stage}. Executed immediate rollback to previous production version '{restored_ver_str}'. Reason: {reason}",
                metadata_json={
                    "candidate_version": state.candidate_version,
                    "restored_version": restored_ver_str,
                    "reason": reason,
                },
            )
            self.db.add(inc_evt)

        self.db.commit()

        # 7. Store frontend notification
        notification_payload = {
            "type": "CANARY_ROLLBACK",
            "title": f"Rollback Executed for {state.model_name}",
            "message": f"Candidate {state.candidate_version} rolled back at stage {state.current_stage}. Restored {restored_ver_str}.",
            "details": {"reason": reason, "stage": state.current_stage},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.canary_manager.add_notification(notification_payload)

        # 8. Never delete previous production model artifact check
        if state.production_version_id:
            prod_mver = self.db.query(ModelVersion).filter(ModelVersion.id == state.production_version_id).first()
            if prod_mver and prod_mver.artifact_path:
                if os.path.exists(prod_mver.artifact_path):
                    logger.info(f"Verified production artifact at '{prod_mver.artifact_path}' remains intact on disk.")

        state.status = "ROLLED_BACK"
        state.rollback_reason = reason
        state.updated_at = datetime.now(timezone.utc).isoformat()
        return state
