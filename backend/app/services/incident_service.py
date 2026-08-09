"""
SentinelML Incident Management Service.

Handles automated incident creation upon high/critical drift or performance drops,
persists immutable event timelines suitable for frontend visualization, triggers RCA,
and manages incident resolutions.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.incident import Incident, IncidentEvent
from backend.app.models.model import ModelVersion
from backend.app.core.enums import IncidentSeverity, IncidentStatus, IncidentEventType
from ml.explainability.root_cause import RootCauseAnalyzer


class IncidentService:
    """
    Service managing incident lifecycle, automated creation, event timeline persistence,
    and root-cause integration.
    """

    def __init__(self, db: Session):
        self.db = db

    def add_timeline_event(
        self,
        incident_id: str,
        event_type: Union[str, IncidentEventType],
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IncidentEvent:
        """Appends a new timeline event to an incident."""
        evt_type_str = event_type.value if hasattr(event_type, "value") else str(event_type)
        event = IncidentEvent(
            incident_id=incident_id,
            event_type=evt_type_str,
            message=message,
            metadata_json=metadata,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def create_automated_drift_incident(
        self,
        drift_report: Dict[str, Any],
        model_version_id: str,
        ref_df: Optional[pd.DataFrame] = None,
        cur_df: Optional[pd.DataFrame] = None,
    ) -> Incident:
        """
        Automatically creates an Incident when HIGH or CRITICAL drift occurs.
        Logs timeline: DRIFT_DETECTED -> INCIDENT_CREATED -> ROOT_CAUSE_STARTED -> ROOT_CAUSE_COMPLETED.
        """
        overall_status = drift_report.get("overall_status", "HIGH")
        severity_enum = IncidentSeverity.CRITICAL if overall_status == "CRITICAL" else IncidentSeverity.HIGH

        model_ver = self.db.query(ModelVersion).filter(ModelVersion.id == model_version_id).first()
        model_name = model_ver.model.name if model_ver and model_ver.model else "FraudDetector"
        model_version_str = model_ver.version if model_ver else "v1.0.0"

        title = f"Automated Alert: {overall_status} statistical drift on {model_name}-{model_version_str}"
        description = f"Monitoring engine detected {overall_status} distribution shift requiring investigation or retraining."

        incident = Incident(
            model_version_id=model_version_id,
            title=title,
            description=description,
            severity=severity_enum,
            status=IncidentStatus.OPEN,
            incident_type="DATA_DRIFT",
            recommended_action="RETRAIN_MODEL",
            opened_at=datetime.now(timezone.utc),
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        # Timeline Event 1: DRIFT_DETECTED
        self.add_timeline_event(
            incident_id=incident.id,
            event_type=IncidentEventType.DRIFT_DETECTED,
            message=f"Statistical drift engine detected {overall_status} distribution shift.",
            metadata={"drift_report_summary": drift_report.get("overall_status")},
        )

        # Timeline Event 2: INCIDENT_CREATED
        self.add_timeline_event(
            incident_id=incident.id,
            event_type=IncidentEventType.INCIDENT_CREATED,
            message=f"Operational incident #{incident.id[:8]} created automatically.",
        )

        # Timeline Event 3 & 4: ROOT_CAUSE_STARTED & COMPLETED
        if ref_df is not None and cur_df is not None:
            self.add_timeline_event(
                incident_id=incident.id,
                event_type=IncidentEventType.ROOT_CAUSE_STARTED,
                message="Automated Root Cause Analysis (RCA) execution started.",
            )

            try:
                analyzer = RootCauseAnalyzer()
                rca_res = analyzer.analyze_root_cause(
                    model_name=model_name,
                    model_version=model_version_str,
                    ref_df=ref_df,
                    cur_df=cur_df,
                    drift_report=drift_report,
                )
                incident.rca_result = rca_res
                self.db.add(incident)
                self.db.commit()

                self.add_timeline_event(
                    incident_id=incident.id,
                    event_type=IncidentEventType.ROOT_CAUSE_COMPLETED,
                    message="Root Cause Analysis completed. Identified top feature contributors and affected segments.",
                    metadata={"top_contributor": rca_res.get("contributors", [{}])[0].get("feature")},
                )
            except Exception as e:
                self.add_timeline_event(
                    incident_id=incident.id,
                    event_type=IncidentEventType.ROOT_CAUSE_COMPLETED,
                    message=f"Root cause calculation error: {str(e)}",
                )

        return incident

    def get_incident_with_timeline(self, incident_id: str) -> Dict[str, Any]:
        """
        Retrieves incident record along with chronological timeline formatted for frontend visualization.
        """
        inc = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            raise ValueError(f"Incident '{incident_id}' not found.")

        model_ver = self.db.query(ModelVersion).filter(ModelVersion.id == inc.model_version_id).first()
        model_name = model_ver.model.name if model_ver and model_ver.model else "FraudDetector"
        model_version_str = model_ver.version if model_ver else "v1.0.0"

        # Fetch timeline events ordered by creation timestamp
        events = (
            self.db.query(IncidentEvent)
            .filter(IncidentEvent.incident_id == inc.id)
            .order_by(IncidentEvent.created_at.asc())
            .all()
        )

        timeline_data = [
            {
                "event_id": evt.id,
                "event_type": evt.event_type,
                "message": evt.message,
                "timestamp": evt.created_at.isoformat() if evt.created_at else None,
                "metadata": evt.metadata_json,
            }
            for evt in events
        ]

        return {
            "incident_id": inc.id,
            "model_id": model_ver.model_id if model_ver else None,
            "model_name": model_name,
            "model_version": model_version_str,
            "type": inc.incident_type,
            "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
            "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            "detected_at": inc.opened_at.isoformat() if inc.opened_at else None,
            "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            "description": inc.description,
            "root_cause": inc.rca_result,
            "recommended_action": inc.recommended_action,
            "timeline": timeline_data,
        }

    def resolve_incident(self, incident_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolves an incident, updates status to RESOLVED, sets resolved_at, and appends INCIDENT_RESOLVED event.
        """
        inc = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            raise ValueError(f"Incident '{incident_id}' not found.")

        now_utc = datetime.now(timezone.utc)
        inc.status = IncidentStatus.RESOLVED
        inc.resolved_at = now_utc
        self.db.add(inc)

        self.add_timeline_event(
            incident_id=inc.id,
            event_type=IncidentEventType.INCIDENT_RESOLVED,
            message=notes or "Incident resolved successfully.",
        )
        self.db.commit()

        return self.get_incident_with_timeline(incident_id)
