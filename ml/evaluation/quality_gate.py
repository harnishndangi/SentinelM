"""
SentinelML Model Quality Gate Engine.

Enforces strict candidate-vs-production model evaluation prior to production promotion.
Prevents sub-standard or degraded candidates from being promoted automatically.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import joblib
from pydantic import BaseModel, Field

logger = logging.getLogger("sentinelml.quality_gate")


class QualityGateConfig(BaseModel):
    """Configurable quality gate thresholds and metric tolerances."""
    pr_auc_tolerance: float = Field(default=0.0, description="Max allowable drop in PR-AUC compared to production (0.0 means candidate must be >= production)")
    recall_tolerance: float = Field(default=0.02, description="Max allowable drop in Recall compared to production")
    f1_tolerance: float = Field(default=0.02, description="Max allowable drop in F1 compared to production")
    precision_tolerance: float = Field(default=0.02, description="Max allowable drop in Precision compared to production")
    max_latency_p95_ms: float = Field(default=50.0, description="Maximum allowed 95th percentile inference latency in ms")
    min_absolute_pr_auc: float = Field(default=0.50, description="Minimum absolute PR-AUC required even if no production model exists")
    min_absolute_recall: float = Field(default=0.50, description="Minimum absolute Recall required even if no production model exists")
    require_data_validation: bool = Field(default=True, description="Enforce data validation pass")
    require_schema_validation: bool = Field(default=True, description="Enforce schema validation pass")
    require_valid_artifact: bool = Field(default=True, description="Enforce model artifact existence and integrity check")


class QualityGateResult(BaseModel):
    """Result payload from ModelQualityGate evaluation."""
    status: str  # "CANDIDATE APPROVED" or "MODEL PROMOTION REJECTED"
    passed: bool
    rejection_reasons: List[str]
    candidate_metrics: Dict[str, Any]
    production_metrics: Dict[str, Any]
    evaluations: Dict[str, Dict[str, Any]]


class ModelQualityGate:
    """
    Evaluates candidate model metrics against production baseline metrics and quality thresholds.
    """

    def __init__(self, config: Optional[QualityGateConfig] = None):
        self.config = config or QualityGateConfig()

    def validate_artifact(self, artifact_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validates model artifact file existence, non-emptiness, and deserialization.
        """
        if not artifact_path:
            return False, "Model artifact path is missing or empty."

        if not os.path.exists(artifact_path):
            return False, f"Model artifact file '{artifact_path}' does not exist on disk."

        try:
            if os.path.getsize(artifact_path) == 0:
                return False, f"Model artifact file '{artifact_path}' is empty (0 bytes)."

            model_obj = joblib.load(artifact_path)
            if model_obj is None:
                return False, f"Deserialized model artifact from '{artifact_path}' is None."

            if not (hasattr(model_obj, "predict") or hasattr(model_obj, "predict_proba")):
                return False, f"Loaded model object from '{artifact_path}' does not implement predict or predict_proba."

            return True, None
        except Exception as e:
            return False, f"Failed to deserialize model artifact from '{artifact_path}': {str(e)}"

    def evaluate(
        self,
        candidate_metrics: Dict[str, Any],
        production_metrics: Optional[Dict[str, Any]] = None,
        data_validation_passed: bool = True,
        schema_validation_passed: bool = True,
        artifact_path: Optional[str] = None,
    ) -> QualityGateResult:
        """
        Runs candidate vs production evaluation against quality rules and thresholds.
        """
        rejection_reasons: List[str] = []
        evaluations: Dict[str, Dict[str, Any]] = {}
        prod_metrics = production_metrics or {}

        # 1. Data & Schema Validation Checks
        if self.config.require_data_validation:
            evaluations["data_validation"] = {
                "passed": data_validation_passed,
                "detail": "Data validation passed" if data_validation_passed else "Data validation failed",
            }
            if not data_validation_passed:
                rejection_reasons.append("Data validation failed prior to candidate evaluation.")

        if self.config.require_schema_validation:
            evaluations["schema_validation"] = {
                "passed": schema_validation_passed,
                "detail": "Schema validation passed" if schema_validation_passed else "Major schema validation problems detected",
            }
            if not schema_validation_passed:
                rejection_reasons.append("Major schema problems detected in candidate dataset.")

        # 2. Artifact Integrity Check
        if self.config.require_valid_artifact and artifact_path:
            artifact_ok, err_msg = self.validate_artifact(artifact_path)
            evaluations["artifact_validation"] = {
                "passed": artifact_ok,
                "detail": err_msg or f"Artifact at '{artifact_path}' is valid",
            }
            if not artifact_ok:
                rejection_reasons.append(f"Model artifact validation failed: {err_msg}")

        # 3. Candidate vs Production Metric Comparisons
        cand_pr_auc = float(candidate_metrics.get("pr_auc", 0.0))
        prod_pr_auc = float(prod_metrics.get("pr_auc", 0.0))

        cand_recall = float(candidate_metrics.get("recall", 0.0))
        prod_recall = float(prod_metrics.get("recall", 0.0))

        cand_f1 = float(candidate_metrics.get("f1", 0.0))
        prod_f1 = float(prod_metrics.get("f1", 0.0))

        cand_precision = float(candidate_metrics.get("precision", 0.0))
        prod_precision = float(prod_metrics.get("precision", 0.0))

        cand_latency = float(candidate_metrics.get("prediction_latency_ms", candidate_metrics.get("latency_p95_ms", 0.0)))

        # 3a. PR-AUC Check
        if production_metrics and "pr_auc" in prod_metrics:
            target_pr_auc = prod_pr_auc - self.config.pr_auc_tolerance
            pr_auc_passed = cand_pr_auc >= target_pr_auc
            evaluations["pr_auc"] = {
                "candidate": cand_pr_auc,
                "production": prod_pr_auc,
                "threshold": target_pr_auc,
                "passed": pr_auc_passed,
            }
            if not pr_auc_passed:
                rejection_reasons.append(
                    f"Candidate PR-AUC ({cand_pr_auc:.4f}) is below production threshold ({target_pr_auc:.4f}, production: {prod_pr_auc:.4f})."
                )
        else:
            pr_auc_passed = cand_pr_auc >= self.config.min_absolute_pr_auc
            evaluations["pr_auc"] = {
                "candidate": cand_pr_auc,
                "production": None,
                "threshold": self.config.min_absolute_pr_auc,
                "passed": pr_auc_passed,
            }
            if not pr_auc_passed:
                rejection_reasons.append(
                    f"Candidate PR-AUC ({cand_pr_auc:.4f}) is below absolute threshold ({self.config.min_absolute_pr_auc:.4f})."
                )

        # 3b. Recall Check
        if production_metrics and "recall" in prod_metrics:
            target_recall = prod_recall - self.config.recall_tolerance
            recall_passed = cand_recall >= target_recall
            evaluations["recall"] = {
                "candidate": cand_recall,
                "production": prod_recall,
                "threshold": target_recall,
                "passed": recall_passed,
            }
            if not recall_passed:
                rejection_reasons.append(
                    f"Candidate Recall ({cand_recall:.4f}) dropped below allowable tolerance threshold ({target_recall:.4f}, production: {prod_recall:.4f})."
                )
        else:
            recall_passed = cand_recall >= self.config.min_absolute_recall
            evaluations["recall"] = {
                "candidate": cand_recall,
                "production": None,
                "threshold": self.config.min_absolute_recall,
                "passed": recall_passed,
            }
            if not recall_passed:
                rejection_reasons.append(
                    f"Candidate Recall ({cand_recall:.4f}) is below absolute threshold ({self.config.min_absolute_recall:.4f})."
                )

        # 3c. F1 Check
        if production_metrics and "f1" in prod_metrics:
            target_f1 = prod_f1 - self.config.f1_tolerance
            f1_passed = cand_f1 >= target_f1
            evaluations["f1"] = {
                "candidate": cand_f1,
                "production": prod_f1,
                "threshold": target_f1,
                "passed": f1_passed,
            }
            if not f1_passed:
                rejection_reasons.append(
                    f"Candidate F1 ({cand_f1:.4f}) dropped below allowable threshold ({target_f1:.4f}, production: {prod_f1:.4f})."
                )

        # 3d. Precision Check
        if production_metrics and "precision" in prod_metrics:
            target_prec = prod_precision - self.config.precision_tolerance
            prec_passed = cand_precision >= target_prec
            evaluations["precision"] = {
                "candidate": cand_precision,
                "production": prod_precision,
                "threshold": target_prec,
                "passed": prec_passed,
            }
            if not prec_passed:
                rejection_reasons.append(
                    f"Candidate Precision ({cand_precision:.4f}) dropped below allowable threshold ({target_prec:.4f}, production: {prod_precision:.4f})."
                )

        # 3e. Inference Latency Check
        if cand_latency > 0:
            latency_passed = cand_latency <= self.config.max_latency_p95_ms
            evaluations["inference_latency"] = {
                "candidate_ms": cand_latency,
                "max_threshold_ms": self.config.max_latency_p95_ms,
                "passed": latency_passed,
            }
            if not latency_passed:
                rejection_reasons.append(
                    f"Candidate inference latency ({cand_latency:.2f}ms) exceeds max threshold ({self.config.max_latency_p95_ms:.2f}ms)."
                )

        passed = len(rejection_reasons) == 0
        status_str = "CANDIDATE APPROVED" if passed else "MODEL PROMOTION REJECTED"

        logger.info(
            f"Quality Gate Evaluation Complete: {status_str}",
            passed=passed,
            rejection_count=len(rejection_reasons),
        )

        return QualityGateResult(
            status=status_str,
            passed=passed,
            rejection_reasons=rejection_reasons,
            candidate_metrics=candidate_metrics,
            production_metrics=prod_metrics,
            evaluations=evaluations,
        )
