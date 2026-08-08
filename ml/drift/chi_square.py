"""
Chi-Square Test for Categorical Feature Drift.
"""
from typing import Union, List, Any
import numpy as np
import pandas as pd
from scipy import stats
from ml.drift.base import BaseDriftDetector, DriftResult, DriftSeverity


class ChiSquareDetector(BaseDriftDetector):
    """
    Chi-Square Test of Independence for Categorical Feature Drift.
    Evaluates category distribution differences between reference and current samples.
    """

    def __init__(self, p_value_threshold: float = 0.05):
        super().__init__(threshold=p_value_threshold)

    def detect(
        self,
        reference: Union[np.ndarray, List[Any], pd.Series],
        current: Union[np.ndarray, List[Any], pd.Series],
        feature_name: str = "feature",
    ) -> DriftResult:
        ref_s = pd.Series(reference).dropna().astype(str)
        cur_s = pd.Series(current).dropna().astype(str)

        if len(ref_s) == 0 or len(cur_s) == 0:
            return DriftResult(
                feature=feature_name,
                method="Chi-Square",
                score=0.0,
                threshold=self.threshold,
                severity=DriftSeverity.NONE,
                is_drifted=False,
                p_value=1.0,
            )

        # Get unique category union
        all_categories = sorted(list(set(ref_s.unique()).union(set(cur_s.unique()))))

        ref_counts = ref_s.value_counts().reindex(all_categories, fill_value=0).values
        cur_counts = cur_s.value_counts().reindex(all_categories, fill_value=0).values

        contingency_table = np.array([ref_counts, cur_counts])

        try:
            chi2_stat, p_val, dof, _ = stats.chi2_contingency(contingency_table)
            chi2_stat = float(chi2_stat)
            p_val = float(p_val)
        except Exception:
            chi2_stat = 0.0
            p_val = 1.0

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
            method="Chi-Square",
            score=chi2_stat,
            threshold=self.threshold,
            severity=severity,
            is_drifted=is_drifted,
            p_value=p_val,
            details={"chi2_statistic": chi2_stat, "categories_count": len(all_categories)},
        )
