"""
Central Drift Detection Engine Orchestrator.

Compares REFERENCE DISTRIBUTION against CURRENT PRODUCTION WINDOW.
Calculates statistical drift scores (PSI, KS, JS, Wasserstein, Chi-Square),
determines per-feature severity, calculates overall model drift status,
and persists analysis results to PostgreSQL DriftEvent and DriftScore tables.
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.drift import DriftEvent, DriftScore
from backend.app.core.enums import DriftType
from ml.drift.base import DriftResult, DriftSeverity
from ml.drift.feature_drift import FeatureDriftAnalyzer
from ml.drift.prediction_drift import PredictionDriftAnalyzer


class DriftEngine:
    """
    SentinelML Central Statistical Drift Detection Engine.
    
    Usage:
        engine = DriftEngine(db_session)
        report = engine.run_drift_analysis(
            reference_data=df_reference,
            current_data=df_production,
            model_version_id="model_ver_uuid",
            save_to_db=True,
        )
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        numerical_method: str = "psi",
        categorical_method: str = "chi_square",
    ):
        self.db = db
        self.analyzer = FeatureDriftAnalyzer(
            numerical_method=numerical_method,
            categorical_method=categorical_method,
        )
        self.prediction_analyzer = PredictionDriftAnalyzer()

    def _determine_overall_severity(self, feature_results: List[DriftResult]) -> DriftSeverity:
        """Determines overall aggregated model drift severity."""
        if not feature_results:
            return DriftSeverity.NONE

        severities = [r.severity for r in feature_results]
        drifted_count = sum(1 for r in feature_results if r.is_drifted)
        total_features = len(feature_results)
        drift_ratio = drifted_count / total_features if total_features > 0 else 0.0

        if DriftSeverity.CRITICAL in severities or drift_ratio >= 0.5:
            return DriftSeverity.CRITICAL
        elif DriftSeverity.HIGH in severities or drift_ratio >= 0.3:
            return DriftSeverity.HIGH
        elif DriftSeverity.MEDIUM in severities or drift_ratio >= 0.15:
            return DriftSeverity.MEDIUM
        elif DriftSeverity.LOW in severities or drifted_count > 0:
            return DriftSeverity.LOW
        else:
            return DriftSeverity.NONE

    def run_evidently_validation(
        self, reference_df: pd.DataFrame, current_df: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Optional Evidently AI report monitoring/validation layer.
        Executes if Evidently library is installed.
        """
        try:
            from evidently.report import Report
            from evidently.metric_preset import DataDriftPreset

            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=reference_df, current_data=current_df)
            dict_report = report.as_dict()
            return dict_report
        except ImportError:
            return {"note": "Evidently AI not installed. Statistical engine executed standalone."}
        except Exception as e:
            return {"error": f"Evidently validation failed: {str(e)}"}

    def run_drift_analysis(
        self,
        reference_data: Union[pd.DataFrame, str, Path],
        current_data: Union[pd.DataFrame, str, Path],
        model_version_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
        save_to_db: bool = True,
        include_evidently: bool = False,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive statistical drift analysis comparing Reference Distribution
        against Current Production Window.
        """
        # Load reference data
        if isinstance(reference_data, (str, Path)):
            ref_df = pd.read_csv(reference_data)
        else:
            ref_df = pd.DataFrame(reference_data)

        # Load current production data
        if isinstance(current_data, (str, Path)):
            cur_df = pd.read_csv(current_data)
        else:
            cur_df = pd.DataFrame(current_data)

        # Exclude label column if present
        for col in ["target", "label", "Class", "is_fraud"]:
            if col in ref_df.columns and col in cur_df.columns:
                ref_df = ref_df.drop(columns=[col])
                cur_df = cur_df.drop(columns=[col])

        # Run statistical feature drift analysis
        drift_results = self.analyzer.analyze_dataset(ref_df, cur_df)

        overall_severity = self._determine_overall_severity(drift_results)
        is_actionable = overall_severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]

        feature_summary = [r.to_dict() for r in drift_results]
        drifted_features = [r.feature for r in drift_results if r.is_drifted]

        evidently_summary = None
        if include_evidently:
            evidently_summary = self.run_evidently_validation(ref_df, cur_df)

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model_version_id": model_version_id,
            "overall_status": overall_severity.value,
            "is_actionable": is_actionable,
            "total_features": len(drift_results),
            "drifted_features_count": len(drifted_features),
            "drifted_features": drifted_features,
            "per_feature_results": feature_summary,
            "evidently_validation": evidently_summary,
        }

        # Persist results to PostgreSQL / SQLite database if db session & model_version_id exist
        if save_to_db and self.db is not None and model_version_id:
            drift_event = DriftEvent(
                model_version_id=model_version_id,
                dataset_version_id=dataset_version_id,
                drift_type=DriftType.DATA_DRIFT,
                overall_status=overall_severity.value,
                is_actionable=is_actionable,
                detected_at=datetime.now(timezone.utc),
            )
            self.db.add(drift_event)
            self.db.commit()
            self.db.refresh(drift_event)

            for res in drift_results:
                score_obj = DriftScore(
                    drift_event_id=drift_event.id,
                    feature_name=res.feature,
                    method=res.method,
                    p_value=res.p_value,
                    drift_score=float(res.score),
                    threshold=float(res.threshold),
                    severity=res.severity.value if isinstance(res.severity, DriftSeverity) else str(res.severity),
                    is_drifted=res.is_drifted,
                )
                self.db.add(score_obj)

            self.db.commit()
            summary["drift_event_id"] = drift_event.id

            # Automatically trigger Incident Creation when drift is HIGH/CRITICAL
            if is_actionable:
                try:
                    from backend.app.services.incident_service import IncidentService
                    inc_service = IncidentService(self.db)
                    inc_obj = inc_service.create_automated_drift_incident(
                        drift_report=summary,
                        model_version_id=model_version_id,
                        ref_df=ref_df,
                        cur_df=cur_df,
                    )
                    summary["incident_id"] = inc_obj.id
                except Exception as e:
                    summary["incident_error"] = f"Failed to automate incident creation: {str(e)}"

        return summary
