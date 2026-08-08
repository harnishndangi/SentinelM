from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.repositories.model_repository import MLModelRepository, ModelVersionRepository, ModelMetricRepository
from backend.app.models.model import MLModel, ModelVersion, ModelMetric
from backend.app.core.enums import ModelVersionStatus


class ModelService:
    def __init__(self, db: Session):
        self.db = db
        self.model_repo = MLModelRepository(db)
        self.version_repo = ModelVersionRepository(db)
        self.metric_repo = ModelMetricRepository(db)

        from ml.registry.model_registry import ModelRegistry
        self.registry = ModelRegistry(db)

    def create_model(self, name: str, description: Optional[str] = None, framework: Optional[str] = None, task_type: Optional[str] = None) -> MLModel:
        existing = self.model_repo.get_by_name(name)
        if existing:
            return existing
        return self.model_repo.create({
            "name": name,
            "description": description,
            "framework": framework,
            "task_type": task_type,
        })

    def create_model_version(
        self,
        model_id: str,
        version: str,
        status: ModelVersionStatus = ModelVersionStatus.TRAINING,
        artifact_uri: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ModelVersion:
        existing = self.version_repo.get_by_model_and_version(model_id, version)
        if existing:
            return existing
        return self.version_repo.create({
            "model_id": model_id,
            "version": version,
            "status": status,
            "artifact_uri": artifact_uri,
            "parameters": parameters,
        })

    def add_metric(self, model_version_id: str, metric_name: str, metric_value: float, split: str = "test") -> ModelMetric:
        return self.metric_repo.create({
            "model_version_id": model_version_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "split": split,
        })

    def get_model_details(self, name: str) -> Optional[Dict[str, Any]]:
        model = self.model_repo.get_by_name(name)
        if not model:
            return None
        
        prod_version = self.version_repo.get_production_version(model.id)
        metrics = []
        if prod_version:
            metric_objs = self.metric_repo.get_metrics_for_version(prod_version.id)
            metrics = [{"name": m.metric_name, "value": m.metric_value, "split": m.split} for m in metric_objs]

        return {
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "framework": model.framework,
            "task_type": model.task_type,
            "production_version": prod_version.version if prod_version else None,
            "metrics": metrics,
        }
