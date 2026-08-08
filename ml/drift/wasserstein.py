"""
Wasserstein Distance (Earth Mover's Distance) Drift Detector.
"""
import numpy as np
from scipy import stats
from ml.drift.base import BaseDriftDetector, DriftResult, DriftSeverity


class WassersteinDetector(BaseDriftDetector):
    """
    Wasserstein Distance (Earth Mover's Distance) Statistical Drift Detector.
    Measures the minimum work needed to transform one probability distribution into another.
    Threshold is normalized relative to reference standard deviation.
    """

    def __init__(self, normalized_threshold: float = 0.1):
        super().__init__(threshold=normalized_threshold)

    def detect(self, reference: np.ndarray, current: np.ndarray, feature_name: str = "feature") -> DriftResult:
        ref_arr = np.asarray(reference, dtype=float)
        cur_arr = np.asarray(current, dtype=float)

        ref_clean = ref_arr[~np.isnan(ref_arr)]
        cur_clean = cur_arr[~np.isnan(cur_arr)]

        if len(ref_clean) == 0 or len(cur_clean) == 0:
            return DriftResult(
                feature=feature_name,
                method="Wasserstein",
                score=0.0,
                threshold=self.threshold,
                severity=DriftSeverity.NONE,
                is_drifted=False,
            )

        raw_distance = float(stats.wasserstein_distance(ref_clean, cur_clean))
        ref_std = float(np.std(ref_clean))

        # Normalized distance to make threshold unit-invariant across different scale features
        if ref_std > 1e-8:
            norm_distance = float(raw_distance / ref_std)
        else:
            norm_distance = raw_distance

        is_drifted = norm_distance >= self.threshold

        if norm_distance < 0.05:
            severity = DriftSeverity.NONE
        elif norm_distance < 0.1:
            severity = DriftSeverity.LOW
        elif norm_distance < 0.2:
            severity = DriftSeverity.MEDIUM
        elif norm_distance < 0.35:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        return DriftResult(
            feature=feature_name,
            method="Wasserstein",
            score=norm_distance,
            threshold=self.threshold,
            severity=severity,
            is_drifted=is_drifted,
            details={"raw_wasserstein_distance": raw_distance, "reference_std": ref_std},
        )
