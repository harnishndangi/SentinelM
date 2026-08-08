from typing import Dict, Any, Tuple
import hashlib
import json
from datetime import datetime, timezone
import pandas as pd


class DatasetLoader:
    """Dataset loading, schema hashing, and metadata tracking utility."""

    @staticmethod
    def load_csv(file_path: str) -> pd.DataFrame:
        """Loads dataset from CSV file."""
        return pd.read_csv(file_path)

    @staticmethod
    def compute_schema_hash(df: pd.DataFrame) -> str:
        """Computes deterministic schema MD5 hash based on column names and data types."""
        schema_repr = ",".join([f"{col}:{df[col].dtype}" for col in sorted(df.columns)])
        return hashlib.md5(schema_repr.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_dataset_metadata(
        df: pd.DataFrame,
        target_col: str = "is_fraud",
        version: str = "v1.0.0",
        source: str = "data/raw/transactions_raw.csv",
        validation_status: str = "PASSED",
    ) -> Dict[str, Any]:
        """
        Generates dataset metadata summary.
        """
        total_rows = len(df)
        fraud_count = int(df[target_col].sum()) if target_col in df.columns else 0
        fraud_pct = float(round((fraud_count / total_rows) * 100, 4)) if total_rows > 0 else 0.0

        return {
            "dataset_version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "row_count": total_rows,
            "feature_count": df.shape[1] - (1 if target_col in df.columns else 0),
            "fraud_count": fraud_count,
            "fraud_percentage": fraud_pct,
            "schema_hash": DatasetLoader.compute_schema_hash(df),
            "source": source,
            "validation_status": validation_status,
        }

    @staticmethod
    def save_metadata(metadata: Dict[str, Any], output_path: str) -> None:
        """Saves dataset metadata to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
