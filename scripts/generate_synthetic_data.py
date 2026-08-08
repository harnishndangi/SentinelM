"""
Synthetic Fraud Transaction Data Generator.
Generates realistic binary transaction fraud classification dataset with controllable class imbalance.
"""
import argparse
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Categorical Domains
MERCHANT_CATEGORIES = ["retail", "electronics", "travel", "food", "online", "luxury", "entertainment", "utilities"]
DEVICE_TYPES = ["mobile_ios", "mobile_android", "desktop_mac", "desktop_windows", "tablet", "unknown"]
REGIONS = ["north_america", "europe", "asia_pacific", "latin_america", "middle_east", "africa"]


def _normalize_probs(p_list):
    arr = np.array(p_list, dtype=np.float64)
    return arr / arr.sum()


def generate_synthetic_transactions(
    num_records: int = 50000,
    fraud_ratio: float = 0.02,
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generates synthetic transaction dataframe with realistic feature distributions for fraud detection.
    """
    np.random.seed(random_seed)

    num_fraud = int(num_records * fraud_ratio)
    num_legit = num_records - num_fraud

    # Legitimate Transactions
    legit_p_hour = _normalize_probs([
        0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.04, 0.06, 0.07, 0.08, 0.08, 0.08,
        0.08, 0.07, 0.07, 0.06, 0.05, 0.05, 0.04, 0.03, 0.03, 0.02, 0.01, 0.01
    ])
    legit_p_merchant = _normalize_probs([0.25, 0.15, 0.10, 0.20, 0.15, 0.03, 0.07, 0.05])
    legit_p_device = _normalize_probs([0.40, 0.35, 0.10, 0.10, 0.04, 0.01])
    legit_p_region = _normalize_probs([0.45, 0.25, 0.15, 0.08, 0.05, 0.02])

    legit_df = pd.DataFrame({
        "transaction_amount": np.random.exponential(scale=60.0, size=num_legit) + 1.0,
        "transaction_hour": np.random.choice(np.arange(24), size=num_legit, p=legit_p_hour),
        "merchant_category": np.random.choice(MERCHANT_CATEGORIES, size=num_legit, p=legit_p_merchant),
        "device_type": np.random.choice(DEVICE_TYPES, size=num_legit, p=legit_p_device),
        "device_age_days": np.random.uniform(30, 1000, size=num_legit),
        "region": np.random.choice(REGIONS, size=num_legit, p=legit_p_region),
        "account_age_days": np.random.uniform(60, 2000, size=num_legit),
        "transactions_last_24h": np.random.poisson(lam=3, size=num_legit),
        "average_transaction_amount": np.random.normal(loc=55.0, scale=15.0, size=num_legit).clip(min=5.0),
        "distance_from_home": np.random.exponential(scale=12.0, size=num_legit),
        "international_transaction": np.random.choice([0, 1], size=num_legit, p=_normalize_probs([0.95, 0.05])),
        "failed_transactions_last_24h": np.random.choice([0, 1, 2], size=num_legit, p=_normalize_probs([0.92, 0.06, 0.02])),
        "is_fraud": 0,
    })

    # Fraudulent Transactions
    fraud_p_hour = _normalize_probs([
        0.08, 0.09, 0.09, 0.08, 0.07, 0.04, 0.02, 0.01, 0.01, 0.02, 0.02, 0.03,
        0.03, 0.03, 0.03, 0.04, 0.04, 0.05, 0.05, 0.05, 0.04, 0.04, 0.04, 0.03
    ])
    fraud_p_merchant = _normalize_probs([0.05, 0.25, 0.20, 0.05, 0.25, 0.15, 0.03, 0.02])
    fraud_p_device = _normalize_probs([0.20, 0.20, 0.10, 0.20, 0.10, 0.20])
    fraud_p_region = _normalize_probs([0.25, 0.20, 0.20, 0.15, 0.10, 0.10])

    fraud_df = pd.DataFrame({
        "transaction_amount": np.random.exponential(scale=350.0, size=num_fraud) + 80.0,
        "transaction_hour": np.random.choice(np.arange(24), size=num_fraud, p=fraud_p_hour),
        "merchant_category": np.random.choice(MERCHANT_CATEGORIES, size=num_fraud, p=fraud_p_merchant),
        "device_type": np.random.choice(DEVICE_TYPES, size=num_fraud, p=fraud_p_device),
        "device_age_days": np.random.uniform(0, 45, size=num_fraud),
        "region": np.random.choice(REGIONS, size=num_fraud, p=fraud_p_region),
        "account_age_days": np.random.uniform(1, 180, size=num_fraud),
        "transactions_last_24h": np.random.poisson(lam=8, size=num_fraud),
        "average_transaction_amount": np.random.normal(loc=60.0, scale=20.0, size=num_fraud).clip(min=5.0),
        "distance_from_home": np.random.exponential(scale=150.0, size=num_fraud) + 20.0,
        "international_transaction": np.random.choice([0, 1], size=num_fraud, p=_normalize_probs([0.40, 0.60])),
        "failed_transactions_last_24h": np.random.choice([0, 1, 2, 3, 4], size=num_fraud, p=_normalize_probs([0.30, 0.30, 0.20, 0.12, 0.08])),
        "is_fraud": 1,
    })

    # Combine & shuffle dataset
    df = pd.concat([legit_df, fraud_df], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)

    # Integer types
    int_cols = ["transaction_hour", "transactions_last_24h", "international_transaction", "failed_transactions_last_24h", "is_fraud"]
    df[int_cols] = df[int_cols].astype(int)

    # Round continuous numerical columns
    round_cols = ["transaction_amount", "device_age_days", "account_age_days", "average_transaction_amount", "distance_from_home"]
    df[round_cols] = df[round_cols].round(2)

    return df


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction fraud dataset")
    parser.add_argument("--num-records", type=int, default=50000, help="Total dataset row count (default 50,000)")
    parser.add_argument("--fraud-ratio", type=float, default=0.02, help="Fraud ratio between 0.01 and 0.03 (default 0.02)")
    parser.add_argument("--output-path", type=str, default="data/raw/transactions_raw.csv", help="Destination CSV path")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    output_file = root_dir / args.output_path
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.num_records} transaction records with {args.fraud_ratio*100:.1f}% fraud ratio...")
    df = generate_synthetic_transactions(num_records=args.num_records, fraud_ratio=args.fraud_ratio)

    df.to_csv(output_file, index=False)
    print(f"Saved dataset to {output_file} (Rows: {len(df)}, Fraud Count: {df['is_fraud'].sum()})")


if __name__ == "__main__":
    main()
