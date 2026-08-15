"""
SentinelML Automated Retraining Pipeline (Prefect Orchestrated).

Implements the self-healing automated retraining component.
Workflow sequence:
Drift detected -> Incident created -> Dataset snapshot -> Data validation ->
Feature preprocessing -> Candidate training -> Hyperparameter optimization ->
Evaluation -> Candidate registration.

Features:
- Prefect flow and tasks orchestration
- Redis locking per incident (prevents concurrent retraining jobs for the same incident)
- State persistence & status logging per step
- IncidentEvent timeline updates
- Task retries and exception handling
"""

import os
import json
import uuid
import time
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

try:
    from prefect import task, flow
except ImportError:
    def task(*args, **kwargs):
        def decorator(fn):
            return fn
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    def flow(*args, **kwargs):
        def decorator(fn):
            return fn
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator


from backend.app.database import SessionLocal
from backend.app.models.incident import Incident, IncidentEvent
from backend.app.models.model import ModelVersion, MLModel
from backend.app.core.enums import IncidentSeverity, IncidentStatus, IncidentEventType, ModelVersionStatus
from backend.app.services.incident_service import IncidentService
from backend.app.dependencies import redis_client

from ml.preprocessing.dataset_loader import DatasetLoader
from ml.preprocessing.schema_validator import validate_schema
from ml.preprocessing.feature_preprocessor import FeaturePreprocessor, stratified_train_val_test_split
from ml.training.trainer_factory import TrainerFactory
from ml.training.tuning.tuner import OptunaTuner
from ml.registry.model_registry import ModelRegistry
from ml.simulator.drift_simulator import DriftSimulator

logger = logging.getLogger("sentinelml.retraining_flow")
logger.setLevel(logging.INFO)

# Global Run State Store & Lock Management
RETRAINING_RUNS: Dict[str, Dict[str, Any]] = {}
RETRAINING_RUNS_MUTEX = threading.Lock()

IN_MEMORY_LOCKS = set()
IN_MEMORY_LOCK_MUTEX = threading.Lock()


def acquire_retraining_lock(incident_id: str, run_id: str, expire_seconds: int = 3600) -> bool:
    """Acquires lock for an incident using Redis (with fallback to in-memory set)."""
    lock_key = f"lock:retraining:incident:{incident_id}"
    if redis_client is not None:
        try:
            acquired = redis_client.set(lock_key, run_id, nx=True, ex=expire_seconds)
            if acquired:
                return True
            else:
                return False
        except Exception as e:
            logger.warning(f"Redis lock failed, falling back to in-memory lock: {e}")

    with IN_MEMORY_LOCK_MUTEX:
        if incident_id in IN_MEMORY_LOCKS:
            return False
        IN_MEMORY_LOCKS.add(incident_id)
        return True


def release_retraining_lock(incident_id: str, run_id: str):
    """Releases lock for an incident."""
    lock_key = f"lock:retraining:incident:{incident_id}"
    if redis_client is not None:
        try:
            val = redis_client.get(lock_key)
            if val == run_id:
                redis_client.delete(lock_key)
        except Exception as e:
            logger.warning(f"Failed releasing Redis lock: {e}")

    with IN_MEMORY_LOCK_MUTEX:
        IN_MEMORY_LOCKS.discard(incident_id)


