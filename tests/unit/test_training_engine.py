import os
import pytest
import numpy as np
from ml.training.trainer_factory import TrainerFactory
from ml.training.base_trainer import BaseTrainer
from ml.training.logistic_trainer import LogisticRegressionTrainer
from ml.training.random_forest_trainer import RandomForestTrainer
from ml.training.xgboost_trainer import XGBoostTrainer
from ml.training.lightgbm_trainer import LightGBMTrainer


def generate_dummy_data(n_samples=500, n_features=10):
    np.random.seed(42)
    X = np.random.randn(n_samples, n_features)
    # Synthetic target with ~5% positives
    y = (X[:, 0] + X[:, 1] > 1.5).astype(int)
    return X, y


def test_trainer_factory():
    lr = TrainerFactory.get_trainer("logistic_regression")
    rf = TrainerFactory.get_trainer("random_forest")
    xgb = TrainerFactory.get_trainer("xgboost")
    lgb = TrainerFactory.get_trainer("lightgbm")

    assert isinstance(lr, LogisticRegressionTrainer)
    assert isinstance(rf, RandomForestTrainer)
    assert isinstance(xgb, XGBoostTrainer)
    assert isinstance(lgb, LightGBMTrainer)

    with pytest.raises(ValueError):
        TrainerFactory.get_trainer("non_existent_model")


@pytest.mark.parametrize("model_key", ["logistic", "rf", "xgb", "lgb"])
def test_trainers_fit_evaluate_and_save(model_key, tmp_path):
    X, y = generate_dummy_data(n_samples=600, n_features=8)
    split = 450
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    trainer = TrainerFactory.get_trainer(model_key)
    trainer.fit(X_train, y_train)

    assert trainer.is_fitted is True
    assert trainer.training_time_sec >= 0.0

    eval_metrics = trainer.evaluate(X_test, y_test)

    assert "pr_auc" in eval_metrics
    assert "recall" in eval_metrics
    assert "f1" in eval_metrics
    assert "precision" in eval_metrics
    assert "roc_auc" in eval_metrics
    assert "accuracy" in eval_metrics
    assert "confusion_matrix" in eval_metrics
    assert "prediction_latency_ms" in eval_metrics

    assert 0.0 <= eval_metrics["pr_auc"] <= 1.0
    assert 0.0 <= eval_metrics["accuracy"] <= 1.0

    # Test saving & loading artifact
    artifact_path = os.path.join(tmp_path, f"{model_key}_model.joblib")
    trainer.save_artifact(artifact_path)
    assert os.path.exists(artifact_path)

    loaded_trainer = TrainerFactory.get_trainer(model_key)
    loaded_trainer.load_artifact(artifact_path)
    assert loaded_trainer.is_fitted is True

    y_pred_original = trainer.predict(X_test)
    y_pred_loaded = loaded_trainer.predict(X_test)
    np.testing.assert_array_equal(y_pred_original, y_pred_loaded)
