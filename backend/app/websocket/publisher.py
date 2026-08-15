import json
from typing import Union, Dict, Any
from pydantic import BaseModel
import redis
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.websocket.events import EventType, WebSocketEvent


def get_redis_sync_client() -> redis.Redis:
    """Returns synchronous Redis client instance."""
    if settings.REDIS_PASSWORD:
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
        )
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )


def publish_websocket_event(event_type: EventType, payload: Union[BaseModel, Dict[str, Any]]):
    """
    Publishes a strongly typed WebSocket event payload to the Redis Pub/Sub channel.
    Can be called from Celery background tasks or FastAPI API endpoints.
    """
    try:
        raw_payload = payload.model_dump() if isinstance(payload, BaseModel) else payload
        event = WebSocketEvent(
            event_type=event_type,
            payload=raw_payload,
        )
        event_json = event.model_dump_json()

        r = get_redis_sync_client()
        r.publish(settings.WS_REDIS_CHANNEL, event_json)
        logger.info("Published WebSocket event to Redis Pub/Sub", event_type=event_type.value)
    except Exception as e:
        logger.warning(
            "Could not publish WebSocket event to Redis (Redis might be offline)",
            event_type=event_type.value if hasattr(event_type, "value") else str(event_type),
            error=str(e),
        )