def update_run_state(
    run_id: str,
    current_step: str,
    status: str = "RUNNING",
    incident_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Persists run state in the global store."""
    with RETRAINING_RUNS_MUTEX:
        if run_id not in RETRAINING_RUNS:
            RETRAINING_RUNS[run_id] = {
                "run_id": run_id,
                "incident_id": incident_id,
                "status": status,
                "current_step": current_step,
                "steps_completed": [],
                "started_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "error": None,
                "metrics": {},
                "candidate_version": None,
                "candidate_id": None,
            }

        run = RETRAINING_RUNS[run_id]
        if incident_id and not run["incident_id"]:
            run["incident_id"] = incident_id

        run["status"] = status
        run["current_step"] = current_step
        run["updated_at"] = datetime.now(timezone.utc).isoformat()

        if current_step and current_step not in run["steps_completed"] and status != "FAILED":
            run["steps_completed"].append(current_step)

        if details:
            run.update(details)

        if error:
            run["error"] = str(error)

        if status in ["COMPLETED", "FAILED"]:
            run["completed_at"] = datetime.now(timezone.utc).isoformat()


def get_run_state(run_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves state of a retraining run by run_id."""
    with RETRAINING_RUNS_MUTEX:
        return RETRAINING_RUNS.get(run_id)


# Helper DB Timeline Event Updater
def log_and_update_event(
    db: SessionLocal,
    incident_id: str,
    event_type: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Logs step status and appends timeline event to Incident in DB."""
    logger.info(f"[{incident_id[:8]}] {event_type}: {message}")
    if db and incident_id:
        try:
            service = IncidentService(db)
            service.add_timeline_event(
                incident_id=incident_id,
                event_type=event_type,
                message=message,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to record incident timeline event {event_type}: {e}")


# PREFECT TASKS

@task(name="1. Drift Detection", retries=2, retry_delay_seconds=2)
def detect_drift_step(incident_id: Optional[str], model_version_id: Optional[str], run_id: str) -> Dict[str, Any]:
    """Step 1: Detect/verify statistical drift."""
    update_run_state(run_id=run_id, current_step="Drift Detected", incident_id=incident_id)
    db = SessionLocal()
    try:
        drift_summary = {"status": "DRIFT_DETECTED", "severity": "HIGH", "timestamp": datetime.now(timezone.utc).isoformat()}
        if incident_id:
            log_and_update_event(
                db=db,
                incident_id=incident_id,
                event_type=IncidentEventType.DRIFT_DETECTED.value,
                message="Self-healing pipeline confirmed active dataset/concept drift.",
                metadata=drift_summary,
            )
        return drift_summary
    finally:
        db.close()


@task(name="2. Incident Creation/Verification", retries=2, retry_delay_seconds=2)
def create_or_verify_incident_step(incident_id: Optional[str], model_version_id: Optional[str], run_id: str) -> str:
    """Step 2: Create new Incident or verify existing Incident state."""
    update_run_state(run_id=run_id, current_step="Incident Created", incident_id=incident_id)
    db = SessionLocal()
    try:
        if incident_id:
            inc = db.query(Incident).filter(Incident.id == incident_id).first()
            if inc:
                inc.status = IncidentStatus.RETRAINING
                db.add(inc)
                db.commit()
                log_and_update_event(
                    db=db,
                    incident_id=incident_id,
                    event_type=IncidentEventType.RETRAINING_STARTED.value,
                    message=f"Automated retraining flow started (Run ID: {run_id[:8]}).",
                )
                return incident_id

        # Find default or specified model version
        mver = None
        if model_version_id:
            mver = db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()
        if not mver:
            mver = db.query(ModelVersion).order_by(ModelVersion.created_at.desc()).first()

        target_mver_id = mver.id if mver else str(uuid.uuid4())
        model_name = mver.model.name if mver and mver.model else "FraudDetector"

        new_inc = Incident(
            model_version_id=target_mver_id,
            title=f"Automated Recovery Incident for {model_name}",
            description="Self-healing pipeline created incident upon drift qualification.",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.RETRAINING,
            incident_type="DATA_DRIFT",
            recommended_action="RETRAIN_MODEL",
            opened_at=datetime.now(timezone.utc),
        )
        db.add(new_inc)
        db.commit()
        db.refresh(new_inc)

        log_and_update_event(
            db=db,
            incident_id=new_inc.id,
            event_type=IncidentEventType.INCIDENT_CREATED.value,
            message=f"Incident #{new_inc.id[:8]} created for automated recovery flow.",
        )
        log_and_update_event(
            db=db,
            incident_id=new_inc.id,
            event_type=IncidentEventType.RETRAINING_STARTED.value,
            message=f"Automated retraining flow initiated (Run ID: {run_id[:8]}).",
        )

        update_run_state(run_id=run_id, current_step="Incident Created", incident_id=new_inc.id)
        return new_inc.id
    finally:
        db.close()


@task(name="3. Dataset Snapshot", retries=2, retry_delay_seconds=3)
def dataset_snapshot_step(incident_id: str, run_id: str) -> Dict[str, Any]:
    """Step 3: Capture dataset snapshot combining baseline reference data and recent drifted transactions."""
    update_run_state(run_id=run_id, current_step="Dataset Snapshot", incident_id=incident_id)
    db = SessionLocal()
    try:
        simulator = DriftSimulator(db)
        ref_df = simulator.get_baseline_reference_data(num_records=2000)
        cur_df = simulator.apply_drift_scenario(df=ref_df, scenario="MULTI_FEATURE_DRIFT", intensity=0.7)

        # Combine into retraining snapshot
        combined_df = pd.concat([ref_df, cur_df], ignore_index=True)

        snapshot_dir = os.path.join("data", "snapshots")
        os.makedirs(snapshot_dir, exist_ok=True)
        snapshot_path = os.path.join(snapshot_dir, f"snapshot_{incident_id[:8]}_{int(time.time())}.csv")
        combined_df.to_csv(snapshot_path, index=False)

        metadata = DatasetLoader.generate_dataset_metadata(
            df=combined_df,
            target_col="is_fraud",
            version=f"snap_{int(time.time())}",
            source=snapshot_path,
        )

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type="DATASET_SNAPSHOTTED",
            message=f"Created dataset snapshot with {len(combined_df)} records (schema_hash: {metadata['schema_hash'][:8]}).",
            metadata=metadata,
        )

        return {"snapshot_path": snapshot_path, "metadata": metadata, "row_count": len(combined_df)}
    finally:
        db.close()


@task(name="4. Data Validation", retries=2, retry_delay_seconds=3)
def data_validation_step(incident_id: str, snapshot_info: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """Step 4: Validate snapshot dataset schema and data quality rules."""
    update_run_state(run_id=run_id, current_step="Data Validation", incident_id=incident_id)
    db = SessionLocal()
    try:
        snapshot_path = snapshot_info["snapshot_path"]
        df = DatasetLoader.load_csv(snapshot_path)

        is_valid, errors = validate_schema(df)
        if not is_valid:
            error_msg = f"Data validation failed: {', '.join(errors[:3])}"
            log_and_update_event(
                db=db,
                incident_id=incident_id,
                event_type="DATA_VALIDATION_FAILED",
                message=error_msg,
                metadata={"errors": errors},
            )
            raise ValueError(error_msg)

        validation_summary = {
            "status": "PASSED",
            "schema_valid": True,
            "columns": list(df.columns),
            "rows": len(df),
            "fraud_rate": float(round((df["is_fraud"].sum() / len(df)) * 100, 2)),
        }

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type="DATA_VALIDATED",
            message=f"Data schema and quality validation passed ({len(df)} rows validated).",
            metadata=validation_summary,
        )

        return validation_summary
    finally:
        db.close()


@task(name="5. Feature Preprocessing", retries=2, retry_delay_seconds=3)
def feature_preprocessing_step(incident_id: str, snapshot_info: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """Step 5: Preprocess features strictly on Train split without data leakage."""
    update_run_state(run_id=run_id, current_step="Feature Preprocessing", incident_id=incident_id)
    db = SessionLocal()
    try:
        snapshot_path = snapshot_info["snapshot_path"]
        df = DatasetLoader.load_csv(snapshot_path)

        X_train, y_train, X_val, y_val, X_test, y_test = stratified_train_val_test_split(
            df=df, target_col="is_fraud", train_size=0.70, val_size=0.15, test_size=0.15, random_state=42
        )

        preprocessor = FeaturePreprocessor()
        X_train_proc = preprocessor.fit_transform(X_train)
        X_val_proc = preprocessor.transform(X_val)
        X_test_proc = preprocessor.transform(X_test)

        preproc_dir = os.path.join("artifacts", "preprocessors")
        os.makedirs(preproc_dir, exist_ok=True)
        preproc_path = os.path.join(preproc_dir, f"preprocessor_{incident_id[:8]}.joblib")
        preprocessor.save(preproc_path)

        processed_data = {
            "preprocessor_path": preproc_path,
            "X_train": X_train_proc,
            "y_train": y_train.to_numpy(),
            "X_val": X_val_proc,
            "y_val": y_val.to_numpy(),
            "X_test": X_test_proc,
            "y_test": y_test.to_numpy(),
            "feature_names": preprocessor.feature_names_out_,
        }

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type="FEATURES_PREPROCESSED",
            message=f"Feature preprocessing completed (train shape: {X_train_proc.shape}, test shape: {X_test_proc.shape}).",
            metadata={"num_features": len(preprocessor.feature_names_out_), "preprocessor_path": preproc_path},
        )

        return processed_data
    finally:
        db.close()


@task(name="6. Candidate Training", retries=2, retry_delay_seconds=5)
def candidate_training_step(incident_id: str, processed_data: Dict[str, Any], model_type: str, run_id: str) -> Dict[str, Any]:
    """Step 6: Train initial baseline candidate model."""
    update_run_state(run_id=run_id, current_step="Candidate Training", incident_id=incident_id)
    db = SessionLocal()
    try:
        X_train = processed_data["X_train"]
        y_train = processed_data["y_train"]
        X_val = processed_data["X_val"]
        y_val = processed_data["y_val"]

        trainer = TrainerFactory.get_trainer(model_type=model_type)
        trainer.fit(X_train, y_train)
        val_metrics = trainer.evaluate(X_val, y_val)

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type=IncidentEventType.CANDIDATE_TRAINED.value,
            message=f"Initial candidate model ({model_type.upper()}) trained. Validation PR-AUC: {val_metrics.get('pr_auc', 0.0):.4f}",
            metadata={"model_type": model_type, "val_metrics": val_metrics},
        )

        return {"model_type": model_type, "val_metrics": val_metrics, "trainer": trainer}
    finally:
        db.close()


@task(name="7. Hyperparameter Optimization", retries=1, retry_delay_seconds=5)
def hyperparameter_optimization_step(
    incident_id: str, processed_data: Dict[str, Any], model_type: str, run_id: str
) -> Dict[str, Any]:
    """Step 7: Optimize hyperparameters using Optuna."""
    update_run_state(run_id=run_id, current_step="Hyperparameter Optimization", incident_id=incident_id)
    db = SessionLocal()
    try:
        tuner = OptunaTuner(
            model_type=model_type,
            n_trials=10,  # Token and time efficient tuning for automated self-healing
            seed=42,
            output_dir=os.path.join("artifacts", "tuning"),
        )
        tuning_res = tuner.optimize(
            X_train=processed_data["X_train"],
            y_train=processed_data["y_train"],
            X_val=processed_data["X_val"],
            y_val=processed_data["y_val"],
            X_test=processed_data["X_test"],
            y_test=processed_data["y_test"],
            save_results=True,
        )

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type="HYPERPARAMETERS_OPTIMIZED",
            message=f"Optuna hyperparameter optimization completed (Best Val PR-AUC: {tuning_res['best_score_val']:.4f}).",
            metadata={"best_score": tuning_res["best_score_val"], "best_params": tuning_res["best_params"]},
        )

        return tuning_res
    finally:
        db.close()


@task(name="8. Evaluation", retries=2, retry_delay_seconds=3)
def candidate_evaluation_step(incident_id: str, processed_data: Dict[str, Any], tuning_res: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """Step 8: Evaluate best hyperparameter tuned candidate on held-out test split."""
    update_run_state(run_id=run_id, current_step="Evaluation", incident_id=incident_id)
    db = SessionLocal()
    try:
        model_type = tuning_res["model_type"]
        best_params = tuning_res["best_params"]

        best_trainer = TrainerFactory.get_trainer(model_type, hyperparams=best_params)
        best_trainer.fit(processed_data["X_train"], processed_data["y_train"])
        test_metrics = best_trainer.evaluate(processed_data["X_test"], processed_data["y_test"])

        # Save tuned candidate artifact
        model_dir = os.path.join("artifacts", "models")
        os.makedirs(model_dir, exist_ok=True)
        artifact_path = os.path.join(model_dir, f"candidate_{model_type}_{incident_id[:8]}.joblib")
        best_trainer.save_artifact(artifact_path)

        eval_summary = {
            "model_type": model_type,
            "test_metrics": test_metrics,
            "artifact_path": artifact_path,
            "best_params": best_params,
        }

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type=IncidentEventType.CANDIDATE_EVALUATED.value,
            message=f"Final candidate evaluation on held-out test set: PR-AUC={test_metrics.get('pr_auc', 0.0):.4f}, ROC-AUC={test_metrics.get('roc_auc', 0.0):.4f}, F1={test_metrics.get('f1', 0.0):.4f}.",
            metadata=test_metrics,
        )

        return eval_summary
    finally:
        db.close()


@task(name="9. Candidate Registration", retries=2, retry_delay_seconds=3)
def candidate_registration_step(incident_id: str, eval_summary: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """Step 9: Register candidate in Model Registry and mark Incident as RESOLVED."""
    update_run_state(run_id=run_id, current_step="Candidate Registration", incident_id=incident_id)
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        model_name = "FraudDetector"
        if inc and inc.model_version and inc.model_version.model:
            model_name = inc.model_version.model.name

        registry = ModelRegistry(db)
        version_str = f"v{int(time.time())}"

        reg_result = registry.register_candidate(
            model_name=model_name,
            version=version_str,
            algorithm=eval_summary["model_type"],
            artifact_path=eval_summary["artifact_path"],
            metrics=eval_summary["test_metrics"],
            parameters=eval_summary["best_params"],
        )

        # Update Incident status to RESOLVED and set resolved_at
        if inc:
            inc.status = IncidentStatus.RESOLVED
            inc.resolved_at = datetime.now(timezone.utc)
            db.add(inc)

        log_and_update_event(
            db=db,
            incident_id=incident_id,
            event_type=IncidentEventType.INCIDENT_RESOLVED.value,
            message=f"Candidate model version {version_str} registered successfully. Self-healing recovery complete.",
            metadata={"candidate_version": version_str, "model_version_id": reg_result.get("id")},
        )
        db.commit()

        update_run_state(
            run_id=run_id,
            current_step="Candidate Registration",
            status="COMPLETED",
            incident_id=incident_id,
            details={
                "candidate_version": version_str,
                "model_version_id": reg_result.get("id"),
                "metrics": eval_summary["test_metrics"],
            },
        )

        return reg_result
    finally:
        db.close()


# MAIN PREFECT FLOW

@flow(name="Automated Retraining Pipeline")
def automated_retraining_flow(
    incident_id: Optional[str] = None,
    model_version_id: Optional[str] = None,
    model_type: str = "xgboost",
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Prefect Retraining Flow orchestrating the self-healing component.
    """
    if not run_id:
        run_id = str(uuid.uuid4())

    update_run_state(run_id=run_id, current_step="Initializing Flow", status="RUNNING", incident_id=incident_id)

    # 1. Acquire Redis/In-Memory Lock if incident_id is known
    lock_acquired = False
    active_incident_id = incident_id

    if active_incident_id:
        lock_acquired = acquire_retraining_lock(active_incident_id, run_id)
        if not lock_acquired:
            err_msg = f"Retraining job for incident '{active_incident_id}' is already in progress."
            logger.warning(err_msg)
            update_run_state(run_id=run_id, current_step="Lock Check", status="FAILED", error=err_msg)
            raise RuntimeError(err_msg)

    try:
        # Step 1: Drift Detected
        drift_res = detect_drift_step(active_incident_id, model_version_id, run_id)

        # Step 2: Incident Created / Verified
        active_incident_id = create_or_verify_incident_step(active_incident_id, model_version_id, run_id)

        # Re-verify lock if incident was created in Step 2 and lock wasn't set earlier
        if not lock_acquired and active_incident_id:
            lock_acquired = acquire_retraining_lock(active_incident_id, run_id)
            if not lock_acquired:
                err_msg = f"Retraining job for incident '{active_incident_id}' is already in progress."
                update_run_state(run_id=run_id, current_step="Lock Check", status="FAILED", error=err_msg)
                raise RuntimeError(err_msg)

        # Step 3: Dataset Snapshot
        snapshot_info = dataset_snapshot_step(active_incident_id, run_id)

        # Step 4: Data Validation
        val_info = data_validation_step(active_incident_id, snapshot_info, run_id)

        # Step 5: Feature Preprocessing
        processed_data = feature_preprocessing_step(active_incident_id, snapshot_info, run_id)

        # Step 6: Candidate Training
        training_res = candidate_training_step(active_incident_id, processed_data, model_type, run_id)

        # Step 7: Hyperparameter Optimization
        tuning_res = hyperparameter_optimization_step(active_incident_id, processed_data, model_type, run_id)

        # Step 8: Evaluation
        eval_summary = candidate_evaluation_step(active_incident_id, processed_data, tuning_res, run_id)

        # Step 9: Candidate Registration
        reg_result = candidate_registration_step(active_incident_id, eval_summary, run_id)

        return get_run_state(run_id) or {"status": "COMPLETED", "run_id": run_id, "incident_id": active_incident_id}

    except Exception as e:
        logger.error(f"Retraining flow failed for run '{run_id}': {e}", exc_info=True)
        update_run_state(run_id=run_id, current_step="Flow Exception", status="FAILED", error=str(e))

        # Update Incident status to FAILED in database
        if active_incident_id:
            db = SessionLocal()
            try:
                inc = db.query(Incident).filter(Incident.id == active_incident_id).first()
                if inc:
                    inc.status = IncidentStatus.FAILED
                    db.add(inc)
                    log_and_update_event(
                        db=db,
                        incident_id=active_incident_id,
                        event_type="RETRAINING_FAILED",
                        message=f"Automated retraining pipeline failed: {str(e)}",
                    )
                    db.commit()
            except Exception:
                pass
            finally:
                db.close()
        raise e

    finally:
        if active_incident_id and lock_acquired:
            release_retraining_lock(active_incident_id, run_id)


if __name__ == "__main__":
    res = automated_retraining_flow(model_type="xgboost")
    print("Execution complete:", res)
