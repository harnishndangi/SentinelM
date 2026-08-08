from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="engineer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    models = relationship("MLModel", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")
