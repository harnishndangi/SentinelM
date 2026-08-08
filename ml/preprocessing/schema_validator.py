from typing import Tuple, List, Dict, Any
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema

MERCHANT_CATEGORIES = ["retail", "electronics", "travel", "food", "online", "luxury", "entertainment", "utilities"]
DEVICE_TYPES = ["mobile_ios", "mobile_android", "desktop_mac", "desktop_windows", "tablet", "unknown"]
REGIONS = ["north_america", "europe", "asia_pacific", "latin_america", "middle_east", "africa"]

# Pandera Schema Definition
TransactionSchema = DataFrameSchema(
    columns={
        "transaction_amount": Column(float, Check.ge(0.0), nullable=False),
        "transaction_hour": Column(int, Check.in_range(0, 23), nullable=False),
        "merchant_category": Column(str, Check.isin(MERCHANT_CATEGORIES), nullable=False),
        "device_type": Column(str, Check.isin(DEVICE_TYPES), nullable=False),
        "device_age_days": Column(float, Check.ge(0.0), nullable=False),
        "region": Column(str, Check.isin(REGIONS), nullable=False),
        "account_age_days": Column(float, Check.ge(0.0), nullable=False),
        "transactions_last_24h": Column(int, Check.ge(0), nullable=False),
        "average_transaction_amount": Column(float, Check.ge(0.0), nullable=False),
        "distance_from_home": Column(float, Check.ge(0.0), nullable=False),
        "international_transaction": Column(int, Check.isin([0, 1]), nullable=False),
        "failed_transactions_last_24h": Column(int, Check.ge(0), nullable=False),
        "is_fraud": Column(int, Check.isin([0, 1]), nullable=False),
    },
    coerce=True,
    strict=False,
)


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates dataframe against Pandera TransactionSchema.
    Returns (is_valid, list_of_error_messages).
    """
    try:
        TransactionSchema.validate(df, lazy=True)
        return True, []
    except pa.errors.SchemaErrors as err:
        errors = [f"Schema Error at {failure['column']}: {failure['failure_case']}" for failure in err.failure_cases.to_dict('records')]
        return False, errors
    except Exception as e:
        return False, [str(e)]


def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Returns missing value count per column."""
    return df.isnull().sum().to_dict()


def detect_duplicates(df: pd.DataFrame) -> int:
    """Returns total count of duplicate rows."""
    return int(df.duplicated().sum())


def check_numerical_ranges(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Computes min, max, mean, std summary for numerical features."""
    num_cols = df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns
    summary = {}
    for col in num_cols:
        summary[col] = {
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": float(df[col].mean()),
            "std": float(df[col].std()),
        }
    return summary


def check_categorical_values(df: pd.DataFrame) -> Dict[str, List[str]]:
    """Returns unique categories present in categorical columns."""
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns
    return {col: df[col].unique().tolist() for col in cat_cols}
