import uuid
import pytest
from backend.app.models.model import MLModel, ModelVersion, ModelMetric
from backend.app.core.enums import ModelVersionStatus


def test_create_model_and_version(client):
    from backend.app.database import SessionLocal

    db = SessionLocal()
    try:
        model_name = f"TestModel-{uuid.uuid4().hex[:8]}"
        model = MLModel(
            name=model_name,
            description="Test description",
            framework="PyTorch",
            task_type="classification",
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        assert model.id is not None
        assert model.name == model_name

        version = ModelVersion(
            model_id=model.id,
            version="1.0.0",
            status=ModelVersionStatus.PRODUCTION,
        )
        db.add(version)
        db.commit()
        db.refresh(version)

        assert version.id is not None
        assert version.status == ModelVersionStatus.PRODUCTION
    finally:
        db.close()
