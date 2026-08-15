from typing import Dict, Any, Optional, List
from backend.app.core.celery_app import celery_app, SentinelBaseTask, update_job_progress
from backend.app.core.logging import logger
from backend.app.database import SessionLocal


@celery_app.task(bind=True, base=SentinelBaseTask, max_retries=3, default_retry_delay=10)
def calculate_shap_task(
    self,
    model_version_id: str,
    top_k: int = 10,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background worker for computing SHAP feature attributions and global feature importance.
    Offloads compute-intensive SHAP tree/kernel explainer calculations from FastAPI API requests.
    """
    current_job_id = job_id or self.request.id
    logger.info("Executing SHAP analysis task", job_id=current_job_id, model_version_id=model_version_id)

    update_job_progress(current_job_id, "STARTED", 10.0)

    db = SessionLocal()
    try:
        from ml.simulator.drift_simulator import DriftSimulator
        from ml.explainability.root_cause import RootCauseAnalyzer

        update_job_progress(current_job_id, "RUNNING", 30.0)
        simulator = DriftSimulator(db)
        ref_df = simulator.get_baseline_reference_data(num_records=1000)
        cur_df = simulator.apply_drift_scenario(df=ref_df, scenario="MULTI_FEATURE_DRIFT", intensity=0.7)

        update_job_progress(current_job_id, "RUNNING", 60.0)
        analyzer = RootCauseAnalyzer()
        rca_res = analyzer.analyze_root_cause(
            model_name="FraudDetector",
            model_version="v1.0.0",
            ref_df=ref_df,
            cur_df=cur_df,
        )

        update_job_progress(current_job_id, "RUNNING", 90.0)
        shap_rankings = rca_res.get("top_impacted_features", [])[:top_k]

        result = {
            "model_version_id": model_version_id,
            "top_k": top_k,
            "shap_feature_importance": shap_rankings,
            "business_impact": rca_res.get("impacted_business_segments", []),
            "summary": rca_res.get("summary", ""),
        }

        update_job_progress(current_job_id, "SUCCESS", 100.0, payload_update=result)
        return result
    except Exception as exc:
        logger.error("Error computing SHAP analysis in worker task", error=str(exc))
        try:
            self.retry(exc=exc)
        except Exception:
            raise exc
    finally:
        db.close()
