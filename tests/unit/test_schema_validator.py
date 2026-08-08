import pytest
import pandas as pd
from ml.preprocessing.schema_validator import (
    validate_schema,
    detect_missing_values,
    detect_duplicates,
    check_numerical_ranges,
    check_categorical_values,
)
from scripts.generate_synthetic_data import generate_synthetic_transactions


def test_schema_validator_success():
    df = generate_synthetic_transactions(num_records=500, fraud_ratio=0.02, random_seed=42)
    is_valid, errors = validate_schema(df)
    assert is_valid is True
    assert len(errors) == 0

    assert sum(detect_missing_values(df).values()) == 0
    assert detect_duplicates(df) == 0


def test_schema_validator_failure_cases():
    df = generate_synthetic_transactions(num_records=100, fraud_ratio=0.02, random_seed=42)

    # Inject negative transaction amount
    invalid_df = df.copy()
    invalid_df.loc[0, "transaction_amount"] = -50.0
    is_valid, errors = validate_schema(invalid_df)
    assert is_valid is False
    assert len(errors) > 0

    # Inject invalid categorical value
    invalid_df2 = df.copy()
    invalid_df2.loc[0, "merchant_category"] = "unauthorized_category"
    is_valid2, errors2 = validate_schema(invalid_df2)
    assert is_valid2 is False
    assert len(errors2) > 0
