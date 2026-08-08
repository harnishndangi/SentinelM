"""
Prediction Drift Detector for Model Output Probability Distributions.
"""
from typing import Dict, Any
import numpy as np
from ml.drift.base import DriftResult
from ml.drift.psi import PSIDetector
from ml.drift.ks import KSDetector


class PredictionDriftAnalyzer:
    """
    Evaluates distribution drift on model output prediction probabilities over time.
    Compares baseline/reference predicted probabilities against production current window probabilities.
    """

    def __init__(self, psi_threshold: float = 0.1, ks_threshold: float = 0.05):
        self.psi_detector = PSIDetector(num_bins=10, threshold=psi_threshold)
        self.ks_detector = KSDetector(p_value_threshold=ks_threshold)

    def analyze(self, ref_probabilities: np.ndarray, cur_probabilities: np.ndarray) -> Dict[str, DriftResult]:
        """Analyzes prediction probability distributions using PSI and KS test."""
        psi_res = self.psi_detector.detect(ref_probabilities, cur_probabilities, feature_name="prediction_probability")
        ks_res = self.ks_detector.detect(ref_probabilities, cur_probabilities, feature_name="prediction_probability")

        return {
            "psi": psi_res,
            "ks": ks_res,
        }
