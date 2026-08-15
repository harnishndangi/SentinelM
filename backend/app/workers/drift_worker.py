from typing import Dict, Any, Optional
from backend.app.core.celery_app import celery_app, SentinelBaseTask, update_job_progress
from backend.app.core.logging import logger
from backend.app.database import SessionLocal
from backend.app.websocket import publish_websocket_event, EventType
from backend.app.websocket.events import DriftDetectedPayload, ModelHealthChangedPayload


@celery_app.task(bind=True, base=SentinelBaseTask, max_retries=3, default_retry_delay=15)
def calculate_drift_task(
    self,
    model_version_id: str,
    scenario: str = "MULTI_FEATURE_DRIFT",
    intensity: float = 0.85,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background worker for computing data & concept drift.
    Moves expensive statistical drift tests (PSI, KS-test, Chi-Square, Wasserstein) out of API threads.
    """
    current_job_id = job_id or self.request.id
    logger.info("Executing background drift calculation task", job_id=current_job_id, model_version_id=model_version_id)
    update_job_progress(current_job_id, "STARTED", 10.0)

    db = SessionLocal()
    try:
        from ml.simulator.drift_simulator import DriftSimulator
        from ml.drift.drift_engine import DriftEngine

        simulator = DriftSimulator(db)
        update_job_progress(current_job_id, "RUNNING", 30.0)

        ref_df = simulator.get_baseline_reference_data(num_records=1000)
        cur_df = simulator.apply_drift_scenario(df=ref_df, scenario=scenario, intensity=intensity)

        update_job_progress(current_job_id, "RUNNING", 60.0)

        engine = DriftEngine()
        drift_report = engine.analyze(reference_df=ref_df, current_df=cur_df)

        update_job_progress(current_job_id, "RUNNING", 85.0)

        has_drift = drift_report.get("dataset_drift_detected", False)
        drift_share = drift_report.get("drifted_feature_share", 0.0)

        # Broadcast WebSocket event if drift is detected
        if has_drift:
            publish_websocket_event(
                EventType.DRIFT_DETECTED,
                DriftDetectedPayload(
                    model_version_id=model_version_id,
                    drift_type="FEATURE_DRIFT",
                    psi_score=drift_share,
                    threshold=0.2,
                ),
            )
            publish_websocket_event(
                EventType.MODEL_HEALTH_CHANGED,
                ModelHealthChangedPayload(
                    model_version_id=model_version_id,
                    previous_status="HEALTHY",
                    new_status="DEGRADED",
                    health_score=max(0.0, 1.0 - drift_share),
                    details={"drifted_features": drift_report.get("drifted_features", [])},
                ),
            )

        result_summary = {
            "model_version_id": model_version_id,
            "scenario": scenario,
            "dataset_drift_detected": has_drift,
            "drifted_feature_share": drift_share,
            "drifted_features": drift_report.get("drifted_features", []),
        }

        update_job_progress(current_job_id, "SUCCESS", 100.0, payload_update=result_summary)
        return result_summary
    except Exception as exc:
        logger.error("Error in drift calculation worker task", error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            raise exc
    finally:
        db.close()
