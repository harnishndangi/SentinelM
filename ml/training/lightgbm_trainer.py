from typing import Dict, Any, Optional
import numpy as np
from lightgbm import LGBMClassifier
from ml.training.base_trainer import BaseTrainer


class LightGBMTrainer(BaseTrainer):
    """
    LightGBM Gradient Boosting Trainer (Strong Challenger Model).
    Optimized for high speed and imbalanced classification using scale_pos_weight.
    """

    def __init__(self, hyperparams: Optional[Dict[str, Any]] = None, scale_pos_weight: Optional[float] = None):
        default_params = {
            "n_estimators": 150,
            "num_leaves": 31,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42,
            "verbose": -1,
            "n_jobs": -1,
        }
        if scale_pos_weight is not None:
            default_params["scale_pos_weight"] = scale_pos_weight
        if hyperparams:
            default_params.update(hyperparams)
        super().__init__(model_name="LightGBM", hyperparams=default_params)

    def fit(self, X_train: np.ndarray, y_train: np.ndarray) -> "LightGBMTrainer":
        # Calculate scale_pos_weight if not explicitly provided
        if "scale_pos_weight" not in self.hyperparams:
            num_pos = np.sum(y_train == 1)
            num_neg = np.sum(y_train == 0)
            if num_pos > 0:
                self.hyperparams["scale_pos_weight"] = float(round(num_neg / num_pos, 2))
        return super().fit(X_train, y_train)

    def _build_model(self):
        self.model = LGBMClassifier(**self.hyperparams)
