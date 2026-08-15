"""
Application-Level Canary & Shadow Model Evaluator.

Provides inside-FastAPI traffic splitting, shadow prediction evaluation,
and comparative metric collection WITHOUT requiring Kubernetes, Docker,
or external infrastructure load balancers.
"""
import random
import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

logger = logging.getLogger("sentinelml.canary")

ALLOWED_CANARY_PERCENTAGES = [0, 5, 10, 25, 50, 100]


class CanaryConfig(BaseModel):
    """Configuration payload for application-level Canary & Shadow deployment."""
    enabled: bool = Field(default=False, description="Whether canary/shadow deployment is active")
    mode: str = Field(default="SHADOW", description="Deployment mode: 'CANARY' or 'SHADOW'")
    canary_percentage: int = Field(default=10, description="Percentage of traffic routed to candidate model (0, 5, 10, 25, 50, 100)")
    production_version_id: Optional[str] = Field(default=None, description="Active production model version ID")
    candidate_version_id: Optional[str] = Field(default=None, description="Active candidate model version ID")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RouterDecision(BaseModel):
    """Decision output from CanaryRouter for request routing."""
    target: str  # "PRODUCTION" or "CANDIDATE"
    is_shadow: bool
    mode: str
    production_version_id: Optional[str]
    candidate_version_id: Optional[str]


