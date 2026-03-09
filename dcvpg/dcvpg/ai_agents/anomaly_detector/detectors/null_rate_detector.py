import logging
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class NullRateDetector:
    """
    Detects sudden spikes in null rate for individual fields using a rolling baseline.
    """

    def __init__(self, z_threshold: float = 3.0, absolute_delta_threshold: float = 0.10):
        self.z_threshold = z_threshold
        self.absolute_delta_threshold = absolute_delta_threshold

    def check(
        self,
        field: str,
        null_rate: float,
        baseline: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Returns an anomaly dict if null_rate is outside the expected range, else None.
        baseline should contain: {"mean": ..., "std": ..., "sample_count": ...}
        """
        if baseline is None:
            return None

        mean = baseline.get("mean", 0.0)
        std = baseline.get("std", 0.0)
        delta = abs(null_rate - mean)

        # Trigger if delta exceeds absolute threshold OR Z-score threshold
        if delta < self.absolute_delta_threshold:
            return None

        z_score = delta / std if std > 0 else float("inf")
        if z_score > self.z_threshold or delta > self.absolute_delta_threshold:
            return {
                "detector": "null_rate",
                "field": field,
                "anomaly_type": "NULL_RATE_SPIKE",
                "observed_null_rate": round(null_rate, 4),
                "expected_null_rate_mean": round(mean, 4),
                "expected_null_rate_std": round(std, 4),
                "z_score": round(z_score, 3) if z_score != float("inf") else None,
            }
        return None

    def update_baseline(
        self, null_rate: float, baseline: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if baseline is None:
            return {"mean": null_rate, "std": 0.0, "sample_count": 1}
        n = baseline["sample_count"]
        old_mean = baseline["mean"]
        new_mean = (old_mean * n + null_rate) / (n + 1)
        old_var = baseline["std"] ** 2
        new_var = (old_var * n + (null_rate - old_mean) * (null_rate - new_mean)) / (n + 1)
        return {"mean": new_mean, "std": new_var ** 0.5, "sample_count": n + 1}

    def compute_null_rate(self, df: pd.DataFrame, field: str) -> float:
        if field not in df.columns:
            return 1.0
        return float(df[field].isna().mean())
