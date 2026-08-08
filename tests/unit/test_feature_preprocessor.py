import os
import pytest
import numpy as np
import pandas as pd
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor, stratified_train_val_test_split
from scripts.generate_synthetic_data import generate_synthetic_transactions


def test_stratified_train_val_test_split():
    df = generate_synthetic_transactions(num_records=1000, fraud_ratio=0.02, random_seed=42)
    X_train, y_train, X_val, y_val, X_test, y_test = stratified_train_val_test_split(
        df=df, target_col="is_fraud", train_size=0.70, val_size=0.15, test_size=0.15
    )

    assert len(X_train) == 700
    assert len(X_val) == 150
    assert len(X_test) == 150

    # Verify fraud ratio stratification consistency
    train_fraud_rate = y_train.mean()
    val_fraud_rate = y_val.mean()
    test_fraud_rate = y_test.mean()

    assert abs(train_fraud_rate - 0.02) < 0.01
    assert abs(val_fraud_rate - 0.02) < 0.01
    assert abs(test_fraud_rate - 0.02) < 0.01


def test_feature_preprocessor_fit_transform_and_joblib(tmp_path):
    df = generate_synthetic_transactions(num_records=1000, fraud_ratio=0.02, random_seed=42)
    X_train, y_train, X_val, y_val, X_test, y_test = stratified_train_val_test_split(df, "is_fraud")

    preprocessor = FeaturePreprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)

    assert isinstance(X_train_proc, np.ndarray)
    assert X_train_proc.shape[0] == len(X_train)
    assert X_val_proc.shape[0] == len(X_val)
    assert X_train_proc.shape[1] == X_val_proc.shape[1]

    # Test saving & loading joblib artifact
    artifact_file = os.path.join(tmp_path, "preprocessor_test.joblib")
    preprocessor.save(artifact_file)
    assert os.path.exists(artifact_file)

    loaded_preprocessor = FeaturePreprocessor.load(artifact_file)
    X_val_proc_loaded = loaded_preprocessor.transform(X_val)

    np.testing.assert_allclose(X_val_proc, X_val_proc_loaded)
