"""
SentinelML Model Registry Service.

Connects MLflow model artifacts with PostgreSQL / SQLAlchemy ModelVersion records.
Manages model lifecycle transitions:
TRAINING -> CANDIDATE -> STAGING -> PRODUCTION -> ARCHIVED.

Enforces strict governance:
- Only one model version can be active in PRODUCTION for a given model.
- Every lifecycle change generates an AuditLog entry.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session

import mlflow
from backend.app.models.model import MLModel, ModelVersion, ModelMetric
from backend.app.models.audit import AuditLog
from backend.app.core.enums import ModelVersionStatus
from backend.app.repositories.model_repository import MLModelRepository, ModelVersionRepository, ModelMetricRepository


class ModelRegistry:
    """
    Central Model Registry abstraction for SentinelML.
    
    Usage:
        registry = ModelRegistry(db_session)
        candidate = registry.register_candidate(
            model_name="SentinelML-FraudDetection",
            version="v1.0.0",
            algorithm="XGBoost",
            training_run_id="mlflow_run_12345",
        )
        prod = registry.promote_model(
            model_name="SentinelML-FraudDetection",
            version="v1.0.0",
            target_status=ModelVersionStatus.PRODUCTION,
        )
    """

    def __init__(self, db: Session):
        self.db = db
        self.model_repo = MLModelRepository(db)
        self.version_repo = ModelVersionRepository(db)
        self.metric_repo = ModelMetricRepository(db)

    def _log_audit_event(
        self,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> AuditLog:
        """Records an immutable AuditLog entry in PostgreSQL."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="MODEL_VERSION",
            resource_id=resource_id,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        return audit_entry

    def _get_or_create_model(self, model_name: str, algorithm: Optional[str] = None) -> MLModel:
        """Finds or creates parent MLModel entity."""
        model = self.model_repo.get_by_name(model_name)
        if not model:
            model = self.model_repo.create({
                "name": model_name,
                "description": f"SentinelML model container for {model_name}",
                "framework": algorithm or "scikit-learn/xgboost",
                "task_type": "classification",
            })
        return model

    def register_candidate(
        self,
        model_name: str,
        version: str,
        algorithm: Optional[str] = None,
        artifact_path: Optional[str] = None,
        dataset_version: Optional[str] = "v1.0.0",
        metrics: Optional[Dict[str, float]] = None,
        training_run_id: Optional[str] = None,
        user_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registers a new model version candidate in PostgreSQL, linking MLflow artifacts.
        
        Lifecycle state set to: CANDIDATE.
        Creates an AuditLog entry.
        """
        model = self._get_or_create_model(model_name, algorithm=algorithm)
        
        # Check if version already exists
        existing_version = self.version_repo.get_by_model_and_version(model.id, version)
        if existing_version:
            return existing_version.to_registry_dict()

        # If training_run_id is provided, pull missing metadata/artifacts from MLflow
        extracted_metrics = metrics or {}
        extracted_artifact_path = artifact_path
        extracted_algorithm = algorithm
        extracted_dataset_version = dataset_version

        if training_run_id and (not extracted_metrics or not extracted_artifact_path):
            try:
                client = mlflow.tracking.MlflowClient()
                run = client.get_run(training_run_id)
                if run:
                    if not extracted_metrics:
                        extracted_metrics = {k: float(v) for k, v in run.data.metrics.items()}
                    if not extracted_artifact_path:
                        extracted_artifact_path = run.info.artifact_uri
                    if not extracted_algorithm:
                        extracted_algorithm = run.data.tags.get("model_name", "Unknown")
                    if run.data.tags.get("dataset_version"):
                        extracted_dataset_version = run.data.tags.get("dataset_version")
            except Exception:
                pass

        # Create ModelVersion database record
        version_obj = self.version_repo.create({
            "model_id": model.id,
            "version": version,
            "status": ModelVersionStatus.CANDIDATE,
            "artifact_path": extracted_artifact_path,
            "artifact_uri": extracted_artifact_path,
            "algorithm": extracted_algorithm or "Unknown",
            "dataset_version": extracted_dataset_version or "v1.0.0",
            "training_run_id": training_run_id,
            "parameters": parameters or {},
            "metrics_summary": extracted_metrics,
        })

        # Save individual metrics into ModelMetric table
        for metric_name, metric_val in extracted_metrics.items():
            if isinstance(metric_val, (int, float)):
                self.metric_repo.create({
                    "model_version_id": version_obj.id,
                    "metric_name": metric_name,
                    "metric_value": float(metric_val),
                    "split": "test",
                })

        # Generate AuditLog
        self._log_audit_event(
            action="REGISTER_CANDIDATE",
            resource_id=version_obj.id,
            details={
                "model_name": model_name,
                "version": version,
                "status": ModelVersionStatus.CANDIDATE.value,
                "algorithm": extracted_algorithm,
                "training_run_id": training_run_id,
                "artifact_path": extracted_artifact_path,
            },
            user_id=user_id,
        )

        return version_obj.to_registry_dict()

    def get_production_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the active PRODUCTION model version for a given model.
        Returns None if no version is in production.
        """
        model = self.model_repo.get_by_name(model_name)
        if not model:
            return None
        
        prod_version = self.version_repo.get_production_version(model.id)
        if not prod_version:
            return None
        
        return prod_version.to_registry_dict()

    def get_model_version(self, model_name: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves model version dict representation by model_name and version string.
        """
        model = self.model_repo.get_by_name(model_name)
        if not model:
            return None
        ver_obj = self.version_repo.get_by_model_and_version(model.id, version)
        if not ver_obj:
            return None
        return ver_obj.to_registry_dict()

    def get_candidate_models(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all model versions with status CANDIDATE.
        Optionally filtered by model_name.
        """
        model_id = None
        if model_name:
            model = self.model_repo.get_by_name(model_name)
            if not model:
                return []
            model_id = model.id

        candidates = self.version_repo.get_versions_by_status(
            model_id=model_id,
            status=ModelVersionStatus.CANDIDATE,
        )
        return [v.to_registry_dict() for v in candidates]

    def promote_model(
        self,
        model_name: str,
        version: str,
        target_status: Union[str, ModelVersionStatus] = ModelVersionStatus.PRODUCTION,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Promotes a model version to target status (STAGING or PRODUCTION).
        
        Governance Rule:
        - Only ONE active version can be in PRODUCTION for a model.
        - When promoting a new version to PRODUCTION, the existing active production
          version is automatically demoted to STAGING.
          
        Creates an AuditLog entry.
        """
        model = self.model_repo.get_by_name(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found in registry.")

        target_ver_obj = self.version_repo.get_by_model_and_version(model.id, version)
        if not target_ver_obj:
            raise ValueError(f"Version '{version}' for model '{model_name}' not found.")

        # Normalize target status enum
        if isinstance(target_status, str):
            target_status_enum = ModelVersionStatus(target_status.upper())
        else:
            target_status_enum = target_status

        previous_status = target_ver_obj.status.value if hasattr(target_ver_obj.status, "value") else str(target_ver_obj.status)

        # Enforce single active PRODUCTION version rule
        demoted_version = None
        if target_status_enum == ModelVersionStatus.PRODUCTION:
            current_prod = self.version_repo.get_production_version(model.id)
            if current_prod and current_prod.id != target_ver_obj.id:
                current_prod.status = ModelVersionStatus.STAGING
                self.db.add(current_prod)
                demoted_version = current_prod.version
                
                # Log audit event for demoted version
                self._log_audit_event(
                    action="DEMOTE_PRODUCTION_MODEL",
                    resource_id=current_prod.id,
                    details={
                        "model_name": model_name,
                        "version": current_prod.version,
                        "previous_status": ModelVersionStatus.PRODUCTION.value,
                        "new_status": ModelVersionStatus.STAGING.value,
                        "reason": f"Replaced by active production version {version}",
                    },
                    user_id=user_id,
                )

        # Update target version status
        target_ver_obj.status = target_status_enum
        self.db.add(target_ver_obj)
        self.db.commit()
        self.db.refresh(target_ver_obj)

        # Log promotion AuditLog
        self._log_audit_event(
            action="PROMOTE_MODEL",
            resource_id=target_ver_obj.id,
            details={
                "model_name": model_name,
                "version": version,
                "previous_status": previous_status,
                "new_status": target_status_enum.value,
                "demoted_previous_production_version": demoted_version,
            },
            user_id=user_id,
        )

        return target_ver_obj.to_registry_dict()

    def archive_model(
        self,
        model_name: str,
        version: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Archives a model version (transitions status to ARCHIVED).
        Creates an AuditLog entry.
        """
        model = self.model_repo.get_by_name(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found.")

        version_obj = self.version_repo.get_by_model_and_version(model.id, version)
        if not version_obj:
            raise ValueError(f"Version '{version}' for model '{model_name}' not found.")

        previous_status = version_obj.status.value if hasattr(version_obj.status, "value") else str(version_obj.status)

        version_obj.status = ModelVersionStatus.ARCHIVED
        self.db.add(version_obj)
        self.db.commit()
        self.db.refresh(version_obj)

        # Log archive AuditLog
        self._log_audit_event(
            action="ARCHIVE_MODEL",
            resource_id=version_obj.id,
            details={
                "model_name": model_name,
                "version": version,
                "previous_status": previous_status,
                "new_status": ModelVersionStatus.ARCHIVED.value,
            },
            user_id=user_id,
        )

        return version_obj.to_registry_dict()

    def rollback_model(
        self,
        model_name: str,
        target_version: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rolls back the current production model to a target version or the most recently
        available non-production version (e.g. previous production version in STAGING).
        
        Creates an AuditLog entry.
        """
        model = self.model_repo.get_by_name(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found.")

        current_prod = self.version_repo.get_production_version(model.id)
        if not current_prod:
            raise ValueError(f"No current PRODUCTION version found for model '{model_name}' to rollback from.")

        rollback_ver_obj = None
        if target_version:
            rollback_ver_obj = self.version_repo.get_by_model_and_version(model.id, target_version)
            if not rollback_ver_obj:
                raise ValueError(f"Target rollback version '{target_version}' for model '{model_name}' not found.")
        else:
            # Find the most recently created candidate/staging version that is not current production
            all_versions = (
                self.db.query(ModelVersion)
                .filter(ModelVersion.model_id == model.id, ModelVersion.id != current_prod.id)
                .order_by(ModelVersion.created_at.desc())
                .all()
            )
            if not all_versions:
                raise ValueError(f"No prior model version available for rollback in model '{model_name}'.")
            rollback_ver_obj = all_versions[0]

        # Perform rollback swap:
        # Demote current production version to STAGING
        current_prod.status = ModelVersionStatus.STAGING
        self.db.add(current_prod)

        # Promote rollback target version to PRODUCTION
        rollback_ver_obj.status = ModelVersionStatus.PRODUCTION
        self.db.add(rollback_ver_obj)

        self.db.commit()
        self.db.refresh(rollback_ver_obj)
        self.db.refresh(current_prod)

        # Log rollback AuditLog
        self._log_audit_event(
            action="ROLLBACK_MODEL",
            resource_id=rollback_ver_obj.id,
            details={
                "model_name": model_name,
                "demoted_version": current_prod.version,
                "promoted_version": rollback_ver_obj.version,
                "new_status": ModelVersionStatus.PRODUCTION.value,
            },
            user_id=user_id,
        )

        return rollback_ver_obj.to_registry_dict()
