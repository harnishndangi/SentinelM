"""
End-to-end Dataset Processing Pipeline Execution Script.
Loads raw transaction dataset, executes Pandera schema validation, performs leakage-free stratified split,
fits FeaturePreprocessor on training set, saves fitted joblib artifact, and outputs processed datasets & metadata.
"""
import argparse
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.preprocessing.dataset_loader import DatasetLoader
from ml.preprocessing.schema_validator import validate_schema, detect_missing_values, detect_duplicates
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor, stratified_train_val_test_split


def run_pipeline(raw_csv_path: str, output_dir: str, artifact_dir: str):
    root = Path(__file__).resolve().parent.parent
    raw_file = root / raw_csv_path
    out_path = root / output_dir
    art_path = root / artifact_dir

    out_path.mkdir(parents=True, exist_ok=True)
    art_path.mkdir(parents=True, exist_ok=True)

    print(f"--- 1. Loading Raw Dataset: {raw_file} ---")
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw dataset file not found at {raw_file}. Run scripts/generate_synthetic_data.py first.")

    df = DatasetLoader.load_csv(str(raw_file))
    print(f"Loaded {len(df)} rows, {df.shape[1]} columns.")

    print("--- 2. Validating Pandera Schema & Quality Checks ---")
    is_valid, errors = validate_schema(df)
    missing_counts = detect_missing_values(df)
    duplicate_count = detect_duplicates(df)

    total_missing = sum(missing_counts.values())
    validation_status = "PASSED" if (is_valid and total_missing == 0 and duplicate_count == 0) else "WARNINGS/FAILED"
    print(f"Schema Validation Status: {validation_status}")
    if errors:
        print(f"Validation Errors: {errors}")
    print(f"Missing Values Count: {total_missing}, Duplicate Rows: {duplicate_count}")

    print("--- 3. Generating Dataset Metadata ---")
    metadata = DatasetLoader.generate_dataset_metadata(
        df=df,
        target_col="is_fraud",
        version="v1.0.0",
        source=str(raw_csv_path),
        validation_status=validation_status,
    )
    metadata_file = out_path / "metadata_v1.json"
    DatasetLoader.save_metadata(metadata, str(metadata_file))
    print(f"Saved metadata to {metadata_file} (Fraud %: {metadata['fraud_percentage']}%)")

    print("--- 4. Stratified Train / Val / Test Split (70% / 15% / 15%) ---")
    X_train, y_train, X_val, y_val, X_test, y_test = stratified_train_val_test_split(
        df=df, target_col="is_fraud", train_size=0.70, val_size=0.15, test_size=0.15
    )
    print(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}, Test Shape: {X_test.shape}")

    print("--- 5. Fitting FeaturePreprocessor strictly on Train split (Preventing Data Leakage) ---")
    preprocessor = FeaturePreprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    print(f"Preprocessed Feature Array Shape: {X_train_proc.shape}")

    print("--- 6. Saving Fitted Preprocessor Artifact ---")
    preprocessor_artifact = art_path / "preprocessor_v1.joblib"
    preprocessor.save(str(preprocessor_artifact))
    print(f"Saved preprocessor artifact to {preprocessor_artifact}")

    print("--- 7. Saving Processed Data Arrays ---")
    np.save(out_path / "X_train.npy", X_train_proc)
    np.save(out_path / "X_val.npy", X_val_proc)
    np.save(out_path / "X_test.npy", X_test_proc)

    y_train.to_csv(out_path / "y_train.csv", index=False)
    y_val.to_csv(out_path / "y_val.csv", index=False)
    y_test.to_csv(out_path / "y_test.csv", index=False)

    print("Pipeline execution completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Run dataset ingestion, validation, and preprocessing pipeline")
    parser.add_argument("--raw-csv", type=str, default="data/raw/transactions_raw.csv", help="Input raw CSV path")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for processed arrays")
    parser.add_argument("--artifact-dir", type=str, default="artifacts", help="Output directory for fitted preprocessor")
    args = parser.parse_args()

    run_pipeline(args.raw_csv, args.output_dir, args.artifact_dir)


if __name__ == "__main__":
    main()
