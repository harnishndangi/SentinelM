from sqlalchemy import Column, String, Enum as SQLEnum, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now
from backend.app.core.enums import IncidentSeverity, IncidentStatus


class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"

    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(IncidentSeverity), default=IncidentSeverity.MEDIUM, nullable=False, index=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.OPEN, nullable=False, index=True)
    opened_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    model_version = relationship("ModelVersion", back_populates="incidents")
    events = relationship("IncidentEvent", back_populates="incident", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="incident", cascade="all, delete-orphan")


class IncidentEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incident_events"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="events")
