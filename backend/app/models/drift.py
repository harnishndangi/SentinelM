from sqlalchemy import Column, String, Float, Boolean, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now
from backend.app.core.enums import DriftType


class DriftEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drift_events"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_version_id = Column(String(36), ForeignKey("dataset_versions.id", ondelete="SET NULL"), nullable=True)
    drift_type = Column(SQLEnum(DriftType), default=DriftType.DATA_DRIFT, nullable=False, index=True)
    overall_status = Column(String(50), default="NONE", nullable=False)
    is_actionable = Column(Boolean, default=False, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="drift_events")
    dataset_version = relationship("DatasetVersion", back_populates="drift_events")
    drift_scores = relationship("DriftScore", back_populates="drift_event", cascade="all, delete-orphan")


class DriftScore(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drift_scores"

    drift_event_id = Column(String(36), ForeignKey("drift_events.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_name = Column(String(255), index=True, nullable=False)
    method = Column(String(100), nullable=False)  # KS, PSI, Wasserstein, Chi-Square, JS
    p_value = Column(Float, nullable=True)
    drift_score = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(50), default="NONE", nullable=False)
    is_drifted = Column(Boolean, default=False, nullable=False)

    # Relationships
    drift_event = relationship("DriftEvent", back_populates="drift_scores")
