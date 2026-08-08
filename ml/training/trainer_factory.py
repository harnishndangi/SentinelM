from typing import Dict, Any, Optional, Type, List
from ml.training.base_trainer import BaseTrainer
from ml.training.logistic_trainer import LogisticRegressionTrainer
from ml.training.random_forest_trainer import RandomForestTrainer
from ml.training.xgboost_trainer import XGBoostTrainer
from ml.training.lightgbm_trainer import LightGBMTrainer


class TrainerFactory:
    """
    Factory pattern for instantiating model trainers.
    """

    _TRAINERS: Dict[str, Type[BaseTrainer]] = {
        "logistic_regression": LogisticRegressionTrainer,
        "logistic": LogisticRegressionTrainer,
        "lr": LogisticRegressionTrainer,
        "random_forest": RandomForestTrainer,
        "rf": RandomForestTrainer,
        "xgboost": XGBoostTrainer,
        "xgb": XGBoostTrainer,
        "lightgbm": LightGBMTrainer,
        "lgb": LightGBMTrainer,
        "lgbm": LightGBMTrainer,
    }

    @classmethod
    def get_trainer(cls, model_type: str, hyperparams: Optional[Dict[str, Any]] = None) -> BaseTrainer:
        key = model_type.lower().strip()
        if key not in cls._TRAINERS:
            supported = list(set(cls._TRAINERS.keys()))
            raise ValueError(f"Unknown model_type '{model_type}'. Supported trainers: {supported}")
        return cls._TRAINERS[key](hyperparams=hyperparams)

    @classmethod
    def list_supported_models(cls) -> List[str]:
        return ["logistic_regression", "random_forest", "xgboost", "lightgbm"]
