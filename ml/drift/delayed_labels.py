"""
Delayed Label Processing Engine for Concept Drift Monitoring.

Processes delayed ground truth labels (e.g., chargebacks, manual investigation labels),
links labels to past prediction records in PostgreSQL, calculates error metrics,
updates stream concept drift detectors (ADWIN, Page-Hinkley, DDM), and persists
concept drift events to PostgreSQL.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.orm import Session

from backend.app.models.prediction import Prediction
from backend.app.models.ground_truth import GroundTruthLog
from backend.app.models.drift import DriftEvent, DriftScore
from backend.app.core.enums import DriftType
from ml.drift.concept_drift import ConceptDriftMonitor


class DelayedLabelProcessor:
    """
    Processes delayed ground truth feedback and evaluates P(Y|X) concept drift over time.
    """

    def __init__(self, db: Session, monitor: Optional[ConceptDriftMonitor] = None):
        self.db = db
        self.monitor = monitor or ConceptDriftMonitor()

    def process_feedback(
        self,
        prediction_id: str,
        actual_label: float,
        feedback_source: str = "manual_review",
        save_to_db: bool = True,
    ) -> Dict[str, Any]:
        """
        Processes delayed ground truth feedback for a specific prediction ID.
        
        Steps:
        1. Locate prediction record in PostgreSQL.
        2. Update actual_label and compute prediction error e = |y - p|.
        3. Save GroundTruthLog.
        4. Pass error signal to ConceptDriftMonitor (ADWIN, Page-Hinkley, DDM).
        5. Persist concept drift alert to DriftEvent and DriftScore tables if drift/warning is triggered.
        """
        # Find prediction by prediction_id string or UUID
        pred_record = (
            self.db.query(Prediction)
            .filter((Prediction.prediction_id == prediction_id) | (Prediction.id == prediction_id))
            .first()
        )

        if not pred_record:
            raise ValueError(f"Prediction record '{prediction_id}' not found in database.")

        # Extract prediction values
        predicted_val = 0
        fraud_prob = 0.5
        if pred_record.output_prediction and isinstance(pred_record.output_prediction, dict):
            predicted_val = int(pred_record.output_prediction.get("prediction", 0))
            fraud_prob = float(pred_record.output_prediction.get("fraud_probability", 0.5))
        elif pred_record.confidence_score is not None:
            fraud_prob = float(pred_record.confidence_score)
            predicted_val = int(fraud_prob >= 0.5)

        # Compute prediction error signals
        binary_actual = int(actual_label >= 0.5)
        is_binary_error = bool(predicted_val != binary_actual)
        error_val = float(abs(binary_actual - fraud_prob))

        now_utc = datetime.now(timezone.utc)

        # Update prediction record
        pred_record.actual_label = float(actual_label)
        pred_record.label_received_at = now_utc.isoformat()
        pred_record.error_val = error_val
        self.db.add(pred_record)

        # Create GroundTruthLog record
        gt_log = GroundTruthLog(
            prediction=pred_record,
            actual_label=float(actual_label),
            feedback_source=feedback_source,
            received_at=now_utc,
        )
        self.db.add(gt_log)

        # Update concept drift monitor
        drift_status = self.monitor.update(error_val=error_val, is_binary_error=is_binary_error)

        drift_event_id = None
        if save_to_db and (drift_status["drift_detected"] or drift_status["warning_detected"]):
            # Create DriftEvent in PostgreSQL with drift_type = CONCEPT_DRIFT
            drift_event = DriftEvent(
                model_version_id=pred_record.model_version_id,
                drift_type=DriftType.CONCEPT_DRIFT,
                overall_status=drift_status["severity"],
                is_actionable=drift_status["is_actionable"],
                detected_at=now_utc,
            )
            self.db.add(drift_event)
            self.db.commit()
            self.db.refresh(drift_event)
            drift_event_id = drift_event.id

            # Save individual detector scores to DriftScore
            for det_name, det_info in drift_status["detectors"].items():
                score_val = 1.0 if det_info["drift"] else (0.5 if det_info.get("warning") else 0.0)
                d_score = DriftScore(
                    drift_event_id=drift_event.id,
                    feature_name="concept_drift_error_stream",
                    method=det_name,
                    drift_score=score_val,
                    threshold=0.5,
                    severity="CRITICAL" if det_info["drift"] else ("MEDIUM" if det_info.get("warning") else "NONE"),
                    is_drifted=det_info["drift"],
                )
                self.db.add(d_score)

        self.db.commit()

        return {
            "prediction_id": prediction_id,
            "actual_label": actual_label,
            "predicted_label": predicted_val,
            "fraud_probability": fraud_prob,
            "error_val": error_val,
            "is_binary_error": is_binary_error,
            "concept_drift_status": drift_status,
            "drift_event_id": drift_event_id,
        }
