from fastapi import APIRouter
from backend.app.api.v1 import health, models

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(models.router, tags=["Models"])
