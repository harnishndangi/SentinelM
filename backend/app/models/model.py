from sqlalchemy import Column, String, Float, Enum as SQLEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now
from backend.app.core.enums import ModelVersionStatus


class MLModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ml_models"

    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    framework = Column(String(100), nullable=True)  # e.g., scikit-learn, xgboost, PyTorch
    task_type = Column(String(100), nullable=True)  # e.g., classification, regression
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="models")
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")


class ModelVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_versions"

    model_id = Column(String(36), ForeignKey("ml_models.id", ondelete="CASCADE"), index=True, nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(SQLEnum(ModelVersionStatus), default=ModelVersionStatus.TRAINING, nullable=False, index=True)
    artifact_uri = Column(String(512), nullable=True)
    artifact_path = Column(String(512), nullable=True)
    algorithm = Column(String(100), nullable=True)
    dataset_version = Column(String(50), nullable=True)
    training_run_id = Column(String(255), nullable=True)
    parameters = Column(JSON, nullable=True)
    metrics_summary = Column(JSON, nullable=True)

    # Relationships
    model = relationship("MLModel", back_populates="versions")
    metrics = relationship("ModelMetric", back_populates="model_version", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="model_version", cascade="all, delete-orphan")
    drift_events = relationship("DriftEvent", back_populates="model_version", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="model_version", cascade="all, delete-orphan")
    training_runs = relationship("TrainingRun", back_populates="model_version", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="model_version", cascade="all, delete-orphan")

    @property
    def metrics_dict(self) -> dict:
        """Returns dictionary of metrics combined from metrics_summary and ModelMetric relationship."""
        result = {}
        if self.metrics_summary and isinstance(self.metrics_summary, dict):
            result.update(self.metrics_summary)
        for m in self.metrics:
            result[m.metric_name] = m.metric_value
        return result

    def to_registry_dict(self) -> dict:
        """Formats model version into standard SentinelML Model Registry dict representation."""
        effective_artifact_path = self.artifact_path or self.artifact_uri
        return {
            "id": self.id,
            "version_id": self.id,
            "model_id": self.model_id,
            "model_name": self.model.name if self.model else None,
            "version": self.version,
            "algorithm": self.algorithm,
            "artifact_path": effective_artifact_path,
            "dataset_version": self.dataset_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metrics": self.metrics_dict,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "training_run_id": self.training_run_id,
        }


class ModelMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_metrics"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    split = Column(String(50), default="test", nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="metrics")