class CanaryMetrics:
    """
    In-memory metrics collector tracking comparative metrics for Production vs Candidate.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self.production_count: int = 0
            self.candidate_count: int = 0
            self.production_latencies: List[float] = []
            self.candidate_latencies: List[float] = []
            self.production_probs: List[float] = []
            self.candidate_probs: List[float] = []

            # Shadow metrics
            self.total_shadow_evaluations: int = 0
            self.agreement_count: int = 0
            self.disagreement_count: int = 0
            self.prob_diffs: List[float] = []

    def record_production(self, latency_ms: float, fraud_prob: float):
        with self._lock:
            self.production_count += 1
            self.production_latencies.append(latency_ms)
            self.production_probs.append(fraud_prob)
            if len(self.production_latencies) > 2000:
                self.production_latencies = self.production_latencies[-1000:]
                self.production_probs = self.production_probs[-1000:]

    def record_candidate(self, latency_ms: float, fraud_prob: float):
        with self._lock:
            self.candidate_count += 1
            self.candidate_latencies.append(latency_ms)
            self.candidate_probs.append(fraud_prob)
            if len(self.candidate_latencies) > 2000:
                self.candidate_latencies = self.candidate_latencies[-1000:]
                self.candidate_probs = self.candidate_probs[-1000:]

    def record_shadow_evaluation(
        self,
        prod_pred: int,
        cand_pred: int,
        prod_prob: float,
        cand_prob: float,
        cand_latency_ms: float,
    ):
        with self._lock:
            self.total_shadow_evaluations += 1
            if prod_pred == cand_pred:
                self.agreement_count += 1
            else:
                self.disagreement_count += 1

            self.prob_diffs.append(abs(prod_prob - cand_prob))
            self.candidate_count += 1
            self.candidate_latencies.append(cand_latency_ms)
            self.candidate_probs.append(cand_prob)

            if len(self.prob_diffs) > 2000:
                self.prob_diffs = self.prob_diffs[-1000:]
                self.candidate_latencies = self.candidate_latencies[-1000:]
                self.candidate_probs = self.candidate_probs[-1000:]

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            prod_p95 = float(np.percentile(self.production_latencies, 95)) if self.production_latencies else 0.0
            cand_p95 = float(np.percentile(self.candidate_latencies, 95)) if self.candidate_latencies else 0.0

            prod_mean_prob = float(np.mean(self.production_probs)) if self.production_probs else 0.0
            cand_mean_prob = float(np.mean(self.candidate_probs)) if self.candidate_probs else 0.0

            agreement_rate = (
                float(round(self.agreement_count / max(self.total_shadow_evaluations, 1), 4))
                if self.total_shadow_evaluations > 0
                else 1.0
            )

            disagreement_rate = (
                float(round(self.disagreement_count / max(self.total_shadow_evaluations, 1), 4))
                if self.total_shadow_evaluations > 0
                else 0.0
            )

            mean_prob_diff = float(np.mean(self.prob_diffs)) if self.prob_diffs else 0.0

            return {
                "production": {
                    "request_count": self.production_count,
                    "latency_p95_ms": round(prod_p95, 2),
                    "mean_fraud_prob": round(prod_mean_prob, 4),
                },
                "candidate": {
                    "request_count": self.candidate_count,
                    "latency_p95_ms": round(cand_p95, 2),
                    "mean_fraud_prob": round(cand_mean_prob, 4),
                },
                "shadow_evaluation": {
                    "total_evaluations": self.total_shadow_evaluations,
                    "agreement_count": self.agreement_count,
                    "disagreement_count": self.disagreement_count,
                    "agreement_rate": agreement_rate,
                    "disagreement_rate": disagreement_rate,
                    "mean_prob_difference": round(mean_prob_diff, 4),
                },
            }


class CanaryConfigManager:
    """Thread-safe singleton managing active CanaryConfig, CanaryMetrics, and Frontend Notifications."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CanaryConfigManager, cls).__new__(cls)
            cls._instance.config = CanaryConfig()
            cls._instance.metrics = CanaryMetrics()
            cls._instance.notifications = []
            cls._instance.lock = threading.Lock()
        return cls._instance

    def add_notification(self, notification: Dict[str, Any]):
        with self.lock:
            self.notifications.append(notification)
            if len(self.notifications) > 100:
                self.notifications = self.notifications[-100:]

    def get_notifications(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.notifications)

    def update_config(
        self,
        enabled: Optional[bool] = None,
        mode: Optional[str] = None,
        canary_percentage: Optional[int] = None,
        candidate_version_id: Optional[str] = None,
        production_version_id: Optional[str] = None,
    ) -> CanaryConfig:
        with self.lock:
            if enabled is not None:
                self.config.enabled = enabled
            if mode is not None:
                mode_upper = mode.upper()
                if mode_upper not in ["CANARY", "SHADOW"]:
                    raise ValueError(f"Invalid mode '{mode}'. Must be 'CANARY' or 'SHADOW'.")
                self.config.mode = mode_upper
            if canary_percentage is not None:
                if canary_percentage not in ALLOWED_CANARY_PERCENTAGES and not (0 <= canary_percentage <= 100):
                    raise ValueError(f"Invalid canary_percentage {canary_percentage}. Must be integer between 0 and 100.")
                self.config.canary_percentage = canary_percentage
            if candidate_version_id is not None:
                self.config.candidate_version_id = candidate_version_id
            if production_version_id is not None:
                self.config.production_version_id = production_version_id

            self.config.updated_at = datetime.now(timezone.utc).isoformat()
            return self.config.model_copy()

    def get_config(self) -> CanaryConfig:
        with self.lock:
            return self.config.model_copy()


class CanaryRouter:
    """
    Application-level traffic splitting router inside FastAPI.
    """

    def __init__(self, manager: Optional[CanaryConfigManager] = None):
        self.manager = manager or CanaryConfigManager()

    def route_request(self) -> RouterDecision:
        """
        Determines whether to route current request to Production or Candidate,
        or perform Shadow evaluation.
        """
        config = self.manager.get_config()

        if not config.enabled or not config.candidate_version_id:
            return RouterDecision(
                target="PRODUCTION",
                is_shadow=False,
                mode="PRODUCTION",
                production_version_id=config.production_version_id,
                candidate_version_id=config.candidate_version_id,
            )

        if config.mode == "SHADOW":
            # In SHADOW mode, user request ALWAYS goes to PRODUCTION model directly.
            # Candidate receives asynchronous shadow copy in background.
            return RouterDecision(
                target="PRODUCTION",
                is_shadow=True,
                mode="SHADOW",
                production_version_id=config.production_version_id,
                candidate_version_id=config.candidate_version_id,
            )

        # Mode == "CANARY"
        percentage = config.canary_percentage
        roll = random.randint(1, 100)

        if roll <= percentage:
            return RouterDecision(
                target="CANDIDATE",
                is_shadow=False,
                mode="CANARY",
                production_version_id=config.production_version_id,
                candidate_version_id=config.candidate_version_id,
            )
        else:
            return RouterDecision(
                target="PRODUCTION",
                is_shadow=False,
                mode="CANARY",
                production_version_id=config.production_version_id,
                candidate_version_id=config.candidate_version_id,
            )


