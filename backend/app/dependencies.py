from typing import Generator
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.config import settings

try:
    import redis

    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


def get_redis_client():
    """Dependency generator for Redis connection."""
    return redis_client
