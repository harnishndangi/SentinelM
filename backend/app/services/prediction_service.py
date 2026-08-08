"""
Production Fraud Prediction Service with Dynamic Model Registry Integration,
Model Artifact In-Memory Caching, Structured Logging, and DB Persistence.
"""
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import joblib
import structlog
from sqlalchemy.orm import Session

from backend.app.models.model import ModelVersion
from backend.app.models.prediction import Prediction, FeatureLog
from backend.app.schemas.predict_schemas import (
    PredictionRequest,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
)
from ml.registry.model_registry import ModelRegistry
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor

logger = structlog.get_logger(__name__)


class ModelCache:
    """
    In-memory singleton cache manager for ML models and preprocessors.
    Prevents reading model binaries from disk on every prediction request.
    """
    _instance: Optional["ModelCache"] = None
    _cache: Dict[str, Tuple[Any, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelCache, cls).__new__(cls)
            cls._cache = {}
        return cls._instance

    @classmethod
    def get(cls, key: str) -> Optional[Tuple[Any, Any]]:
        return cls._cache.get(key)

    @classmethod
    def set(cls, key: str, model: Any, preprocessor: Any):
        cls._cache[key] = (model, preprocessor)

    @classmethod
    def clear(cls):
        cls._cache.clear()


class PredictionService:
    """
    Production Fraud Prediction Engine.
    
    Dynamically resolves active PRODUCTION model from ModelRegistry,
    leverages ModelCache for high-throughput low-latency inference,
    logs telemetry, and persists prediction metadata to DB for monitoring.
    """

    def __init__(self, db: Session):
        self.db = db
        self.registry = ModelRegistry(db)
        self.cache = ModelCache()

    def _resolve_production_model(self) -> Tuple[ModelVersion, Any, Any]:
        """
        Dynamically resolves the active PRODUCTION model from ModelRegistry.
        If no production model is registered yet, checks fallback artifact paths and registers it.
        Uses ModelCache to avoid repeated disk reads.
        """
        # 1. Query registry for active production model
        prod_dict = self.registry.get_production_model("SentinelML-FraudDetection")
        if not prod_dict:
            prod_dict = self.registry.get_production_model("FraudDetector")

        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        fallback_model_file = root_dir / "artifacts" / "models" / "fraud_detector" / "v1" / "model.joblib"
        fallback_prep_file = root_dir / "artifacts" / "models" / "fraud_detector" / "v1" / "preprocessor.joblib"

        if not prod_dict:
            # Fallback auto-registration if artifact exists
            if fallback_model_file.exists():
                logger.info("No active production model found in DB. Auto-registering default fallback model.")
                self.registry.register_candidate(
                    model_name="FraudDetector",
                    version="v1.0.0",
                    algorithm="LogisticRegression",
                    artifact_path=str(fallback_model_file),
                )
                self.registry.promote_model("FraudDetector", "v1.0.0", target_status="PRODUCTION")
                prod_dict = self.registry.get_production_model("FraudDetector")

        if not prod_dict:
            raise RuntimeError("No active PRODUCTION model found in registry and no default artifact available.")

        version_id = prod_dict["model_id"]
        version_str = prod_dict["version"]
        artifact_path_str = prod_dict.get("artifact_path") or str(fallback_model_file)
        cache_key = f"{prod_dict['model_name']}:{version_str}:{artifact_path_str}"

        # 2. Check in-memory ModelCache
        cached = self.cache.get(cache_key)
        if cached:
            model_obj, prep_obj = cached
        else:
            logger.info("Loading model artifact into memory cache", cache_key=cache_key)
            if not os.path.exists(artifact_path_str) and fallback_model_file.exists():
                artifact_path_str = str(fallback_model_file)

            if not os.path.exists(artifact_path_str):
                raise FileNotFoundError(f"Model artifact path '{artifact_path_str}' does not exist.")

            model_obj = joblib.load(artifact_path_str)

            # Resolve preprocessor path
            prep_file = Path(artifact_path_str).parent / "preprocessor.joblib"
            if not prep_file.exists():
                prep_file = root_dir / "artifacts" / "preprocessor_v1.joblib"

            if prep_file.exists():
                try:
                    prep_obj = FeaturePreprocessor.load(str(prep_file))
                except Exception:
                    prep_obj = joblib.load(str(prep_file))
            else:
                prep_obj = None

            self.cache.set(cache_key, model_obj, prep_obj)

        # Get SQLAlchemy ModelVersion object for DB relation
        model_ver_obj = self.registry.version_repo.get_by_model_and_version(
            self.registry._get_or_create_model(prod_dict["model_name"]).id, version_str
        )

        return model_ver_obj, model_obj, prep_obj

    def _preprocess_and_predict(
        self, features_df: pd.DataFrame, model_obj: Any, prep_obj: Any
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocesses DataFrame and generates predictions and fraud probabilities."""
        df_proc = features_df.copy()

        # Handle alias mappings if present
        alias_map = {"amount": "transaction_amount"}
        for k, v in alias_map.items():
            if k in df_proc.columns and v not in df_proc.columns:
                df_proc[v] = df_proc[k]

        if prep_obj is not None:
            num_cols = getattr(prep_obj, "numerical_features", [])
            cat_cols = getattr(prep_obj, "categorical_features", [])

            for col in num_cols:
                if col not in df_proc.columns:
                    df_proc[col] = 0.0
            for col in cat_cols:
                if col not in df_proc.columns:
                    df_proc[col] = "unknown"

            if hasattr(prep_obj, "transform"):
                X_transformed = prep_obj.transform(df_proc)
            else:
                X_transformed = df_proc.values
        else:
            X_transformed = df_proc.values

        # Generate probabilities
        if hasattr(model_obj, "predict_proba"):
            probs = model_obj.predict_proba(X_transformed)[:, 1]
        elif hasattr(model_obj, "decision_function"):
            scores = model_obj.decision_function(X_transformed)
            probs = 1 / (1 + np.exp(-scores))
        else:
            preds = model_obj.predict(X_transformed)
            probs = preds.astype(float)

        preds = (probs >= 0.5).astype(int)
        return preds, probs

    def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        """Processes a single fraud prediction request."""
        start_time = time.perf_counter()
        model_ver_obj, model_obj, prep_obj = self._resolve_production_model()

        model_name = model_ver_obj.model.name if model_ver_obj.model else "FraudDetector"
        model_version_str = model_ver_obj.version

        features = request.features
        features_df = pd.DataFrame([features])

        preds, probs = self._preprocess_and_predict(features_df, model_obj, prep_obj)
        pred_label = int(preds[0])
        fraud_prob = float(round(probs[0], 4))

        latency_ms = float(round((time.perf_counter() - start_time) * 1000, 2))
        prediction_id = f"pred_{uuid.uuid4().hex[:12]}"

        # Emits structured telemetry log
        logger.info(
            "prediction_executed",
            prediction_id=prediction_id,
            model=model_name,
            model_version=model_version_str,
            prediction=pred_label,
            fraud_probability=fraud_prob,
            latency_ms=latency_ms,
        )

        # Store metadata in DB for monitoring
        pred_record = Prediction(
            model_version_id=model_ver_obj.id,
            prediction_id=prediction_id,
            input_features=features,
            output_prediction={"prediction": pred_label, "fraud_probability": fraud_prob},
            confidence_score=fraud_prob,
            latency_ms=latency_ms,
        )
        self.db.add(pred_record)

        # Store numerical features in FeatureLog for drift calculation
        for k, v in features.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                f_log = FeatureLog(
                    prediction=pred_record,
                    feature_name=k,
                    feature_value=float(v),
                )
                self.db.add(f_log)

        self.db.commit()

        return PredictionResponse(
            prediction=pred_label,
            fraud_probability=fraud_prob,
            model=model_name,
            model_version=model_version_str,
            prediction_id=prediction_id,
            latency_ms=latency_ms,
        )

    def predict_batch(self, request: BatchPredictionRequest) -> BatchPredictionResponse:
        """Processes a batch of fraud prediction requests."""
        batch_start = time.perf_counter()
        model_ver_obj, model_obj, prep_obj = self._resolve_production_model()

        model_name = model_ver_obj.model.name if model_ver_obj.model else "FraudDetector"
        model_version_str = model_ver_obj.version

        tx_list = request.transactions
        features_list = [tx.features for tx in tx_list]
        features_df = pd.DataFrame(features_list)

        preds, probs = self._preprocess_and_predict(features_df, model_obj, prep_obj)

        responses: List[PredictionResponse] = []
        for i, tx in enumerate(tx_list):
            single_start = time.perf_counter()
            pred_label = int(preds[i])
            fraud_prob = float(round(probs[i], 4))
            latency_ms = float(round((time.perf_counter() - single_start) * 1000, 2))
            prediction_id = f"pred_{uuid.uuid4().hex[:12]}"

            pred_record = Prediction(
                model_version_id=model_ver_obj.id,
                prediction_id=prediction_id,
                input_features=tx.features,
                output_prediction={"prediction": pred_label, "fraud_probability": fraud_prob},
                confidence_score=fraud_prob,
                latency_ms=latency_ms,
            )
            self.db.add(pred_record)

            responses.append(
                PredictionResponse(
                    prediction=pred_label,
                    fraud_probability=fraud_prob,
                    model=model_name,
                    model_version=model_version_str,
                    prediction_id=prediction_id,
                    latency_ms=latency_ms,
                )
            )

        self.db.commit()
        total_batch_latency_ms = float(round((time.perf_counter() - batch_start) * 1000, 2))

        logger.info(
            "batch_prediction_executed",
            total_count=len(responses),
            model=model_name,
            model_version=model_version_str,
            batch_latency_ms=total_batch_latency_ms,
        )

        return BatchPredictionResponse(
            predictions=responses,
            total_transactions=len(responses),
            batch_latency_ms=total_batch_latency_ms,
        )
