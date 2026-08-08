from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.dependencies import get_redis_client


class HealthService:
    def __init__(self, db: Session):
        self.db = db

    def check_db_connection(self) -> bool:
        """Ping database to confirm connectivity."""
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def check_redis_connection(self) -> bool:
        """Ping Redis instance to confirm connectivity."""
        try:
            client = get_redis_client()
            if client is not None:
                return client.ping()
            return False
        except Exception:
            return False

    def get_full_health_status(self) -> Dict[str, Any]:
        db_healthy = self.check_db_connection()
        redis_healthy = self.check_redis_connection()

        overall_status = "healthy" if db_healthy else "degraded"

        return {
            "status": overall_status,
            "service": "sentinelml-api",
            "version": "1.0.0",
            "dependencies": {
                "database": "connected" if db_healthy else "disconnected",
                "redis": "connected" if redis_healthy else "disconnected",
            },
        }
