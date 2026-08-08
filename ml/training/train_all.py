"""
Model Training Engine Orchestrator.
Trains, evaluates, and ranks Logistic Regression, Random Forest, XGBoost, and LightGBM models.
Ranks candidate models driven by PR-AUC as the primary selection metric for imbalanced fraud detection.
Saves winning model artifact, preprocessor, and metadata to artifacts/models/fraud_detector/v1/.
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.training.trainer_factory import TrainerFactory
from ml.training.base_trainer import BaseTrainer
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor
from ml.tracking.mlflow_service import MLflowService
from scripts.generate_synthetic_data import generate_synthetic_transactions
from scripts.process_dataset import run_pipeline


def load_dataset_split(data_dir: Path):
    """Loads processed dataset arrays and labels from data/processed/."""
    X_train_path = data_dir / "X_train.npy"
    X_val_path = data_dir / "X_val.npy"
    X_test_path = data_dir / "X_test.npy"
    y_train_path = data_dir / "y_train.csv"
    y_val_path = data_dir / "y_val.csv"
    y_test_path = data_dir / "y_test.csv"

    if not (X_train_path.exists() and y_train_path.exists()):
        print("Processed dataset missing. Executing dataset generation and preprocessing pipeline...")
        root = data_dir.parent.parent
        raw_csv = root / "data" / "raw" / "transactions_raw.csv"
        if not raw_csv.exists():
            df_syn = generate_synthetic_transactions(num_records=50000, fraud_ratio=0.02)
            raw_csv.parent.mkdir(parents=True, exist_ok=True)
            df_syn.to_csv(raw_csv, index=False)
        run_pipeline(raw_csv_path="data/raw/transactions_raw.csv", output_dir="data/processed", artifact_dir="artifacts")

    X_train = np.load(X_train_path)
    X_val = np.load(X_val_path)
    X_test = np.load(X_test_path)

    y_train = pd.read_csv(y_train_path).values.ravel()
    y_val = pd.read_csv(y_val_path).values.ravel()
    y_test = pd.read_csv(y_test_path).values.ravel()

    return X_train, y_train, X_val, y_val, X_test, y_test


def print_comparison_table(eval_results: list):
    """Prints rich ASCII comparison table of trained models ranked by PR-AUC."""
    header = (
        f"{'Rank':<5} | {'Model':<20} | {'PR-AUC*':<9} | {'Recall':<8} | {'F1-Score':<8} | "
        f"{'Precision':<9} | {'ROC-AUC':<8} | {'Accuracy':<8} | {'Train(s)':<8} | {'Lat(ms)':<8}"
    )
    separator = "=" * len(header)
    print("\n" + separator)
    print("                      SENTINELML MODEL CANDIDATE COMPARISON MATRIX                     ")
    print("          (* Primary Model Selection Metric: PR-AUC / Average Precision)               ")
    print(separator)
    print(header)
    print(separator)

    for rank, res in enumerate(eval_results, start=1):
        status_tag = " [WINNER]" if rank == 1 else ""
        model_name_str = f"{res['model_name']}{status_tag}"
        row = (
            f" {rank:<4} | {model_name_str:<20} | {res['pr_auc']:<9.4f} | {res['recall']:<8.4f} | "
            f"{res['f1']:<8.4f} | {res['precision']:<9.4f} | {res['roc_auc']:<8.4f} | "
            f"{res['accuracy']:<8.4f} | {res['training_time_sec']:<8.2f} | {res['prediction_latency_ms']:<8.4f}"
        )
        print(row)
    print(separator + "\n")


def run_training_pipeline(
    data_dir_str: str = "data/processed",
    output_model_dir: str = "artifacts/models/fraud_detector/v1",
):
    root = Path(__file__).resolve().parent.parent.parent
    data_dir = root / data_dir_str
    model_output_path = root / output_model_dir
    model_output_path.mkdir(parents=True, exist_ok=True)

    print("--- 1. Loading Preprocessed Dataset ---")
    X_train, y_train, X_val, y_val, X_test, y_test = load_dataset_split(data_dir)
    print(f"Loaded Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    print(f"Train Fraud Ratio: {y_train.mean()*100:.2f}%, Test Fraud Ratio: {y_test.mean()*100:.2f}%")

    model_keys = ["logistic_regression", "random_forest", "xgboost", "lightgbm"]
    trainers = []
    eval_results = []
    
    mlflow_tracker = MLflowService(experiment_name="SentinelML-FraudDetection")
    preprocessor = None
    prep_path = root / "artifacts" / "preprocessor_v1.joblib"
    if prep_path.exists():
        try:
            preprocessor = FeaturePreprocessor.load(str(prep_path))
        except Exception:
            preprocessor = None

    print("\n--- 2. Training Model Candidates & Tracking with MLflow ---")
    for key in model_keys:
        trainer = TrainerFactory.get_trainer(key)
        print(f"Training {trainer.model_name}...")
        trainer.fit(X_train, y_train)

        print(f"Evaluating {trainer.model_name} on Test Set...")
        metrics = trainer.evaluate(X_test, y_test)
        eval_results.append(metrics)
        trainers.append(trainer)

        # Log run cleanly via MLflowService abstraction
        try:
            mlflow_tracker.log_training_run(
                model_name=trainer.model_name,
                metrics=metrics,
                hyperparams=trainer.hyperparams,
                model_trainer=trainer,
                preprocessor=preprocessor,
                model_version="v1.0.0",
                dataset_version="v1.0.0",
                feature_version="v1.0.0",
            )
        except Exception as e:
            print(f"[Warning] Failed to log run to MLflow: {e}")

    # 3. Rank models strictly by PR-AUC (Primary Metric)
    eval_results.sort(key=lambda x: x["pr_auc"], reverse=True)
    best_eval = eval_results[0]
    best_model_name = best_eval["model_name"]

    # Map back to winning trainer instance
    best_trainer = next(t for t in trainers if t.model_name == best_model_name)

    print_comparison_table(eval_results)

    print(f"[WINNER] Winning Production Candidate: {best_model_name} (PR-AUC: {best_eval['pr_auc']:.4f})")

    # 4. Save Production Artifacts
    print(f"--- 3. Saving Production Artifacts to {model_output_path} ---")

    # Save best model
    model_file = model_output_path / "model.joblib"
    best_trainer.save_artifact(str(model_file))
    print(f"Saved winning model artifact: {model_file}")

    # Copy preprocessor artifact
    source_preprocessor = root / "artifacts" / "preprocessor_v1.joblib"
    dest_preprocessor = model_output_path / "preprocessor.joblib"
    if source_preprocessor.exists():
        shutil.copy(source_preprocessor, dest_preprocessor)
        print(f"Saved preprocessor artifact: {dest_preprocessor}")

    # Save model metadata
    metadata = {
        "model_name": "FraudDetector",
        "version": "v1.0.0",
        "selected_algorithm": best_model_name,
        "primary_selection_metric": "PR-AUC",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metrics": best_eval,
        "all_candidate_rankings": [
            {"rank": i + 1, "model": r["model_name"], "pr_auc": r["pr_auc"], "f1": r["f1"], "recall": r["recall"]}
            for i, r in enumerate(eval_results)
        ],
    }

    metadata_file = model_output_path / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata: {metadata_file}")

    print("Model Training Engine pipeline completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="Run SentinelML Model Training Engine")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Processed dataset directory")
    parser.add_argument("--output-dir", type=str, default="artifacts/models/fraud_detector/v1", help="Output artifact directory")
    args = parser.parse_args()

    run_training_pipeline(args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
