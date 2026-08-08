"""
Kolmogorov-Smirnov (KS) 2-Sample Statistical Test Drift Detector.
"""
import numpy as np
from scipy import stats
from ml.drift.base import BaseDriftDetector, DriftResult, DriftSeverity


class KSDetector(BaseDriftDetector):
    """
    Two-sample Kolmogorov-Smirnov statistical test for continuous distributions.
    Measures the maximum distance between two empirical cumulative distribution functions (eCDF).
    """

    def __init__(self, p_value_threshold: float = 0.05):
        super().__init__(threshold=p_value_threshold)

    def detect(self, reference: np.ndarray, current: np.ndarray, feature_name: str = "feature") -> DriftResult:
        ref_arr = np.asarray(reference, dtype=float)
        cur_arr = np.asarray(current, dtype=float)

        ref_clean = ref_arr[~np.isnan(ref_arr)]
        cur_clean = cur_arr[~np.isnan(cur_arr)]

        if len(ref_clean) < 2 or len(cur_clean) < 2:
            return DriftResult(
                feature=feature_name,
                method="KS",
                score=0.0,
                threshold=self.threshold,
                severity=DriftSeverity.NONE,
                is_drifted=False,
                p_value=1.0,
            )

        res = stats.ks_2samp(ref_clean, cur_clean)
        ks_stat = float(res.statistic)
        p_val = float(res.pvalue)

        # Evaluate drift based on p-value threshold
        is_drifted = p_val < self.threshold

        if p_val >= self.threshold:
            severity = DriftSeverity.NONE
        elif p_val >= 0.01:
            severity = DriftSeverity.LOW
        elif p_val >= 0.001:
            severity = DriftSeverity.MEDIUM
        elif p_val >= 1e-5:
            severity = DriftSeverity.HIGH
        else:
            severity = DriftSeverity.CRITICAL

        return DriftResult(
            feature=feature_name,
            method="KS",
            score=ks_stat,
            threshold=self.threshold,
            severity=severity,
            is_drifted=is_drifted,
            p_value=p_val,
            details={"ks_statistic": ks_stat, "p_value": p_val},
        )
