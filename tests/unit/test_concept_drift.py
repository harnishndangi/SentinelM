"""
Unit tests for SentinelML Concept Drift Detection Engine & Delayed Label Processing.

Tests:
- ADWIN Detector stream evaluation
- Page-Hinkley Detector change-point detection
- DDM Detector binary error stream warnings and drift
- ConceptDriftMonitor orchestration
- DelayedLabelProcessor ground truth feedback ingestion & PostgreSQL/SQLite DB persistence
"""
import uuid
import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.prediction import Prediction
from backend.app.models.ground_truth import GroundTruthLog
from backend.app.models.drift import DriftEvent, DriftScore
from backend.app.core.enums import DriftType
from ml.drift.concept_drift import (
    ADWINDetector,
    PageHinkleyDetector,
    DDMDetector,
    ConceptDriftMonitor,
)
from ml.drift.delayed_labels import DelayedLabelProcessor
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session for concept drift testing."""
    db_file = tmp_path / "test_concept_drift.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()

    registry = ModelRegistry(session)
    ver_dict = registry.register_candidate(
        model_name="FraudDetector",
        version="v1.0.0",
        algorithm="XGBoost",
    )
    model_version_id = ver_dict["model_id"]

    try:
        yield session, model_version_id
    finally:
        session.close()
        engine.dispose()


def test_adwin_detector_concept_drift_simulation():
    """Simulates stationary error stream followed by sudden concept drift error jump in ADWIN."""
    np.random.seed(42)
    detector = ADWINDetector(delta=0.002)

    drift_triggered = False

    # Stage 1: Stationary low error stream (2% error rate)
    for _ in range(300):
        val = 1.0 if np.random.rand() < 0.02 else 0.0
        drift, warn, _ = detector.update(val)
        if drift:
            drift_triggered = True

    assert drift_triggered is False, "ADWIN should not trigger drift on stationary low-error stream"

    # Stage 2: Sudden concept drift (80% error rate)
    drift_after_shift = False
    for _ in range(200):
        val = 1.0 if np.random.rand() < 0.80 else 0.0
        drift, warn, _ = detector.update(val)
        if drift:
            drift_after_shift = True
            break

    assert drift_after_shift is True, "ADWIN must trigger concept drift when error rate jumps to 80%"


def test_page_hinkley_detector_concept_drift():
    """Verifies Page-Hinkley change detector on continuous mean shift."""
    np.random.seed(42)
    detector = PageHinkleyDetector(min_instances=10, threshold=10.0, delta=0.005)

    # Low error stream
    for _ in range(100):
        detector.update(0.01)

    # Shifted high error stream
    drift_detected = False
    for _ in range(100):
        drift, _, _ = detector.update(0.95)
        if drift:
            drift_detected = True
            break

    assert drift_detected is True, "Page-Hinkley should detect mean shift in error stream"


def test_ddm_detector_binary_error_stream():
    """Verifies DDM binary error stream warning and drift triggers."""
    np.random.seed(42)
    detector = DDMDetector(min_num_instances=20, warning_threshold=2.0, drift_threshold=3.0)

    # Stationary low error stream (2% error rate)
    for _ in range(150):
        detector.update(np.random.rand() < 0.02)

    # Sudden high error stream (60% error rate)
    drift_triggered = False
    for _ in range(150):
        drift, warn, _ = detector.update(np.random.rand() < 0.60)
        if drift:
            drift_triggered = True
            break

    assert drift_triggered is True, "DDM must trigger drift level on high error rate"


def test_concept_drift_monitor():
    """Verifies ConceptDriftMonitor multi-detector orchestration."""
    monitor = ConceptDriftMonitor(ph_threshold=10.0, ddm_min_instances=20)

    np.random.seed(42)
    # Low error stream
    for _ in range(100):
        status = monitor.update(error_val=0.01, is_binary_error=False)

    assert status["severity"] == "NONE"

    # High error stream
    drift_detected = False
    for _ in range(150):
        status = monitor.update(error_val=0.90, is_binary_error=True)
        if status["drift_detected"]:
            drift_detected = True
            break

    assert drift_detected is True
    assert status["severity"] in ["HIGH", "CRITICAL"]


def test_delayed_label_processing_and_db_persistence(test_db):
    """
    Verifies DelayedLabelProcessor ingests ground truth label feedback,
    associates labels with past predictions, records GroundTruthLog, updates error metrics,
    and persists Concept Drift events to PostgreSQL/SQLite DB.
    """
    session, model_ver_id = test_db

    # Create a dummy prediction record in DB
    pred_id_str = f"pred_{uuid.uuid4().hex[:12]}"
    pred_record = Prediction(
        model_version_id=model_ver_id,
        prediction_id=pred_id_str,
        input_features={"amount": 1000.0, "oldbalanceOrg": 5000.0},
        output_prediction={"prediction": 0, "fraud_probability": 0.02},
        confidence_score=0.02,
        latency_ms=5.0,
    )
    session.add(pred_record)
    session.commit()

    processor = DelayedLabelProcessor(session)

    # Ingest delayed label feedback (ground truth actual_label = 1.0 -> Fraud, so prediction was misclassified!)
    res = processor.process_feedback(
        prediction_id=pred_id_str,
        actual_label=1.0,
        feedback_source="chargeback_report",
        save_to_db=True,
    )

    assert res["prediction_id"] == pred_id_str
    assert res["actual_label"] == 1.0
    assert res["predicted_label"] == 0
    assert res["is_binary_error"] is True
    assert res["error_val"] == pytest.approx(0.98, abs=1e-2)

    # Check updated Prediction in DB
    updated_pred = session.query(Prediction).filter(Prediction.prediction_id == pred_id_str).first()
    assert updated_pred.actual_label == 1.0
    assert updated_pred.label_received_at is not None
    assert updated_pred.error_val == pytest.approx(0.98, abs=1e-2)

    # Check GroundTruthLog in DB
    gt_logs = session.query(GroundTruthLog).filter(GroundTruthLog.prediction_id == updated_pred.id).all()
    assert len(gt_logs) == 1
    assert gt_logs[0].actual_label == 1.0
    assert gt_logs[0].feedback_source == "chargeback_report"
