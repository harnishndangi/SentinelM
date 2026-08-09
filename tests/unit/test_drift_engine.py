"""
Comprehensive unit tests for SentinelML Statistical Drift Engine.

Tests:
- PSI Detector (Population Stability Index)
- KS Detector (Kolmogorov-Smirnov 2-sample test)
- Jensen-Shannon Divergence Detector
- Wasserstein Distance Detector
- Chi-Square Test Detector
- FeatureDriftAnalyzer & PredictionDriftAnalyzer
- DriftEngine orchestrator & DB persistence to DriftEvent & DriftScore tables
"""
import uuid
import pytest
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.drift import DriftEvent, DriftScore
from ml.drift.base import DriftSeverity
from ml.drift.psi import PSIDetector
from ml.drift.ks import KSDetector
from ml.drift.jensen_shannon import JensenShannonDetector
from ml.drift.wasserstein import WassersteinDetector
from ml.drift.chi_square import ChiSquareDetector
from ml.drift.feature_drift import FeatureDriftAnalyzer
from ml.drift.prediction_drift import PredictionDriftAnalyzer
from ml.drift.drift_engine import DriftEngine
from ml.registry.model_registry import ModelRegistry


@pytest.fixture
def test_db(tmp_path):
    """Provides isolated SQLite database session."""
    db_file = tmp_path / "test_drift.db"
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


def test_psi_detector_no_drift():
    """Verifies PSI detector returns low score and NONE severity for identical distributions."""
    np.random.seed(42)
    ref = np.random.normal(loc=0.0, scale=1.0, size=1000)
    cur = np.random.normal(loc=0.0, scale=1.0, size=1000)

    detector = PSIDetector(num_bins=10, threshold=0.2)
    res = detector.detect(ref, cur, feature_name="amount")

    assert res.feature == "amount"
    assert res.method == "PSI"
    assert res.score < 0.1
    assert res.is_drifted is False
    assert res.severity == DriftSeverity.NONE


def test_psi_detector_with_drift():
    """Verifies PSI detector flags significant distribution shift."""
    np.random.seed(42)
    ref = np.random.normal(loc=0.0, scale=1.0, size=1000)
    cur = np.random.normal(loc=3.0, scale=1.5, size=1000)  # Significant shift

    detector = PSIDetector(num_bins=10, threshold=0.2)
    res = detector.detect(ref, cur, feature_name="amount")

    assert res.score >= 0.2
    assert res.is_drifted is True
    assert res.severity in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]


def test_ks_detector():
    """Verifies Kolmogorov-Smirnov test statistics and p-values."""
    np.random.seed(42)
    ref = np.random.normal(loc=0.0, scale=1.0, size=500)
    cur_same = np.random.normal(loc=0.0, scale=1.0, size=500)
    cur_shifted = np.random.normal(loc=2.0, scale=1.0, size=500)

    detector = KSDetector(p_value_threshold=0.05)

    res_same = detector.detect(ref, cur_same, feature_name="feature_same")
    assert res_same.is_drifted is False
    assert res_same.p_value >= 0.05

    res_shift = detector.detect(ref, cur_shifted, feature_name="feature_shifted")
    assert res_shift.is_drifted is True
    assert res_shift.p_value < 0.05


def test_jensen_shannon_detector():
    """Verifies Jensen-Shannon divergence detector."""
    np.random.seed(42)
    ref = np.random.exponential(scale=1.0, size=1000)
    cur = np.random.exponential(scale=5.0, size=1000)

    detector = JensenShannonDetector(threshold=0.1)
    res = detector.detect(ref, cur, feature_name="exp_feat")

    assert res.score > 0.1
    assert res.is_drifted is True
    assert res.severity in [DriftSeverity.MEDIUM, DriftSeverity.HIGH, DriftSeverity.CRITICAL]


def test_wasserstein_detector():
    """Verifies Wasserstein Distance / Earth Mover's Distance detector."""
    np.random.seed(42)
    ref = np.random.uniform(0, 100, size=1000)
    cur = np.random.uniform(50, 150, size=1000)

    detector = WassersteinDetector(normalized_threshold=0.1)
    res = detector.detect(ref, cur, feature_name="unif_feat")

    assert res.score >= 0.1
    assert res.is_drifted is True


