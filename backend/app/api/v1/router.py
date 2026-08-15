from fastapi import APIRouter
from backend.app.api.v1 import health, models, predict, simulator, incidents, retraining, canary, jobs

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(models.router, tags=["Models"])
api_router.include_router(predict.router, tags=["Prediction Engine"])
api_router.include_router(simulator.router, tags=["Drift Simulator"])
api_router.include_router(incidents.router, tags=["Incidents & Root Cause Analysis"])
api_router.include_router(retraining.router, tags=["Automated Retraining"])
api_router.include_router(canary.router, tags=["Canary & Shadow Deployment"])
api_router.include_router(jobs.router, tags=["Background Job Status Tracking"])



