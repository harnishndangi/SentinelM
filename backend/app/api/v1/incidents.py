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
from backend.app.core.enums import IncidentSeverity, IncidentStatus
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


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Incident Details",
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves incident details along with stored RCA results."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

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


@router.post(
    "/{incident_id}/rca",
    status_code=status.HTTP_200_OK,
    summary="Execute Root-Cause Analysis for Incident",
    description="Calculates performance degradation, SHAP feature impact ranking, and affected business segments, storing RCA results in the Incident database record.",
)
def run_incident_rca(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Triggers Root Cause Analysis for a specific incident."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")

    model_ver = db.query(ModelVersion).filter(ModelVersion.id == inc.model_version_id).first()
    model_name = model_ver.model.name if model_ver and model_ver.model else "FraudDetector"
    model_version_str = model_ver.version if model_ver else "v1.0.0"

    # Generate baseline reference vs drifted current window datasets for RCA
    simulator = DriftSimulator(db)
    ref_df = simulator.get_baseline_reference_data(num_records=2000)

    # Generate multi-feature drift dataset representing the incident state
    cur_df = simulator.apply_drift_scenario(
        df=ref_df,
        scenario="MULTI_FEATURE_DRIFT",
        intensity=0.85,
    )

    analyzer = RootCauseAnalyzer()
    rca_res = analyzer.analyze_root_cause(
        model_name=model_name,
        model_version=model_version_str,
        ref_df=ref_df,
        cur_df=cur_df,
    )

    # Update Incident with RCA payload in PostgreSQL/SQLite DB
    inc.rca_result = rca_res
    db.add(inc)
    db.commit()
    db.refresh(inc)

    return rca_res
