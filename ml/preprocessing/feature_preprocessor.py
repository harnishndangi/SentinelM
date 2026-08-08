from typing import Tuple, List, Dict, Any, Optional
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder


NUMERICAL_FEATURES = [
    "transaction_amount",
    "transaction_hour",
    "device_age_days",
    "account_age_days",
    "transactions_last_24h",
    "average_transaction_amount",
    "distance_from_home",
    "international_transaction",
    "failed_transactions_last_24h",
]

CATEGORICAL_FEATURES = [
    "merchant_category",
    "device_type",
    "region",
]


class FeaturePreprocessor:
    """
    Leakage-free Feature Preprocessor for Fraud Detection.
    Scales numerical features using StandardScaler and encodes categorical features using OneHotEncoder.
    Fitting occurs strictly on the training set.
    """

    def __init__(self, numerical_features: List[str] = None, categorical_features: List[str] = None):
        self.numerical_features = numerical_features or NUMERICAL_FEATURES
        self.categorical_features = categorical_features or CATEGORICAL_FEATURES
        
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        self.is_fitted = False
        self.feature_names_out_: List[str] = []

    def fit(self, X: pd.DataFrame) -> "FeaturePreprocessor":
        """
        Fits StandardScaler and OneHotEncoder on training dataframe ONLY.
        Prevents data leakage from validation/test sets.
        """
        num_data = X[self.numerical_features]
        cat_data = X[self.categorical_features]

        self.scaler.fit(num_data)
        self.encoder.fit(cat_data)

        # Build output feature names
        cat_encoded_names = list(self.encoder.get_feature_names_out(self.categorical_features))
        self.feature_names_out_ = self.numerical_features + cat_encoded_names
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Transforms input dataframe using fitted scaler and encoder.
        Raises ValueError if preprocessor is not fitted yet.
        """
        if not self.is_fitted:
            raise ValueError("FeaturePreprocessor is not fitted yet. Call 'fit' on training data first.")

        num_scaled = self.scaler.transform(X[self.numerical_features])
        cat_encoded = self.encoder.transform(X[self.categorical_features])

        return np.hstack([num_scaled, cat_encoded])

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Fits preprocessor on X and transforms X."""
        return self.fit(X).transform(X)

    def save(self, file_path: str) -> None:
        """Saves fitted preprocessor to disk using joblib."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        joblib.dump(self, file_path)

    @classmethod
    def load(cls, file_path: str) -> "FeaturePreprocessor":
        """Loads fitted preprocessor from disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Preprocessor artifact not found at {file_path}")
        return joblib.load(file_path)


def stratified_train_val_test_split(
    df: pd.DataFrame,
    target_col: str = "is_fraud",
    train_size: float = 0.70,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Splits dataframe into Train, Validation, and Test sets stratified by target_col.
    """
    assert abs((train_size + val_size + test_size) - 1.0) < 1e-5, "Split sizes must sum to 1.0"

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # First split: Train vs (Val + Test)
    temp_size = val_size + test_size
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=temp_size, random_state=random_state, stratify=y
    )

    # Second split: Val vs Test
    relative_test_size = test_size / temp_size
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=relative_test_size, random_state=random_state, stratify=y_temp
    )

    return X_train, y_train, X_val, y_val, X_test, y_test
