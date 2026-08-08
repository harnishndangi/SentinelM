"""
Base abstractions and data structures for SentinelML Statistical Drift Engine.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
import numpy as np


class DriftSeverity(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class DriftResult:
    """Dataclass holding statistical drift detection evaluation results."""
    feature: str
    method: str
    score: float
    threshold: float
    severity: DriftSeverity
    is_drifted: bool
    p_value: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "method": self.method,
            "score": float(round(self.score, 6)),
            "threshold": float(round(self.threshold, 6)),
            "severity": self.severity.value if isinstance(self.severity, DriftSeverity) else str(self.severity),
            "is_drifted": self.is_drifted,
            "p_value": float(round(self.p_value, 6)) if self.p_value is not None else None,
            "details": self.details,
        }


class BaseDriftDetector(ABC):
    """Abstract Base Class for statistical drift detection algorithms."""

    def __init__(self, threshold: float):
        self.threshold = threshold

    @abstractmethod
    def detect(self, reference: np.ndarray, current: np.ndarray, feature_name: str = "feature") -> DriftResult:
        """Evaluates statistical drift between reference and current feature distributions."""
        pass
