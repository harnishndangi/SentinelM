import uuid
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class EventType(str, Enum):
    MODEL_HEALTH_CHANGED = "MODEL_HEALTH_CHANGED"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    RETRAINING_STARTED = "RETRAINING_STARTED"
    TRAINING_PROGRESS = "TRAINING_PROGRESS"
    CANDIDATE_CREATED = "CANDIDATE_CREATED"
    QUALITY_GATE_PASSED = "QUALITY_GATE_PASSED"
    QUALITY_GATE_FAILED = "QUALITY_GATE_FAILED"
    CANARY_STARTED = "CANARY_STARTED"
    MODEL_PROMOTED = "MODEL_PROMOTED"
    MODEL_ROLLED_BACK = "MODEL_ROLLED_BACK"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"


class ModelHealthChangedPayload(BaseModel):
    model_version_id: str
    model_name: Optional[str] = "FraudDetector"
    previous_status: str
    new_status: str
    health_score: float
    details: Optional[Dict[str, Any]] = None


class DriftDetectedPayload(BaseModel):
    model_version_id: str
    drift_type: str  # e.g., FEATURE_DRIFT, CONCEPT_DRIFT, PREDICTION_DRIFT
    feature_name: Optional[str] = None
    psi_score: Optional[float] = None
    p_value: Optional[float] = None
    threshold: Optional[float] = 0.1
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IncidentCreatedPayload(BaseModel):
    incident_id: str
    model_version_id: str
    title: str
    severity: str
    opened_at: str
    description: Optional[str] = None


class RetrainingStartedPayload(BaseModel):
    run_id: str
    model_version_id: Optional[str] = None
    incident_id: Optional[str] = None
    model_type: str = "xgboost"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TrainingProgressPayload(BaseModel):
    run_id: str
    current_step: str
    progress_percentage: float
    epoch: Optional[int] = None
    loss: Optional[float] = None
    metrics: Optional[Dict[str, float]] = None


class CandidateCreatedPayload(BaseModel):
    candidate_version_id: str
    model_name: str
    version_str: str
    metrics: Dict[str, float]
    artifact_path: Optional[str] = None


class QualityGatePassedPayload(BaseModel):
    candidate_version_id: str
    production_version_id: Optional[str] = None
    evaluations: List[Dict[str, Any]]
    passed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class QualityGateFailedPayload(BaseModel):
    candidate_version_id: str
    rejection_reasons: List[str]
    evaluations: List[Dict[str, Any]]
    failed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CanaryStartedPayload(BaseModel):
    candidate_version_id: str
    production_version_id: Optional[str] = None
    canary_percentage: int
    mode: str = "CANARY"  # CANARY or SHADOW
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelPromotedPayload(BaseModel):
    model_name: str
    version_str: str
    candidate_version_id: Optional[str] = None
    previous_production_version: Optional[str] = None
    promoted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class ModelRolledBackPayload(BaseModel):
    model_name: str
    target_version: str
    current_version: Optional[str] = None
    reason: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IncidentResolvedPayload(BaseModel):
    incident_id: str
    resolved_at: str
    resolution_notes: Optional[str] = None


class WebSocketEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any]
