from sqlalchemy import Column, String, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class Prediction(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "predictions"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    prediction_id = Column(String(255), index=True, nullable=False)
    input_features = Column(JSON, nullable=True)
    output_prediction = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    actual_label = Column(Float, nullable=True)
    label_received_at = Column(JSON, nullable=True)
    error_val = Column(Float, nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="predictions")
    feature_logs = relationship("FeatureLog", back_populates="prediction", cascade="all, delete-orphan")
    ground_truth_logs = relationship("GroundTruthLog", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_prediction_model_created", "model_version_id", "created_at"),
    )


class FeatureLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "feature_logs"

    prediction_id = Column(String(36), ForeignKey("predictions.id", ondelete="CASCADE"), index=True, nullable=False)
    feature_name = Column(String(255), index=True, nullable=False)
    feature_value = Column(Float, nullable=True)

    # Relationships
    prediction = relationship("Prediction", back_populates="feature_logs")
