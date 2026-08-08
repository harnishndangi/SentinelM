import pytest
import pandas as pd
from scripts.generate_synthetic_data import generate_synthetic_transactions, MERCHANT_CATEGORIES, DEVICE_TYPES, REGIONS


def test_synthetic_data_generation_properties():
    num_records = 2000
    fraud_ratio = 0.03
    df = generate_synthetic_transactions(num_records=num_records, fraud_ratio=fraud_ratio, random_seed=42)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == num_records
    assert df.isnull().sum().sum() == 0

    # Verify columns
    expected_cols = [
        "transaction_amount", "transaction_hour", "merchant_category",
        "device_type", "device_age_days", "region", "account_age_days",
        "transactions_last_24h", "average_transaction_amount", "distance_from_home",
        "international_transaction", "failed_transactions_last_24h", "is_fraud"
    ]
    assert list(df.columns) == expected_cols

    # Verify fraud ratio calculation
    fraud_count = df["is_fraud"].sum()
    expected_fraud = int(num_records * fraud_ratio)
    assert fraud_count == expected_fraud

    # Verify categorical domains
    assert set(df["merchant_category"].unique()).issubset(set(MERCHANT_CATEGORIES))
    assert set(df["device_type"].unique()).issubset(set(DEVICE_TYPES))
    assert set(df["region"].unique()).issubset(set(REGIONS))
