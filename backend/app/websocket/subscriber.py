import asyncio
import json
import redis.asyncio as aioredis
from backend.app.config import settings
from backend.app.core.logging import logger
from backend.app.websocket.connection_manager import manager


async def start_redis_event_listener():
    """
    Subscribes to Redis Pub/Sub channel for WebSocket events and broadcasts
    them in real time to connected WebSocket clients.
    Runs as a background asyncio task during FastAPI lifespan.
    """
    channel_name = settings.WS_REDIS_CHANNEL
    logger.info("Starting Redis Pub/Sub listener for WebSocket events", channel=channel_name)

    redis_url = settings.REDIS_URL
    while True:
        try:
            r = aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(channel_name)
            logger.info("Successfully subscribed to Redis WebSocket channel", channel=channel_name)

            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    data = message.get("data")
                    if isinstance(data, str):
                        try:
                            event_data = json.loads(data)
                            await manager.broadcast(event_data)
                        except json.JSONDecodeError:
                            logger.warning("Received non-JSON Redis Pub/Sub message", data=data)
        except asyncio.CancelledError:
            logger.info("Redis WebSocket subscriber task cancelled, shutting down listener.")
            break
        except Exception as e:
            logger.warning("Redis Pub/Sub listener disconnected, retrying in 5 seconds...", error=str(e))
            await asyncio.sleep(5)
