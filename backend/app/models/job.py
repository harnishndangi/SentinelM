import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, JSON, DateTime
from backend.app.database import Base
from backend.app.models.base import UUIDMixin, TimestampMixin


class AsyncJob(Base, UUIDMixin, TimestampMixin):
    """
    Persistent record for background Celery tasks.
    Tracks execution status, inputs, outputs, errors, and real-time progress.
    """
    __tablename__ = "async_jobs"

    job_id = Column(String(255), unique=True, index=True, nullable=False)
    task_type = Column(String(100), index=True, nullable=False)
    status = Column(String(50), default="PENDING", index=True, nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    traceback = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
