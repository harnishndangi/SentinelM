from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class Dataset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "datasets"

    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    data_type = Column(String(100), nullable=True)  # e.g., tabular, image, text

    # Relationships
    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    version = Column(String(50), nullable=False)
    num_rows = Column(Integer, nullable=True)
    num_features = Column(Integer, nullable=True)
    storage_path = Column(String(512), nullable=True)
    checksum = Column(String(64), nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="versions")
    drift_events = relationship("DriftEvent", back_populates="dataset_version")
    training_runs = relationship("TrainingRun", back_populates="dataset_version")
