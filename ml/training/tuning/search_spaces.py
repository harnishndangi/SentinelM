"""
Hyperparameter Search Space Definitions for Optuna Optimization in SentinelML.
Supports XGBoost, LightGBM, Random Forest, and a minimal baseline space for Logistic Regression.
"""
from typing import Dict, Any, Callable
import optuna


def sample_xgboost_params(trial: optuna.Trial) -> Dict[str, Any]:
    """Search space for XGBoost classifier."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=25),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "gamma": trial.suggest_float("gamma", 1e-8, 1.0, log=True),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 50.0, log=True),
        "eval_metric": "logloss",
        "random_state": 42,
        "n_jobs": -1,
    }


def sample_lightgbm_params(trial: optuna.Trial) -> Dict[str, Any]:
    """Search space for LightGBM classifier."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=25),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
        "scale_pos_weight": trial.suggest_float("scale_pos_weight", 1.0, 50.0, log=True),
        "verbose": -1,
        "random_state": 42,
        "n_jobs": -1,
    }


def sample_random_forest_params(trial: optuna.Trial) -> Dict[str, Any]:
    """Search space for Random Forest classifier."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 50, 300, step=25),
        "max_depth": trial.suggest_int("max_depth", 5, 30),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
        "class_weight": trial.suggest_categorical("class_weight", ["balanced", "balanced_subsample", None]),
        "random_state": 42,
        "n_jobs": -1,
    }


def sample_logistic_regression_params(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Minimal baseline search space for Logistic Regression.
    Kept concise as Logistic Regression serves primarily as a baseline model.
    """
    return {
        "C": trial.suggest_float("C", 0.01, 10.0, log=True),
        "max_iter": 1000,
        "random_state": 42,
    }


SEARCH_SPACES: Dict[str, Callable[[optuna.Trial], Dict[str, Any]]] = {
    "xgboost": sample_xgboost_params,
    "xgb": sample_xgboost_params,
    "lightgbm": sample_lightgbm_params,
    "lgb": sample_lightgbm_params,
    "lgbm": sample_lightgbm_params,
    "random_forest": sample_random_forest_params,
    "rf": sample_random_forest_params,
    "logistic_regression": sample_logistic_regression_params,
    "logistic": sample_logistic_regression_params,
    "lr": sample_logistic_regression_params,
}


def get_search_space(model_type: str) -> Callable[[optuna.Trial], Dict[str, Any]]:
    """Returns the parameter sampler function for a given model type."""
    key = model_type.lower().strip()
    if key not in SEARCH_SPACES:
        raise ValueError(
            f"Unsupported model type '{model_type}'. Available search spaces: {list(SEARCH_SPACES.keys())}"
        )
    return SEARCH_SPACES[key]
