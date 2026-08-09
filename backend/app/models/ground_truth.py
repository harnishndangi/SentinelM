"""
GroundTruthLog SQLAlchemy Model for Delayed Label Feedback.
"""
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now


class GroundTruthLog(Base, UUIDMixin, TimestampMixin):
    """
    GroundTruthLog stores delayed ground truth outcome feedback (e.g. chargeback notifications,
    manual fraud investigation labels) associated with past predictions.
    """
    __tablename__ = "ground_truth_logs"

    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), index=True, nullable=False)
    actual_label = Column(Float, nullable=False)
    feedback_source = Column(String(100), default="manual_review", nullable=False)
    received_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    prediction = relationship("Prediction", back_populates="ground_truth_logs")
