"""
Unit tests for SentinelML Optuna Hyperparameter Optimization Module.
"""
import os
import json
import pytest
import numpy as np
import optuna
from pathlib import Path

from ml.training.tuning.search_spaces import get_search_space, SEARCH_SPACES
from ml.training.tuning.tuner import OptunaTuner


@pytest.fixture
def synthetic_dataset():
    """Generates synthetic dataset split for train, val, and test."""
    np.random.seed(42)
    n_train, n_val, n_test = 200, 50, 50
    n_features = 10

    X_train = np.random.randn(n_train, n_features)
    y_train = np.random.choice([0, 1], size=n_train, p=[0.9, 0.1])

    X_val = np.random.randn(n_val, n_features)
    y_val = np.random.choice([0, 1], size=n_val, p=[0.9, 0.1])

    X_test = np.random.randn(n_test, n_features)
    y_test = np.random.choice([0, 1], size=n_test, p=[0.9, 0.1])

    return X_train, y_train, X_val, y_val, X_test, y_test


def test_get_search_spaces():
    """Verifies search space functions for all supported models."""
    for model_name in ["xgboost", "lightgbm", "random_forest", "logistic_regression"]:
        fn = get_search_space(model_name)
        assert callable(fn)

        study = optuna.create_study()
        trial = study.ask()
        params = fn(trial)

        assert isinstance(params, dict)
        assert len(params) > 0

    with pytest.raises(ValueError, match="Unsupported model type"):
        get_search_space("invalid_model_type")


def test_logistic_regression_minimal_space():
    """Ensures Logistic Regression search space is minimal as a baseline."""
    fn = get_search_space("logistic_regression")
    study = optuna.create_study()
    trial = study.ask()
    params = fn(trial)

    # Minimal set of params: C, max_iter, random_state
    assert "C" in params
    assert len(params) <= 4


def test_optuna_tuner_optimization(synthetic_dataset, tmp_path):
    """Verifies end-to-end Optuna study execution on XGBoost."""
    X_train, y_train, X_val, y_val, X_test, y_test = synthetic_dataset
    out_dir = tmp_path / "tuning_artifacts"

    tuner = OptunaTuner(
        model_type="xgboost",
        n_trials=3,
        seed=42,
        output_dir=str(out_dir),
    )

    summary = tuner.optimize(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        y_test=y_test,
        save_results=True,
    )

    assert summary["model_type"] == "xgboost"
    assert summary["objective_metric"] == "pr_auc"
    assert summary["n_trials_requested"] == 3
    assert len(summary["trial_history"]) == 3
    assert summary["optimization_duration_sec"] > 0
    assert "best_params" in summary
    assert "best_score_val" in summary
    assert 0.0 <= summary["best_score_val"] <= 1.0

    # Verify held-out test evaluation
    test_eval = summary["test_evaluation"]
    assert test_eval is not None
    assert "pr_auc" in test_eval
    assert "recall" in test_eval
    assert "f1" in test_eval

    # Verify output JSON saved properly
    result_file = out_dir / "optuna_results_xgboost.json"
    assert result_file.exists()

    with open(result_file, "r") as f:
        saved_data = json.load(f)
    assert saved_data["model_type"] == "xgboost"
    assert len(saved_data["trial_history"]) == 3


def test_optuna_tuner_models(synthetic_dataset, tmp_path):
    """Verifies optimization runs across LightGBM, Random Forest, and Logistic Regression."""
    X_train, y_train, X_val, y_val, X_test, y_test = synthetic_dataset

    for model_name in ["lightgbm", "random_forest", "logistic_regression"]:
        tuner = OptunaTuner(
            model_type=model_name,
            n_trials=2,
            seed=42,
            output_dir=str(tmp_path),
        )

        summary = tuner.optimize(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            save_results=True,
        )

        assert summary["model_type"] == model_name
        assert len(summary["trial_history"]) == 2
        assert (tmp_path / f"optuna_results_{model_name}.json").exists()
