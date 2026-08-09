"""
Stream Concept Drift Detectors using River algorithms:
- ADWIN (Adaptive Windowing)
- Page-Hinkley
- DDM (Drift Detection Method for binary error streams)

Concept Drift monitors P(Y|X) - the relationship between input features X and target outcomes Y.
Evaluates stream prediction errors when delayed ground truth labels become available.
"""
from typing import Dict, Any, Optional, Tuple
import numpy as np

try:
    from river import drift
    from river.drift import binary
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False

from ml.drift.base import DriftSeverity


class ADWINDetector:
    """
    ADWIN (Adaptive Windowing) Concept Drift Detector.
    Maintains an adaptive sliding window of variable length.
    Automatically shrinks when statistical drift is detected in the stream.
    """

    def __init__(self, delta: float = 0.002):
        self.delta = delta
        if RIVER_AVAILABLE:
            self.detector = drift.ADWIN(delta=delta)
        else:
            self.detector = None

    def update(self, val: float) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        Updates ADWIN with a new stream observation (e.g. error |y - p|).
        Returns (drift_detected, warning_detected, details).
        """
        if self.detector is None:
            return False, False, {"error": "River library not available"}

        self.detector.update(val)
        drift_detected = self.detector.drift_detected
        warning_detected = getattr(self.detector, "warning_detected", False)

        details = {
            "width": getattr(self.detector, "width", 0),
            "variance": getattr(self.detector, "variance", 0.0),
            "delta": self.delta,
        }
        return drift_detected, warning_detected, details


class PageHinkleyDetector:
    """
    Page-Hinkley Sequential Analysis Change Detector.
    Monitors changes in the mean of a continuous error stream.
    """

    def __init__(self, min_instances: int = 30, threshold: float = 50.0, delta: float = 0.005, alpha: float = 0.9999):
        self.min_instances = min_instances
        self.threshold = threshold
        self.delta = delta
        self.alpha = alpha

        if RIVER_AVAILABLE:
            self.detector = drift.PageHinkley(
                min_instances=min_instances,
                threshold=threshold,
                delta=delta,
                alpha=alpha,
            )
        else:
            self.detector = None

    def update(self, val: float) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        Updates Page-Hinkley with a continuous stream value.
        Returns (drift_detected, warning_detected, details).
        """
        if self.detector is None:
            return False, False, {"error": "River library not available"}

        self.detector.update(val)
        drift_detected = self.detector.drift_detected
        warning_detected = getattr(self.detector, "warning_detected", False)

        details = {
            "threshold": self.threshold,
            "delta": self.delta,
        }
        return drift_detected, warning_detected, details


class DDMDetector:
    """
    DDM (Drift Detection Method) for Binary Error Streams.
    Tracks error rate p and standard deviation s.
    Triggers Warning when p + s >= p_min + 2 * s_min and Drift when p + s >= p_min + 3 * s_min.
    """

    def __init__(self, min_num_instances: int = 30, warning_threshold: float = 2.0, drift_threshold: float = 3.0):
        self.min_num_instances = min_num_instances
        self.warning_threshold = warning_threshold
        self.drift_threshold = drift_threshold

        if RIVER_AVAILABLE:
            try:
                self.detector = binary.DDM(
                    warm_start=min_num_instances,
                    warning_threshold=warning_threshold,
                    drift_threshold=drift_threshold,
                )
            except TypeError:
                self.detector = binary.DDM(
                    min_num_instances=min_num_instances,
                    warning_threshold=warning_threshold,
                    drift_threshold=drift_threshold,
                )
        else:
            self.detector = None

    def update(self, is_error: bool) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        Updates DDM with a binary error observation (True if prediction != true label).
        Returns (drift_detected, warning_detected, details).
        """
        if self.detector is None:
            return False, False, {"error": "River library not available"}

        self.detector.update(bool(is_error))
        drift_detected = self.detector.drift_detected
        warning_detected = getattr(self.detector, "warning_detected", False)

        details = {
            "min_num_instances": self.min_num_instances,
            "p": getattr(self.detector, "p", 0.0),
            "s": getattr(self.detector, "s", 0.0),
        }
        return drift_detected, warning_detected, details


class ConceptDriftMonitor:
    """
    High-level Concept Drift Monitor orchestrating ADWIN, Page-Hinkley, and DDM detectors concurrently.
    """

    def __init__(
        self,
        adwin_delta: float = 0.002,
        ph_threshold: float = 50.0,
        ddm_min_instances: int = 30,
    ):
        self.adwin = ADWINDetector(delta=adwin_delta)
        self.page_hinkley = PageHinkleyDetector(threshold=ph_threshold)
        self.ddm = DDMDetector(min_num_instances=ddm_min_instances)

    def update(self, error_val: float, is_binary_error: bool) -> Dict[str, Any]:
        """
        Updates all stream concept drift detectors with the new ground truth prediction error signal.
        """
        adwin_drift, adwin_warn, adwin_det = self.adwin.update(error_val)
        ph_drift, ph_warn, ph_det = self.page_hinkley.update(error_val)
        ddm_drift, ddm_warn, ddm_det = self.ddm.update(is_binary_error)

        drift_detected = adwin_drift or ph_drift or ddm_drift
        warning_detected = adwin_warn or ph_warn or ddm_warn

        if adwin_drift and ddm_drift:
            severity = DriftSeverity.CRITICAL
        elif drift_detected:
            severity = DriftSeverity.HIGH
        elif warning_detected:
            severity = DriftSeverity.MEDIUM
        else:
            severity = DriftSeverity.NONE

        return {
            "drift_detected": drift_detected,
            "warning_detected": warning_detected,
            "severity": severity.value,
            "is_actionable": drift_detected,
            "detectors": {
                "ADWIN": {"drift": adwin_drift, "warning": adwin_warn, "details": adwin_det},
                "PageHinkley": {"drift": ph_drift, "warning": ph_warn, "details": ph_det},
                "DDM": {"drift": ddm_drift, "warning": ddm_warn, "details": ddm_det},
            },
        }
