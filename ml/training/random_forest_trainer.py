from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from ml.training.base_trainer import BaseTrainer


class RandomForestTrainer(BaseTrainer):
    """
    Random Forest Trainer with balanced class weights for fraud detection.
    """

    def __init__(self, hyperparams: Optional[Dict[str, Any]] = None):
        default_params = {
            "n_estimators": 100,
            "max_depth": 12,
            "class_weight": "balanced",
            "random_state": 42,
            "n_jobs": -1,
        }
        if hyperparams:
            default_params.update(hyperparams)
        super().__init__(model_name="RandomForest", hyperparams=default_params)

    def _build_model(self):
        self.model = RandomForestClassifier(**self.hyperparams)
