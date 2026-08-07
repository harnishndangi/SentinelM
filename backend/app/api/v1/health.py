from fastapi import APIRouter
from backend.app.schemas.health import HealthResponse
from backend.app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Backend Health Check Endpoint."""
    return HealthResponse(
        status="healthy",
        service="sentinelml-api",
        version=settings.VERSION,
    )
