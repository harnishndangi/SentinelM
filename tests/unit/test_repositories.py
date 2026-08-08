import uuid
from backend.app.database import SessionLocal
from backend.app.services.model_service import ModelService
from backend.app.core.enums import ModelVersionStatus


def test_model_service_and_repositories(client):
    db = SessionLocal()
    try:
        model_name = f"RiskScorer-{uuid.uuid4().hex[:8]}"
        service = ModelService(db)
        model = service.create_model(
            name=model_name,
            description="Credit risk scoring model",
            framework="xgboost",
            task_type="classification",
        )
        assert model.name == model_name

        version = service.create_model_version(
            model_id=model.id,
            version="1.0",
            status=ModelVersionStatus.PRODUCTION,
        )
        assert version.version == "1.0"
        assert version.status == ModelVersionStatus.PRODUCTION

        metric = service.add_metric(
            model_version_id=version.id,
            metric_name="precision",
            metric_value=0.95,
            split="test",
        )
        assert metric.metric_name == "precision"
        assert metric.metric_value == 0.95

        details = service.get_model_details(model_name)
        assert details is not None
        assert details["name"] == model_name
        assert details["production_version"] == "1.0"
        assert len(details["metrics"]) == 1
        assert details["metrics"][0]["name"] == "precision"
        assert details["metrics"][0]["value"] == 0.95
    finally:
        db.close()
