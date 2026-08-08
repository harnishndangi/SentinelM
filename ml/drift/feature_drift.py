"""
Feature Drift Aggregator for Numerical and Categorical Datasets.
"""
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from ml.drift.base import DriftResult, DriftSeverity
from ml.drift.psi import PSIDetector
from ml.drift.ks import KSDetector
from ml.drift.jensen_shannon import JensenShannonDetector
from ml.drift.wasserstein import WassersteinDetector
from ml.drift.chi_square import ChiSquareDetector


class FeatureDriftAnalyzer:
    """
    Aggregates statistical drift detection across tabular features.
    Automatically applies continuous detectors (PSI, KS, Wasserstein, JS) to numerical features
    and categorical detectors (Chi-Square) to categorical features.
    """

    def __init__(
        self,
        numerical_method: str = "psi",
        categorical_method: str = "chi_square",
        psi_threshold: float = 0.2,
        ks_threshold: float = 0.05,
    ):
        self.num_method = numerical_method.lower().strip()
        self.cat_method = categorical_method.lower().strip()

        self.psi_detector = PSIDetector(threshold=psi_threshold)
        self.ks_detector = KSDetector(p_value_threshold=ks_threshold)
        self.js_detector = JensenShannonDetector(threshold=0.1)
        self.wasserstein_detector = WassersteinDetector(normalized_threshold=0.1)
        self.chi_square_detector = ChiSquareDetector(p_value_threshold=ks_threshold)

    def analyze_feature(self, ref_series: pd.Series, cur_series: pd.Series, feature_name: str) -> DriftResult:
        """Analyzes a single feature column."""
        is_numeric = pd.api.types.is_numeric_dtype(ref_series) and not pd.api.types.is_bool_dtype(ref_series)

        if is_numeric:
            if self.num_method == "ks":
                return self.ks_detector.detect(ref_series.values, cur_series.values, feature_name=feature_name)
            elif self.num_method == "jensen_shannon" or self.num_method == "js":
                return self.js_detector.detect(ref_series.values, cur_series.values, feature_name=feature_name)
            elif self.num_method == "wasserstein":
                return self.wasserstein_detector.detect(ref_series.values, cur_series.values, feature_name=feature_name)
            else:
                return self.psi_detector.detect(ref_series.values, cur_series.values, feature_name=feature_name)
        else:
            return self.chi_square_detector.detect(ref_series.values, cur_series.values, feature_name=feature_name)

    def analyze_dataset(
        self,
        reference_df: pd.DataFrame,
        current_df: pd.DataFrame,
        features: Optional[List[str]] = None,
    ) -> List[DriftResult]:
        """Analyzes all specified feature columns across reference and current DataFrames."""
        target_features = features or [c for c in reference_df.columns if c in current_df.columns]
        results: List[DriftResult] = []

        for feat in target_features:
            ref_col = reference_df[feat]
            cur_col = current_df[feat]
            res = self.analyze_feature(ref_col, cur_col, feature_name=feat)
            results.append(res)

        return results
