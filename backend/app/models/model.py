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
    parameters = Column(JSON, nullable=True)

    # Relationships
    model = relationship("MLModel", back_populates="versions")
    metrics = relationship("ModelMetric", back_populates="model_version", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="model_version", cascade="all, delete-orphan")
    drift_events = relationship("DriftEvent", back_populates="model_version", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="model_version", cascade="all, delete-orphan")
    training_runs = relationship("TrainingRun", back_populates="model_version", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="model_version", cascade="all, delete-orphan")


class ModelMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "model_metrics"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    split = Column(String(50), default="test", nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="metrics")