def test_chi_square_detector():
    """Verifies Chi-Square test for categorical features."""
    ref_cat = ["A"] * 500 + ["B"] * 500
    cur_cat = ["A"] * 100 + ["B"] * 900  # Shifted category distribution

    detector = ChiSquareDetector(p_value_threshold=0.05)
    res = detector.detect(ref_cat, cur_cat, feature_name="device_type")

    assert res.method == "Chi-Square"
    assert res.is_drifted is True
    assert res.p_value < 0.05


def test_categorical_distribution_detector():
    """Verifies CategoricalDistributionDetector (Total Variation Distance / Distribution Difference)."""
    from ml.drift.chi_square import CategoricalDistributionDetector
    ref_cat = ["A"] * 500 + ["B"] * 500
    cur_cat = ["A"] * 100 + ["B"] * 900  # Shifted category distribution

    detector = CategoricalDistributionDetector(threshold=0.1)
    res = detector.detect(ref_cat, cur_cat, feature_name="device_type")

    assert res.method == "DistributionDifference"
    assert res.score >= 0.1
    assert res.is_drifted is True


def test_feature_drift_analyzer():
    """Verifies FeatureDriftAnalyzer handling mixed numerical and categorical DataFrame."""
    np.random.seed(42)
    ref_df = pd.DataFrame({
        "amount": np.random.normal(100, 20, 500),
        "category": np.random.choice(["X", "Y"], size=500, p=[0.5, 0.5]),
    })
    cur_df = pd.DataFrame({
        "amount": np.random.normal(300, 50, 500),  # Drifted
        "category": np.random.choice(["X", "Y"], size=500, p=[0.5, 0.5]),  # No drift
    })

    analyzer = FeatureDriftAnalyzer()
    results = analyzer.analyze_dataset(ref_df, cur_df)

    assert len(results) == 2
    res_map = {r.feature: r for r in results}

    assert res_map["amount"].is_drifted is True
    assert res_map["category"].is_drifted is False


def test_prediction_drift_analyzer():
    """Verifies prediction output probability drift detection."""
    np.random.seed(42)
    ref_probs = np.random.beta(0.5, 0.5, size=500)
    cur_probs = np.random.beta(5.0, 1.0, size=500)

    analyzer = PredictionDriftAnalyzer()
    drift_dict = analyzer.analyze(ref_probs, cur_probs)

    assert "psi" in drift_dict
    assert "ks" in drift_dict
    assert drift_dict["psi"].is_drifted is True


def test_drift_engine_execution_and_db_persistence(test_db):
    """
    Verifies DriftEngine orchestrator comparing reference vs production current window,
    computing per-feature severity, overall model status, and persisting to DB.
    """
    session, model_ver_id = test_db

    np.random.seed(42)
    ref_df = pd.DataFrame({
        "amount": np.random.normal(100, 10, 500),
        "oldbalanceOrg": np.random.normal(1000, 100, 500),
        "device": ["mobile"] * 250 + ["desktop"] * 250,
    })
    cur_df = pd.DataFrame({
        "amount": np.random.normal(500, 100, 500),  # Heavy drift
        "oldbalanceOrg": np.random.normal(1000, 100, 500),
        "device": ["mobile"] * 10 + ["desktop"] * 490,  # Heavy categorical drift
    })

    engine = DriftEngine(db=session)
    report = engine.run_drift_analysis(
        reference_data=ref_df,
        current_data=cur_df,
        model_version_id=model_ver_id,
        save_to_db=True,
    )

    assert report["overall_status"] in ["HIGH", "CRITICAL"]
    assert report["is_actionable"] is True
    assert len(report["per_feature_results"]) == 3
    assert "drift_event_id" in report

    # Verify DB persistence
    drift_event_db = session.query(DriftEvent).filter(DriftEvent.id == report["drift_event_id"]).first()
    assert drift_event_db is not None
    assert drift_event_db.overall_status in ["HIGH", "CRITICAL"]
    assert drift_event_db.is_actionable is True

    scores_db = session.query(DriftScore).filter(DriftScore.drift_event_id == drift_event_db.id).all()
    assert len(scores_db) == 3
    score_features = [s.feature_name for s in scores_db]
    assert "amount" in score_features
    assert "device" in score_features
