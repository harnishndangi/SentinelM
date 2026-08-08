"""
Optuna Hyperparameter Optimizer for SentinelML.
Prevents test data leakage by using only Train and Validation sets for hyperparameter selection.
Evaluates the final best model against the held-out Test set.
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import optuna

from ml.training.trainer_factory import TrainerFactory
from ml.training.tuning.search_spaces import get_search_space

# Disable Optuna verbose logging by default unless debugging
optuna.logging.set_verbosity(optuna.logging.WARNING)


class OptunaTuner:
    """
    Optuna hyperparameter optimization manager for SentinelML models.
    Supports XGBoost, LightGBM, Random Forest, and Logistic Regression baseline.
    Enforces PR-AUC objective metric optimization on Train/Val split and evaluates
    winning hyperparameters strictly on held-out Test set.
    """

    def __init__(
        self,
        model_type: str,
        n_trials: int = 50,
        timeout: Optional[float] = None,
        seed: int = 42,
        metric: str = "pr_auc",
        output_dir: str = "artifacts/tuning",
    ):
        self.model_type = model_type.lower().strip()
        self.n_trials = n_trials
        self.timeout = timeout
        self.seed = seed
        self.metric = metric
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.trial_history: List[Dict[str, Any]] = []
        self.best_params: Dict[str, Any] = {}
        self.best_score: float = 0.0
        self.optimization_duration_sec: float = 0.0
        self.study: Optional[optuna.Study] = None

    def optimize(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes Optuna study over specified trials and timeout.
        
        Data Leakage Prevention:
        - Objective function ONLY sees X_train/y_train and X_val/y_val.
        - X_test/y_test is NOT passed into the study objective function.
        - X_test/y_test is evaluated ONCE at the end for the selected best model.
        """
        search_space_fn = get_search_space(self.model_type)
        self.trial_history = []

        def objective(trial: optuna.Trial) -> float:
            trial_start = time.perf_counter()
            params = search_space_fn(trial)

            trainer = TrainerFactory.get_trainer(self.model_type, hyperparams=params)
            trainer.fit(X_train, y_train)

            # Evaluate strictly on validation set during hyperparameter search
            eval_metrics = trainer.evaluate(X_val, y_val)
            val_score = float(eval_metrics.get(self.metric, 0.0))

            trial_duration = float(round(time.perf_counter() - trial_start, 4))

            # Record trial details
            self.trial_history.append(
                {
                    "trial_number": trial.number,
                    "params": params,
                    "val_pr_auc": val_score,
                    "val_metrics": {
                        "pr_auc": eval_metrics.get("pr_auc", 0.0),
                        "f1": eval_metrics.get("f1", 0.0),
                        "recall": eval_metrics.get("recall", 0.0),
                        "precision": eval_metrics.get("precision", 0.0),
                        "roc_auc": eval_metrics.get("roc_auc", 0.0),
                    },
                    "duration_sec": trial_duration,
                    "state": "COMPLETE",
                }
            )

            return val_score

        sampler = optuna.samplers.TPESampler(seed=self.seed)
        self.study = optuna.create_study(direction="maximize", sampler=sampler)

        opt_start = time.perf_counter()
        self.study.optimize(objective, n_trials=self.n_trials, timeout=self.timeout)
        self.optimization_duration_sec = float(round(time.perf_counter() - opt_start, 4))

        self.best_params = self.study.best_params
        # Merge constant hyperparams (like random_state, n_jobs, etc.) into best_params if needed
        dummy_trial = optuna.trial.FixedTrial(self.best_params)
        full_best_params = search_space_fn(dummy_trial)
        self.best_params = full_best_params
        self.best_score = float(self.study.best_value)

        # Final evaluation on held-out test set if provided
        test_eval_metrics: Optional[Dict[str, Any]] = None
        if X_test is not None and y_test is not None:
            best_trainer = TrainerFactory.get_trainer(self.model_type, hyperparams=self.best_params)
            best_trainer.fit(X_train, y_train)
            test_eval_metrics = best_trainer.evaluate(X_test, y_test)

        summary = {
            "model_type": self.model_type,
            "objective_metric": self.metric,
            "best_score_val": self.best_score,
            "best_params": self.best_params,
            "n_trials_requested": self.n_trials,
            "n_trials_completed": len(self.study.trials),
            "optimization_duration_sec": self.optimization_duration_sec,
            "seed": self.seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_evaluation": test_eval_metrics,
            "trial_history": self.trial_history,
        }

        if save_results:
            self.save_results(summary)

        return summary

    def save_results(self, summary: Dict[str, Any]) -> str:
        """Saves optimization results and trial history to JSON file."""
        file_path = self.output_dir / f"optuna_results_{self.model_type}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return str(file_path)
