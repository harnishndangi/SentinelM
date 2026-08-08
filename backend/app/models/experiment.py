from sqlalchemy import Column, String, Float, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class TrainingRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "training_runs"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    logs_path = Column(String(512), nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="training_runs")
    dataset_version = relationship("DatasetVersion", back_populates="training_runs")


class Experiment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "experiments"

    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    metrics = relationship("ExperimentMetric", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "experiment_metrics"

    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    step = Column(Integer, default=0, nullable=False)
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(Float, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="metrics")
