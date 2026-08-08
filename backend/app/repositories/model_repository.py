from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.model import MLModel, ModelVersion, ModelMetric
from backend.app.core.enums import ModelVersionStatus
from backend.app.repositories.base import BaseRepository


class MLModelRepository(BaseRepository[MLModel]):
    def __init__(self, db: Session):
        super().__init__(MLModel, db)

    def get_by_name(self, name: str) -> Optional[MLModel]:
        return self.db.query(MLModel).filter(MLModel.name == name).first()


class ModelVersionRepository(BaseRepository[ModelVersion]):
    def __init__(self, db: Session):
        super().__init__(ModelVersion, db)

    def get_by_model_and_version(self, model_id: str, version: str) -> Optional[ModelVersion]:
        return (
            self.db.query(ModelVersion)
            .filter(ModelVersion.model_id == model_id, ModelVersion.version == version)
            .first()
        )

    def get_production_version(self, model_id: str) -> Optional[ModelVersion]:
        return (
            self.db.query(ModelVersion)
            .filter(
                ModelVersion.model_id == model_id,
                ModelVersion.status == ModelVersionStatus.PRODUCTION,
            )
            .order_by(ModelVersion.created_at.desc())
            .first()
        )


class ModelMetricRepository(BaseRepository[ModelMetric]):
    def __init__(self, db: Session):
        super().__init__(ModelMetric, db)

    def get_metrics_for_version(self, model_version_id: str) -> List[ModelMetric]:
        return (
            self.db.query(ModelMetric)
            .filter(ModelMetric.model_version_id == model_version_id)
            .all()
        )
