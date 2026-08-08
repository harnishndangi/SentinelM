"""
Jensen-Shannon Divergence Drift Detector.
"""
import numpy as np
from scipy.spatial.distance import jensenshannon
from ml.drift.base import BaseDriftDetector, DriftResult, DriftSeverity


class JensenShannonDetector(BaseDriftDetector):
    """
    Jensen-Shannon Divergence Statistical Drift Detector.
    Symmetric and bounded version of Kullback-Leibler (KL) divergence.
    Output range: [0.0, 1.0].
    """

    def __init__(self, num_bins: int = 20, threshold: float = 0.1):
        super().__init__(threshold=threshold)
        self.num_bins = num_bins

    def detect(self, reference: np.ndarray, current: np.ndarray, feature_name: str = "feature") -> DriftResult:
        ref_arr = np.asarray(reference, dtype=float)
        cur_arr = np.asarray(current, dtype=float)

        ref_clean = ref_arr[~np.isnan(ref_arr)]
        cur_clean = cur_arr[~np.isnan(cur_arr)]

        if len(ref_clean) == 0 or len(cur_clean) == 0:
            return DriftResult(
                feature=feature_name,
                method="Jensen-Shannon",
                score=0.0,
                threshold=self.threshold,
                severity=DriftSeverity.NONE,
                is_drifted=False,
            )

        combined = np.concatenate([ref_clean, cur_clean])
        min_val, max_val = combined.min(), combined.max()

        if min_val == max_val:
            bins = np.array([min_val - 0.5, min_val + 0.5])
        else:
            bins = np.linspace(min_val, max_val, self.num_bins + 1)

        ref_hist, _ = np.histogram(ref_clean, bins=bins, density=True)
        cur_hist, _ = np.histogram(cur_clean, bins=bins, density=True)

        # Normalize to probability distributions
        p = ref_hist / np.sum(ref_hist) if np.sum(ref_hist) > 0 else ref_hist
        q = cur_hist / np.sum(cur_hist) if np.sum(cur_hist) > 0 else cur_hist

        js_distance = float(jensenshannon(p, q))
        js_divergence = float(js_distance ** 2)

        is_drifted = js_divergence >= self.threshold

        if js_divergence < 0.05:
            severity = DriftSeverity.NONE
        elif js_divergence < 0.1:
            severity = DriftSeverity.LOW
        elif js_divergence < 0.2:
            severity = DriftSeverity.MEDIUM
        elif js_divergence < 0.35:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        return DriftResult(
            feature=feature_name,
            method="Jensen-Shannon",
            score=js_divergence,
            threshold=self.threshold,
            severity=severity,
            is_drifted=is_drifted,
            details={"js_distance": js_distance, "js_divergence": js_divergence},
        )