class ShadowEvaluator:
    """
    Executes candidate prediction in background thread for shadow evaluation
    without adding latency to user requests or modifying user responses.
    """

    def __init__(self, db_session_factory=None, metrics: Optional[CanaryMetrics] = None):
        self.db_session_factory = db_session_factory
        self.metrics = metrics or CanaryConfigManager().metrics

    def evaluate_shadow_async(
        self,
        features: Dict[str, Any],
        prod_prediction: int,
        prod_probability: float,
        candidate_version_id: str,
    ):
        """Spawns an asynchronous background thread for shadow evaluation."""
        thread = threading.Thread(
            target=self._run_shadow_prediction,
            args=(features, prod_prediction, prod_probability, candidate_version_id),
            daemon=True,
        )
        thread.start()

    def _run_shadow_prediction(
        self,
        features: Dict[str, Any],
        prod_prediction: int,
        prod_probability: float,
        candidate_version_id: str,
    ):
        """Runs candidate inference asynchronously and logs shadow evaluation metrics."""
        start_time = time.perf_counter()
        try:
            from backend.app.database import SessionLocal
            from backend.app.models.model import ModelVersion
            import joblib

            db = SessionLocal()
            try:
                mver = db.query(ModelVersion).filter(ModelVersion.id == candidate_version_id).first()
                if not mver or not mver.artifact_path or not os.path.exists(mver.artifact_path):
                    logger.warning(f"Shadow evaluation skipped: Candidate '{candidate_version_id}' artifact unavailable.")
                    return

                model_obj = joblib.load(mver.artifact_path)
                df = pd.DataFrame([features])

                # Handle preprocessor if present
                prep_file = os.path.join(os.path.dirname(mver.artifact_path), "preprocessor.joblib")
                if os.path.exists(prep_file):
                    prep_obj = joblib.load(prep_file)
                    if hasattr(prep_obj, "transform"):
                        X_proc = prep_obj.transform(df)
                    else:
                        X_proc = df.values
                else:
                    # Filter numerical columns
                    num_df = df.select_dtypes(include=[np.number])
                    X_proc = num_df.values if len(num_df.columns) > 0 else df.values

                if hasattr(model_obj, "predict_proba"):
                    probs = model_obj.predict_proba(X_proc)[:, 1]
                elif hasattr(model_obj, "decision_function"):
                    scores = model_obj.decision_function(X_proc)
                    probs = 1 / (1 + np.exp(-scores))
                else:
                    preds = model_obj.predict(X_proc)
                    probs = preds.astype(float)

                cand_prob = float(round(probs[0], 4))
                cand_pred = int(cand_prob >= 0.5)

                cand_latency_ms = float(round((time.perf_counter() - start_time) * 1000, 2))

                self.metrics.record_shadow_evaluation(
                    prod_pred=prod_prediction,
                    cand_pred=cand_pred,
                    prod_prob=prod_probability,
                    cand_prob=cand_prob,
                    cand_latency_ms=cand_latency_ms,
                )

                logger.debug(
                    "Shadow evaluation complete",
                    prod_pred=prod_prediction,
                    cand_pred=cand_pred,
                    latency_ms=cand_latency_ms,
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Shadow evaluation execution failed: {e}")
