from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.model_service import ModelService
from backend.app.repositories.model_repository import MLModelRepository

router = APIRouter()


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    """List registered ML models."""
    repo = MLModelRepository(db)
    models = repo.list_all()
    return [{"id": m.id, "name": m.name, "description": m.description, "framework": m.framework} for m in models]


@router.get("/models/{name}")
def get_model_details(name: str, db: Session = Depends(get_db)):
    """Get model details including production version and metrics."""
    service = ModelService(db)
    details = service.get_model_details(name)
    if not details:
        raise HTTPException(status_code=404, detail=f"Model '{name}' not found")
    return details
