from sqlalchemy import Column, String, Enum as SQLEnum, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin, utc_now
from backend.app.core.enums import AlertStatus, AlertSeverity


class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"

    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.TRIGGERED, nullable=False, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="alerts")


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
