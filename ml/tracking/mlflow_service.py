"""
MLflow Experiment Tracking Service for SentinelML.

Provides a clean, centralized abstraction for experiment tracking across training and tuning.
Encapsulates MLflow run management, parameter logging, metric recording, tag tracking,
and artifact logging (model, preprocessor, confusion matrix, feature list, metadata, evaluation report).
"""
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd

# Lazy import or direct import of MLflow
import mlflow


class MLflowService:
    """
    Centralized MLflow Experiment Tracker for SentinelML.
    
    Usage:
        tracker = MLflowService(experiment_name="SentinelML-FraudDetection")
        tracker.log_training_run(
            model_name="XGBoost",
            metrics=eval_metrics,
            hyperparams=hyperparams,
            model_trainer=trainer,
            preprocessor=preprocessor,
            model_version="v1.0.0",
            dataset_version="v1.0.0",
            feature_version="v1.0.0",
        )
    """

    def __init__(
        self,
        experiment_name: str = "SentinelML-FraudDetection",
        tracking_uri: Optional[str] = None,
    ):
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri or os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")

        # Set tracking URI and experiment
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)

    @staticmethod
    def get_git_commit() -> str:
        """Retrieves current Git commit SHA if available."""
        try:
            commit = (
                subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
                .decode("utf-8")
                .strip()
            )
            return commit
        except Exception:
            return "unknown"

    def _generate_confusion_matrix_artifacts(
        self, cm_dict: Dict[str, int], temp_dir: str
    ) -> List[str]:
        """Generates visual plot and JSON artifact for confusion matrix."""
        artifact_paths = []
        cm_json_path = os.path.join(temp_dir, "confusion_matrix.json")
        with open(cm_json_path, "w", encoding="utf-8") as f:
            json.dump(cm_dict, f, indent=2)
        artifact_paths.append(cm_json_path)

        # Plot visual confusion matrix plot if matplotlib is available
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(5, 4))
            cm_matrix = np.array([
                [cm_dict.get("tn", 0), cm_dict.get("fp", 0)],
                [cm_dict.get("fn", 0), cm_dict.get("tp", 0)]
            ])
            cax = ax.matshow(cm_matrix, cmap="Blues")
            fig.colorbar(cax)

            for i in range(2):
                for j in range(2):
                    ax.text(j, i, str(cm_matrix[i, j]), va="center", ha="center", color="red", fontsize=12)

            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["Non-Fraud (0)", "Fraud (1)"])
            ax.set_yticklabels(["Non-Fraud (0)", "Fraud (1)"])
            ax.set_xlabel("Predicted Label")
            ax.set_ylabel("True Label")
            ax.set_title("Confusion Matrix")

            plt.tight_layout()
            plot_path = os.path.join(temp_dir, "confusion_matrix.png")
            plt.savefig(plot_path, dpi=150)
            plt.close(fig)
            artifact_paths.append(plot_path)
        except Exception:
            pass

        return artifact_paths

    def log_training_run(
        self,
        model_name: str,
        metrics: Dict[str, Any],
        hyperparams: Optional[Dict[str, Any]] = None,
        model_trainer: Optional[Any] = None,
        preprocessor: Optional[Any] = None,
        model_version: str = "v1.0.0",
        dataset_version: str = "v1.0.0",
        feature_version: str = "v1.0.0",
        run_name: Optional[str] = None,
        artifact_dir: Optional[str] = None,
    ) -> str:
        """
        Logs a complete model training run to MLflow.
        
        Tracks:
        - Tags: model_name, model_version, dataset_version, feature_version, git_commit
        - Parameters: hyperparameters, preprocessing configuration, class weighting
        - Metrics: precision, recall, f1, roc_auc, pr_auc, training_time, prediction_latency
        - Artifacts: model, preprocessing pipeline, confusion matrix, feature list, metadata, evaluation report
        """
        effective_run_name = run_name or f"{model_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=effective_run_name) as run:
            # 1. Track System & Model Tags
            mlflow.set_tag("model_name", model_name)
            mlflow.set_tag("model_version", model_version)
            mlflow.set_tag("dataset_version", dataset_version)
            mlflow.set_tag("feature_version", feature_version)
            mlflow.set_tag("git_commit", self.get_git_commit())
            mlflow.set_tag("framework", "SentinelML")

            # 2. Track Parameters
            params_to_log = {}
            hp = hyperparams or (model_trainer.hyperparams if model_trainer else {})
            for k, v in hp.items():
                params_to_log[f"hyperparam_{k}"] = str(v)

            params_to_log["hyperparameters"] = json.dumps(hp)

            # Extract Class Weighting
            class_weight = hp.get("scale_pos_weight", hp.get("class_weight", "default"))
            params_to_log["class_weighting"] = str(class_weight)

            # Preprocessing Configuration
            if preprocessor and hasattr(preprocessor, "numerical_features"):
                num_count = len(preprocessor.numerical_features)
                cat_count = len(preprocessor.categorical_features)
                params_to_log["preprocessing_config"] = (
                    f"StandardScaler({num_count} num) + OneHotEncoder({cat_count} cat)"
                )
                params_to_log["preprocessing_configuration"] = params_to_log["preprocessing_config"]
            else:
                params_to_log["preprocessing_config"] = "StandardScaler + OneHotEncoder"
                params_to_log["preprocessing_configuration"] = params_to_log["preprocessing_config"]

            mlflow.log_params(params_to_log)

            # 3. Track Metrics
            metrics_to_log = {
                "precision": float(metrics.get("precision", 0.0)),
                "recall": float(metrics.get("recall", 0.0)),
                "f1": float(metrics.get("f1", 0.0)),
                "roc_auc": float(metrics.get("roc_auc", 0.0)),
                "pr_auc": float(metrics.get("pr_auc", 0.0)),
                "training_time": float(metrics.get("training_time_sec", metrics.get("training_time", 0.0))),
                "training_time_sec": float(metrics.get("training_time_sec", metrics.get("training_time", 0.0))),
                "prediction_latency": float(metrics.get("prediction_latency_ms", metrics.get("prediction_latency", 0.0))),
                "prediction_latency_ms": float(metrics.get("prediction_latency_ms", metrics.get("prediction_latency", 0.0))),
                "accuracy": float(metrics.get("accuracy", 0.0)),
            }
            mlflow.log_metrics(metrics_to_log)

            # 4. Generate and Track Artifacts
            with tempfile.TemporaryDirectory() as temp_dir:
                # A. Confusion Matrix Artifacts
                cm_dict = metrics.get("confusion_matrix", {"tn": 0, "fp": 0, "fn": 0, "tp": 0})
                cm_files = self._generate_confusion_matrix_artifacts(cm_dict, temp_dir)
                for cm_file in cm_files:
                    mlflow.log_artifact(cm_file, artifact_path="evaluation")

                # B. Feature List Artifact
                feature_names = []
                if preprocessor and hasattr(preprocessor, "feature_names_out_"):
                    feature_names = preprocessor.feature_names_out_
                elif preprocessor and hasattr(preprocessor, "numerical_features"):
                    feature_names = preprocessor.numerical_features + preprocessor.categorical_features

                feature_list_path = os.path.join(temp_dir, "feature_list.json")
                with open(feature_list_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "feature_count": len(feature_names),
                            "feature_names": feature_names,
                            "numerical_features": getattr(preprocessor, "numerical_features", []),
                            "categorical_features": getattr(preprocessor, "categorical_features", []),
                        },
                        f,
                        indent=2,
                    )
                mlflow.log_artifact(feature_list_path, artifact_path="features")

                # C. Metadata Artifact
                metadata_path = os.path.join(temp_dir, "metadata.json")
                run_metadata = {
                    "model_name": model_name,
                    "model_version": model_version,
                    "dataset_version": dataset_version,
                    "feature_version": feature_version,
                    "git_commit": self.get_git_commit(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "hyperparameters": hp,
                    "metrics": metrics_to_log,
                }
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(run_metadata, f, indent=2)
                mlflow.log_artifact(metadata_path, artifact_path="metadata")

                # D. Evaluation Report Artifact
                report_path = os.path.join(temp_dir, "evaluation_report.json")
                eval_report = {
                    "model_name": model_name,
                    "evaluation_summary": {
                        "PR-AUC (Primary Metric)": metrics_to_log["pr_auc"],
                        "Recall": metrics_to_log["recall"],
                        "F1-Score": metrics_to_log["f1"],
                        "Precision": metrics_to_log["precision"],
                        "ROC-AUC": metrics_to_log["roc_auc"],
                        "Accuracy": metrics_to_log["accuracy"],
                        "Training Duration (s)": metrics_to_log["training_time_sec"],
                        "Prediction Latency (ms/sample)": metrics_to_log["prediction_latency_ms"],
                    },
                    "confusion_matrix": cm_dict,
                }
                with open(report_path, "w", encoding="utf-8") as f:
                    json.dump(eval_report, f, indent=2)
                mlflow.log_artifact(report_path, artifact_path="evaluation")

                # E. Model Artifact & Preprocessing Pipeline Artifact
                if model_trainer and hasattr(model_trainer, "save_artifact"):
                    model_artifact_path = os.path.join(temp_dir, "model.joblib")
                    model_trainer.save_artifact(model_artifact_path)
                    mlflow.log_artifact(model_artifact_path, artifact_path="model")

                if preprocessor and hasattr(preprocessor, "save"):
                    prep_artifact_path = os.path.join(temp_dir, "preprocessor.joblib")
                    preprocessor.save(prep_artifact_path)
                    mlflow.log_artifact(prep_artifact_path, artifact_path="preprocessor")
                    mlflow.log_artifact(prep_artifact_path, artifact_path="preprocessing_pipeline")

            print(f"[MLflow] Training run for '{model_name}' logged to experiment '{self.experiment_name}' (Run ID: {run.info.run_id})")
            return run.info.run_id
