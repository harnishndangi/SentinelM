from abc import ABC, abstractmethod
import time
from typing import Dict, Any, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)


class BaseTrainer(ABC):
    """
    Abstract Base Class for all ML Model Trainers in SentinelML.
    Enforces standardized model building, fitting, latency evaluation, and PR-AUC metric computation.
    """

    def __init__(self, model_name: str, hyperparams: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        self.hyperparams = hyperparams or {}
        self.model = None
        self.training_time_sec: float = 0.0
        self.is_fitted: bool = False

    @abstractmethod
    def _build_model(self):
        """Constructs underlying estimator instance."""
        pass

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "BaseTrainer":
        """Fits model on training data and records training execution duration."""
        if self.model is None:
            self._build_model()

        start_time = time.perf_counter()
        self.model.fit(X_train, y_train)
        self.training_time_sec = float(round(time.perf_counter() - start_time, 4))
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError(f"Trainer {self.model_name} is not fitted yet.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError(f"Trainer {self.model_name} is not fitted yet.")
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X)
            # If 2D probability matrix, return positive class probabilities
            return probs[:, 1] if probs.ndim == 2 and probs.shape[1] == 2 else probs
        elif hasattr(self.model, "decision_function"):
            return self.model.decision_function(X)
        else:
            return self.model.predict(X).astype(float)

    def evaluate(self, X_eval: np.ndarray, y_eval: np.ndarray) -> Dict[str, Any]:
        """
        Evaluates model predictions and probabilities on evaluation dataset.
        Computes PR-AUC (primary metric), Recall, F1, Precision, ROC-AUC, Accuracy,
        Confusion Matrix, and Average Prediction Latency (ms/sample).
        """
        if not self.is_fitted:
            raise ValueError(f"Trainer {self.model_name} is not fitted yet.")

        # Latency measurement
        start_lat = time.perf_counter()
        y_pred = self.predict(X_eval)
        total_lat_sec = time.perf_counter() - start_lat
        sample_count = len(X_eval)
        latency_ms_per_sample = float(round((total_lat_sec * 1000.0) / max(sample_count, 1), 6))

        y_probs = self.predict_proba(X_eval)

        # Calculate metrics
        acc = float(round(accuracy_score(y_eval, y_pred), 4))
        prec = float(round(precision_score(y_eval, y_pred, zero_division=0), 4))
        rec = float(round(recall_score(y_eval, y_pred, zero_division=0), 4))
        f1 = float(round(f1_score(y_eval, y_pred, zero_division=0), 4))
        
        try:
            roc_auc = float(round(roc_auc_score(y_eval, y_probs), 4))
        except Exception:
            roc_auc = 0.0

        try:
            # PR-AUC is Average Precision Score
            pr_auc = float(round(average_precision_score(y_eval, y_probs), 4))
        except Exception:
            pr_auc = 0.0

        # Confusion Matrix
        cm = confusion_matrix(y_eval, y_pred, labels=[0, 1])
        tn, fp, fn, tp = [int(val) for val in cm.ravel()]

        return {
            "model_name": self.model_name,
            "pr_auc": pr_auc,  # Primary metric
            "recall": rec,
            "f1": f1,
            "precision": prec,
            "roc_auc": roc_auc,
            "accuracy": acc,
            "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
            "training_time_sec": self.training_time_sec,
            "prediction_latency_ms": latency_ms_per_sample,
            "hyperparams": self.hyperparams,
        }

    def save_artifact(self, output_path: str) -> None:
        """Saves fitted model to joblib file."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted model artifact.")
        joblib.dump(self.model, output_path)

    def load_artifact(self, input_path: str) -> None:
        """Loads fitted model from joblib file."""
        self.model = joblib.load(input_path)
        self.is_fitted = True
