import logging
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DistributionDetector:
    """
    Detects distribution drift for numeric fields using basic statistical moments
    (mean and standard deviation) compared to a stored baseline.
    """

    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold

    def check(
        self,
        field: str,
        series: pd.Series,
        baseline: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Returns an anomaly dict if the current mean drifts beyond z_threshold * baseline_std.
        """
        if baseline is None:
            return None

        non_null = series.dropna()
        if non_null.empty:
            return None

        current_mean = float(non_null.mean())
        bl_mean = baseline.get("mean", current_mean)
        bl_std = baseline.get("std", 0.0)

        if bl_std == 0:
            return None

        z_score = abs(current_mean - bl_mean) / bl_std
        if z_score > self.z_threshold:
            return {
                "detector": "distribution",
                "field": field,
                "anomaly_type": "DISTRIBUTION_DRIFT",
                "observed_mean": round(current_mean, 6),
                "baseline_mean": round(bl_mean, 6),
                "baseline_std": round(bl_std, 6),
                "z_score": round(z_score, 3),
            }
        return None

    def update_baseline(
        self, series: pd.Series, baseline: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        non_null = series.dropna()
        if non_null.empty:
            return baseline or {}

        current_mean = float(non_null.mean())

        if baseline is None:
            return {"mean": current_mean, "std": float(non_null.std(ddof=0)), "sample_count": 1}

        n = baseline["sample_count"]
        old_mean = baseline["mean"]
        new_mean = (old_mean * n + current_mean) / (n + 1)
        old_var = baseline["std"] ** 2
        new_var = (old_var * n + (current_mean - old_mean) * (current_mean - new_mean)) / (n + 1)
        return {"mean": new_mean, "std": new_var ** 0.5, "sample_count": n + 1}
