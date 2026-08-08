from sqlalchemy import Column, String, Float, Integer, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now
from backend.app.core.enums import DeploymentStatus


class Deployment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "deployments"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    environment = Column(String(50), default="production", nullable=False, index=True)
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False, index=True)
    endpoint_url = Column(String(512), nullable=True)
    deployed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    terminated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="deployments")
    metrics = relationship("DeploymentMetric", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "deployment_metrics"

    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="CASCADE"), index=True, nullable=False)
    request_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    latency_p95_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    deployment = relationship("Deployment", back_populates="metrics")
