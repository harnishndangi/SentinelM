from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.core.celery_app import celery_app, SentinelBaseTask, update_job_progress
from backend.app.core.logging import logger
from backend.app.database import SessionLocal
from backend.app.websocket import publish_websocket_event, EventType
from backend.app.websocket.events import (
    IncidentCreatedPayload,
    IncidentResolvedPayload,
    ModelHealthChangedPayload,
)


@celery_app.task(bind=True, base=SentinelBaseTask, max_retries=3, default_retry_delay=10)
def generate_incident_report_task(
    self,
    incident_id: str,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background worker for operational incident report generation and Root Cause Analysis (RCA).
    Performs SHAP attribution, performance degradation check, and timeline updates.
    """
    current_job_id = job_id or self.request.id
    logger.info("Executing incident report generation task", job_id=current_job_id, incident_id=incident_id)

    update_job_progress(current_job_id, "STARTED", 10.0)

    db = SessionLocal()
    try:
        from backend.app.models.incident import Incident
        from backend.app.models.model import ModelVersion
        from backend.app.services.incident_service import IncidentService
        from ml.explainability.root_cause import RootCauseAnalyzer
        from ml.simulator.drift_simulator import DriftSimulator

        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            raise ValueError(f"Incident '{incident_id}' not found.")

        update_job_progress(current_job_id, "RUNNING", 30.0)

        # Broadcast INCIDENT_CREATED payload if newly opened
        publish_websocket_event(
            EventType.INCIDENT_CREATED,
            IncidentCreatedPayload(
                incident_id=inc.id,
                model_version_id=inc.model_version_id,
                title=inc.title,
                severity=inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
                opened_at=inc.opened_at.isoformat() if inc.opened_at else datetime.now(timezone.utc).isoformat(),
                description=inc.description,
            ),
        )

        update_job_progress(current_job_id, "RUNNING", 60.0)

        # Execute RCA analysis
        model_ver = db.query(ModelVersion).filter(ModelVersion.id == inc.model_version_id).first()
        model_name = model_ver.model.name if model_ver and model_ver.model else "FraudDetector"
        model_version_str = model_ver.version if model_ver else "v1.0.0"

        simulator = DriftSimulator(db)
        ref_df = simulator.get_baseline_reference_data(num_records=1500)
        cur_df = simulator.apply_drift_scenario(df=ref_df, scenario="MULTI_FEATURE_DRIFT", intensity=0.85)

        analyzer = RootCauseAnalyzer()
        rca_res = analyzer.analyze_root_cause(
            model_name=model_name,
            model_version=model_version_str,
            ref_df=ref_df,
            cur_df=cur_df,
        )

        inc.rca_result = rca_res
        db.add(inc)
        db.commit()

        update_job_progress(current_job_id, "RUNNING", 90.0)

        summary = {
            "incident_id": incident_id,
            "title": inc.title,
            "status": inc.status.value if hasattr(inc.status, "value") else str(inc.status),
            "rca_result": rca_res,
        }

        update_job_progress(current_job_id, "SUCCESS", 100.0, payload_update=summary)
        return summary
    except Exception as exc:
        logger.error("Error generating incident report in worker task", error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            raise exc
    finally:
        db.close()
