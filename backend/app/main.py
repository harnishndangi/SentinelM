import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.core.logging import setup_logging, logger
from backend.app.api.v1.router import api_router
from backend.app.websocket import websocket_router, start_redis_event_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    setup_logging()
    logger.info("Starting SentinelML API Server", version=settings.VERSION, env=settings.ENVIRONMENT)
    
    # Launch Redis Pub/Sub listener for WebSockets
    pubsub_task = asyncio.create_task(start_redis_event_listener())
    yield
    # Shutdown tasks
    logger.info("Shutting down SentinelML API Server")
    pubsub_task.cancel()
    try:
        await pubsub_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

from backend.app.metrics.prometheus import prometheus_middleware, get_metrics_response

# Include CORS middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Prometheus HTTP instrumentation middleware
app.middleware("http")(prometheus_middleware)

# Include API Router & WebSocket Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket_router)  # Mounts /ws/events


@app.get("/metrics", tags=["Telemetry"])
def metrics():
    """Prometheus telemetry instrumentation metrics endpoint."""
    return get_metrics_response()


@app.get("/")
def root():
    return {
        "message": "Welcome to SentinelML - Autonomous ML Reliability & Self-Healing Platform API",
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "metrics": "/metrics",
        "events_websocket": "/ws/events",
    }


