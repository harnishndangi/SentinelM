"""
FastAPI Router for SentinelML Incident Management and Root Cause Analysis (RCA).
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app.models.incident import Incident
from backend.app.models.model import ModelVersion
from backend.app.core.enums import IncidentSeverity, IncidentStatus, IncidentEventType
from ml.explainability.root_cause import RootCauseAnalyzer
from ml.simulator.drift_simulator import DriftSimulator


router = APIRouter(prefix="/incidents", tags=["Incidents & Root Cause Analysis"])


class CreateIncidentRequest(BaseModel):
    model_version_id: str = Field(..., description="Target model version ID")
    title: str = Field(..., description="Incident title summary")
    description: Optional[str] = Field(default=None, description="Detailed incident description")
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM, description="Incident severity level")


class IncidentResponse(BaseModel):
    id: str
    model_version_id: str
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    opened_at: str
    rca_result: Optional[Dict[str, Any]] = None


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Incident",
)
def create_incident(
    request: CreateIncidentRequest,
    db: Session = Depends(get_db),
):
    """Creates a new operational incident record."""
    inc = Incident(
        model_version_id=request.model_version_id,
        title=request.title,
        description=request.description,
        severity=request.severity,
        status=IncidentStatus.OPEN,
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return IncidentResponse(
        id=inc.id,
        model_version_id=inc.model_version_id,
        title=inc.title,
        description=inc.description,
        severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
        status=inc.status.value if hasattr(inc.status, "value") else str(inc.status),
        opened_at=inc.opened_at.isoformat(),
        rca_result=inc.rca_result,
    )


from backend.app.services.incident_service import IncidentService


class ResolveIncidentRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Optional resolution notes or actions taken")


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List Operational Incidents",
    description="Retrieves all operational incidents with optional status or severity filtering.",
)
def list_incidents(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists operational incidents."""
    query = db.query(Incident)
    if status_filter:
        query = query.filter(Incident.status == status_filter)
    if severity_filter:
        query = query.filter(Incident.severity == severity_filter)

    incidents = query.order_by(Incident.opened_at.desc()).all()

    service = IncidentService(db)
    results = []
    for inc in incidents:
        try:
            results.append(service.get_incident_with_timeline(inc.id))
        except Exception:
            results.append({
                "incident_id": inc.id,
                "model_version_id": inc.model_version_id,
                "title": inc.title,
                "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
                "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
                "opened_at": inc.opened_at.isoformat() if inc.opened_at else None,
            })
    return results


@router.get(
    "/{incident_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Incident Details & Event Timeline",
    description="Returns detailed incident info, model metadata, root cause diagnosis, and chronological timeline events formatted for frontend visualization.",
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves incident details with timeline array for frontend visualization."""
    try:
        service = IncidentService(db)
        return service.get_incident_with_timeline(incident_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{incident_id}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve Incident",
    description="Marks an incident as RESOLVED, updates resolved_at timestamp, and appends INCIDENT_RESOLVED timeline event.",
)
def resolve_incident(
    incident_id: str,
    request: Optional[ResolveIncidentRequest] = None,
    db: Session = Depends(get_db),
):
    """Resolves an active incident."""
    try:
        service = IncidentService(db)
        notes = request.notes if request else None
        return service.resolve_incident(incident_id, notes=notes)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


from backend.app.models.job import AsyncJob
from backend.app.workers.incident_worker import generate_incident_report_task


@router.post(
    "/{incident_id}/rca",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute Root-Cause Analysis for Incident via Celery Worker",
    description="Calculates performance degradation, SHAP feature impact ranking, and affected business segments asynchronously in Celery.",
)
def run_incident_rca(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Triggers Root Cause Analysis for a specific incident asynchronously."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    task = generate_incident_report_task.delay(incident_id=incident_id)

    job_rec = AsyncJob(
        job_id=task.id,
        task_type="incident_report",
        status="QUEUED",
        progress=0.0,
        payload={"incident_id": incident_id, "model_version_id": inc.model_version_id},
    )
    db.add(job_rec)
    db.commit()

    return {
        "job_id": task.id,
        "incident_id": incident_id,
        "status": "QUEUED",
        "message": "Incident RCA analysis task queued successfully in background Celery worker.",
    }

