"""
CLI Runner for Optuna Hyperparameter Optimization in SentinelML.

Usage:
    python -m ml.training.tuning.run --model xgboost --trials 50
    python -m ml.training.tuning.run --model all --trials 20 --seed 42
    python -m ml.training.tuning.run --model lightgbm --trials 100 --timeout 300
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).resolve().parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from ml.training.train_all import load_dataset_split
from ml.training.tuning.tuner import OptunaTuner


def run_tuning_cli():
    parser = argparse.ArgumentParser(
        description="SentinelML Optuna Hyperparameter Optimization Engine"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="xgboost",
        choices=[
            "xgboost",
            "xgb",
            "lightgbm",
            "lgb",
            "lgbm",
            "random_forest",
            "rf",
            "logistic_regression",
            "logistic",
            "lr",
            "all",
        ],
        help="Target model type to optimize, or 'all' to tune XGBoost, LightGBM, Random Forest, & Logistic Regression baseline.",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=50,
        help="Number of Optuna trials per model study (default: 50).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Optimization timeout in seconds (default: None).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampler reproducibility (default: 42).",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/processed",
        help="Path to preprocessed dataset directory containing X_train.npy, etc.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="artifacts/tuning",
        help="Directory to save Optuna tuning results JSON files.",
    )

    args = parser.parse_args()

    data_dir_path = root_path / args.data_dir
    output_dir_path = root_path / args.output_dir

    print("================================================================================")
    print("                SENTINELML OPTUNA HYPERPARAMETER OPTIMIZATION ENGINE            ")
    print("================================================================================")
    print(f"Target Model(s): {args.model}")
    print(f"Number of Trials: {args.trials}")
    print(f"Timeout (seconds): {args.timeout}")
    print(f"Random Seed: {args.seed}")
    print(f"Data Directory: {data_dir_path}")
    print(f"Output Directory: {output_dir_path}")
    print("--------------------------------------------------------------------------------")

    print("\n--- Loading Preprocessed Dataset (Train / Val / Test) ---")
    X_train, y_train, X_val, y_val, X_test, y_test = load_dataset_split(data_dir_path)
    print(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}, Test Shape: {X_test.shape}")

    if args.model.lower() == "all":
        models_to_tune = ["xgboost", "lightgbm", "random_forest", "logistic_regression"]
    else:
        models_to_tune = [args.model.lower()]

    all_results = {}

    for model_name in models_to_tune:
        print(f"\n================================================================================")
        print(f" Starting Optuna Study for [{model_name.upper()}] ({args.trials} trials, seed={args.seed})")
        print(f" Note: Tuning uses Train/Val splits. Test set is evaluated ONLY after study completes.")
        print(f"================================================================================")

        tuner = OptunaTuner(
            model_type=model_name,
            n_trials=args.trials,
            timeout=args.timeout,
            seed=args.seed,
            metric="pr_auc",
            output_dir=str(output_dir_path),
        )

        result = tuner.optimize(
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
            save_results=True,
        )

        all_results[model_name] = result

        # Log tuned best model run to MLflow
        try:
            from ml.tracking.mlflow_service import MLflowService
            from ml.training.trainer_factory import TrainerFactory

            mlflow_tracker = MLflowService(experiment_name="SentinelML-FraudDetection")
            best_trainer = TrainerFactory.get_trainer(model_name, hyperparams=result["best_params"])
            best_trainer.fit(X_train, y_train)
            if result.get("test_evaluation"):
                mlflow_tracker.log_training_run(
                    model_name=f"{model_name}_tuned",
                    metrics=result["test_evaluation"],
                    hyperparams=result["best_params"],
                    model_trainer=best_trainer,
                    model_version="v1.0.0-tuned",
                    dataset_version="v1.0.0",
                    feature_version="v1.0.0",
                    run_name=f"Optuna_Tuned_{model_name.upper()}",
                )
        except Exception as e:
            print(f"[Warning] Failed to log tuning run to MLflow: {e}")

        print(f"\n[SUMMARY for {model_name.upper()}]")
        print(f"  Best Val PR-AUC Score: {result['best_score_val']:.4f}")
        if result["test_evaluation"]:
            print(f"  Held-out Test PR-AUC:  {result['test_evaluation']['pr_auc']:.4f}")
            print(f"  Held-out Test Recall:  {result['test_evaluation']['recall']:.4f}")
            print(f"  Held-out Test F1:      {result['test_evaluation']['f1']:.4f}")
        print(f"  Optimization Time:     {result['optimization_duration_sec']:.2f} seconds")
        print(f"  Best Hyperparameters:  {json.dumps(result['best_params'], indent=4)}")
        print(f"  Saved Results:         {output_dir_path / f'optuna_results_{model_name}.json'}")

    print("\n================================================================================")
    print("          OPTUNA HYPERPARAMETER OPTIMIZATION COMPLETED SUCCESSFULLY              ")
    print("================================================================================")


if __name__ == "__main__":
    run_tuning_cli()
