from fastapi import APIRouter
from backend.app.api.v1 import health, models, predict, simulator

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(models.router, tags=["Models"])
api_router.include_router(predict.router, tags=["Prediction Engine"])
api_router.include_router(simulator.router, tags=["Drift Simulator"])
