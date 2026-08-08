# MLflow Experiment Tracking for SentinelML

SentinelML includes a clean, centralized MLflow experiment tracking service located in `ml/tracking/mlflow_service.py`.

## Features
- **Experiment Tracking**: Groups all runs under `SentinelML-FraudDetection`.
- **System Tags**: `model_name`, `model_version`, `dataset_version`, `feature_version`, `git_commit`.
- **Hyperparameter Logging**: Model hyperparameters, class weighting (`scale_pos_weight`, `class_weight`), preprocessing configuration.
- **Metrics**: `pr_auc`, `recall`, `f1`, `precision`, `roc_auc`, `accuracy`, `training_time_sec`, `prediction_latency_ms`.
- **Artifacts**:
  - `model/model.joblib`: Serialized model binary.
  - `preprocessor/preprocessor.joblib`: Serialized feature preprocessor pipeline.
  - `evaluation/confusion_matrix.png` & `confusion_matrix.json`: Visual plot & numerical matrix.
  - `features/feature_list.json`: Output feature list and input schema specs.
  - `metadata/metadata.json`: Full execution metadata.
  - `evaluation/evaluation_report.json`: Formatted evaluation metrics summary.

---

## Launching MLflow Locally (No Docker Required)

You can launch MLflow locally using SQLite or file store without needing Docker.

### Option 1: Launch MLflow UI (Simple Local View)
To view all tracked runs and artifacts in your browser:
```bash
python -m mlflow ui --port 5000
```
Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000).

### Option 2: Launch MLflow Tracking Server with SQLite Backend
For production-like local experiment tracking with persistent backend store and artifact root:
```bash
python -m mlflow server --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns --host 127.0.0.1 --port 5000
```

### Configuring Environment Variable (Optional)
By default, `MLflowService` points to `sqlite:///mlflow.db`. You can override the backend by setting:
```bash
set MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

---

## Python API Usage

```python
from ml.tracking.mlflow_service import MLflowService

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
```
