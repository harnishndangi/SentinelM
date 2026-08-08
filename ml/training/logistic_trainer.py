from typing import Dict, Any, Optional
from sklearn.linear_model import LogisticRegression
from ml.training.base_trainer import BaseTrainer


class LogisticRegressionTrainer(BaseTrainer):
    """
    Baseline Trainer using Logistic Regression with balanced class weights.
    """

    def __init__(self, hyperparams: Optional[Dict[str, Any]] = None):
        default_params = {
            "class_weight": "balanced",
            "max_iter": 1000,
            "random_state": 42,
            "C": 1.0,
            "solver": "lbfgs",
        }
        if hyperparams:
            default_params.update(hyperparams)
        super().__init__(model_name="LogisticRegression", hyperparams=default_params)

    def _build_model(self):
        self.model = LogisticRegression(**self.hyperparams)
