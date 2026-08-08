"""
Unit tests for SentinelML MLflow Experiment Tracking Service.
"""
import os
import json
import pytest
import numpy as np
import pandas as pd
import mlflow

from ml.tracking.mlflow_service import MLflowService
from ml.training.xgboost_trainer import XGBoostTrainer
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor


@pytest.fixture
def tmp_mlflow_uri(tmp_path):
    """Sets up isolated MLflow tracking URI for testing."""
    db_path = tmp_path / "mlflow_test.db"
    uri = f"sqlite:///{db_path}"
    return uri


def test_git_commit_retrieval():
    """Ensures git commit SHA function returns non-empty string or 'unknown'."""
    commit = MLflowService.get_git_commit()
    assert isinstance(commit, str)
    assert len(commit) > 0


def test_mlflow_service_log_run(tmp_mlflow_uri, tmp_path):
    """Verifies complete training run logging to MLflow."""
    tracker = MLflowService(
        experiment_name="SentinelML-TestExperiment",
        tracking_uri=tmp_mlflow_uri,
    )

    # Dummy metrics & hyperparams
    metrics = {
        "pr_auc": 0.95,
        "recall": 0.90,
        "f1": 0.92,
        "precision": 0.94,
        "roc_auc": 0.98,
        "accuracy": 0.99,
        "training_time_sec": 1.25,
        "prediction_latency_ms": 0.05,
        "confusion_matrix": {"tn": 950, "fp": 10, "fn": 10, "tp": 30},
    }
    hyperparams = {"n_estimators": 50, "max_depth": 4, "learning_rate": 0.1}

    trainer = XGBoostTrainer(hyperparams=hyperparams)
    # Fit on synthetic data
    X_train = np.random.randn(50, 5)
    y_train = np.random.choice([0, 1], size=50)
    trainer.fit(X_train, y_train)

    preprocessor = FeaturePreprocessor(
        numerical_features=["feat1", "feat2"],
        categorical_features=["cat1"],
    )
    df_train = pd.DataFrame({
        "feat1": [1.0, 2.0],
        "feat2": [3.0, 4.0],
        "cat1": ["A", "B"],
    })
    preprocessor.fit(df_train)

    run_id = tracker.log_training_run(
        model_name="XGBoost",
        metrics=metrics,
        hyperparams=hyperparams,
        model_trainer=trainer,
        preprocessor=preprocessor,
        model_version="v1.0.0-test",
        dataset_version="v1.0.0-test",
        feature_version="v1.0.0-test",
        run_name="Test_Run_XGB",
    )

    assert isinstance(run_id, str)
    assert len(run_id) > 0

    # Retrieve run from MLflow client
    client = mlflow.tracking.MlflowClient()
    run_data = client.get_run(run_id)

    # Check tags
    assert run_data.data.tags.get("model_name") == "XGBoost"
    assert run_data.data.tags.get("model_version") == "v1.0.0-test"
    assert run_data.data.tags.get("dataset_version") == "v1.0.0-test"
    assert run_data.data.tags.get("feature_version") == "v1.0.0-test"
    assert "git_commit" in run_data.data.tags
    assert run_data.data.tags.get("framework") == "SentinelML"

    # Check metrics
    assert run_data.data.metrics.get("precision") == pytest.approx(0.94)
    assert run_data.data.metrics.get("recall") == pytest.approx(0.90)
    assert run_data.data.metrics.get("f1") == pytest.approx(0.92)
    assert run_data.data.metrics.get("roc_auc") == pytest.approx(0.98)
    assert run_data.data.metrics.get("pr_auc") == pytest.approx(0.95)
    assert run_data.data.metrics.get("training_time") == pytest.approx(1.25)
    assert run_data.data.metrics.get("prediction_latency") == pytest.approx(0.05)

    # Check params
    assert run_data.data.params.get("hyperparam_n_estimators") == "50"
    assert run_data.data.params.get("hyperparam_max_depth") == "4"
    assert "hyperparameters" in run_data.data.params
    assert "class_weighting" in run_data.data.params
    assert "preprocessing_config" in run_data.data.params

    # Check artifacts listed under run
    artifacts = [f.path for f in client.list_artifacts(run_id)]
    assert "evaluation" in artifacts
    assert "metadata" in artifacts
    assert "features" in artifacts
    assert "model" in artifacts
    assert "preprocessor" in artifacts or "preprocessing_pipeline" in artifacts
