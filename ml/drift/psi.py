"""
Population Stability Index (PSI) Drift Detector.
"""
from typing import Optional
import numpy as np
from ml.drift.base import BaseDriftDetector, DriftResult, DriftSeverity


class PSIDetector(BaseDriftDetector):
    """
    Population Stability Index (PSI) Statistical Drift Detector.
    
    Formula:
        PSI = sum((Actual_i - Expected_i) * ln(Actual_i / Expected_i))
        
    Threshold benchmarks:
        PSI < 0.1: No significant distribution change (NONE)
        0.1 <= PSI < 0.2: Slight shift (LOW / MEDIUM)
        PSI >= 0.2: Significant population shift (HIGH / CRITICAL)
    """

    def __init__(self, num_bins: int = 10, threshold: float = 0.2, eps: float = 1e-4):
        super().__init__(threshold=threshold)
        self.num_bins = num_bins
        self.eps = eps

    def detect(self, reference: np.ndarray, current: np.ndarray, feature_name: str = "feature") -> DriftResult:
        ref_arr = np.asarray(reference, dtype=float)
        cur_arr = np.asarray(current, dtype=float)

        # Remove NaNs
        ref_clean = ref_arr[~np.isnan(ref_arr)]
        cur_clean = cur_arr[~np.isnan(cur_arr)]

        if len(ref_clean) == 0 or len(cur_clean) == 0:
            return DriftResult(
                feature=feature_name,
                method="PSI",
                score=0.0,
                threshold=self.threshold,
                severity=DriftSeverity.NONE,
                is_drifted=False,
            )

        # Quantile bin edges based on reference distribution
        percentiles = np.linspace(0, 100, self.num_bins + 1)
        bin_edges = np.percentile(ref_clean, percentiles)
        bin_edges = np.unique(bin_edges)  # handle duplicates

        if len(bin_edges) < 2:
            bin_edges = np.linspace(ref_clean.min(), ref_clean.max() + 1e-5, self.num_bins + 1)

        # Add inf margins to catch outliers
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        # Calculate counts per bin
        ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
        cur_counts, _ = np.histogram(cur_clean, bins=bin_edges)

        # Calculate relative frequencies with epsilon smoothing
        ref_props = ref_counts / len(ref_clean)
        cur_props = cur_counts / len(cur_clean)

        ref_props = np.where(ref_props == 0, self.eps, ref_props)
        cur_props = np.where(cur_props == 0, self.eps, cur_props)

        # Calculate PSI
        psi_value = float(np.sum((cur_props - ref_props) * np.log(cur_props / ref_props)))

        # Assign severity based on standard PSI benchmarks
        if psi_value < 0.1:
            severity = DriftSeverity.NONE
            is_drifted = False
        elif psi_value < 0.2:
            severity = DriftSeverity.LOW
            is_drifted = True
        elif psi_value < 0.3:
            severity = DriftSeverity.MEDIUM
            is_drifted = True
        elif psi_value < 0.5:
            severity = DriftSeverity.HIGH
            is_drifted = True
        else:
            severity = DriftSeverity.CRITICAL
            is_drifted = True

        return DriftResult(
            feature=feature_name,
            method="PSI",
            score=psi_value,
            threshold=self.threshold,
            severity=severity,
            is_drifted=is_drifted,
            details={"bins_used": len(bin_edges) - 1, "num_reference": len(ref_clean), "num_current": len(cur_clean)},
        )
