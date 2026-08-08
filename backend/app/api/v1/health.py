from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.health_service import HealthService
from backend.app.schemas.health import HealthResponse
from backend.app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)) -> HealthResponse:
    """Backend Health Check Endpoint with DB connection check."""
    service = HealthService(db)
    is_db_connected = service.check_db_connection()
    status_str = "healthy" if is_db_connected else "degraded"

    return HealthResponse(
        status=status_str,
        service="sentinelml-api",
        version=settings.VERSION,
    )


@router.get("/health/details")
def get_health_details(db: Session = Depends(get_db)):
    """Detailed health status endpoint including DB and Redis dependency status."""
    service = HealthService(db)
    return service.get_full_health_status()
