import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class VolumeDetector:
    """
    Detects row-count anomalies using a rolling mean ± N standard deviations baseline.
    """

    def __init__(self, z_threshold: float = 3.0):
        self.z_threshold = z_threshold

    def check(
        self,
        row_count: int,
        baseline: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Returns an anomaly dict if row_count is outside the expected range, else None.
        baseline should contain: {"mean": ..., "std": ..., "sample_count": ...}
        """
        if baseline is None:
            return None

        mean = baseline.get("mean", 0)
        std = baseline.get("std", 0)

        if std == 0:
            return None

        z_score = abs(row_count - mean) / std
        if z_score > self.z_threshold:
            direction = "LOW" if row_count < mean else "HIGH"
            return {
                "detector": "volume",
                "field": "__row_count__",
                "anomaly_type": f"VOLUME_{direction}",
                "observed": row_count,
                "expected_mean": mean,
                "expected_std": std,
                "z_score": round(z_score, 3),
            }
        return None

    def update_baseline(
        self, row_count: int, baseline: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Incrementally update the rolling baseline with a new observation."""
        if baseline is None:
            return {"mean": row_count, "std": 0.0, "sample_count": 1}

        n = baseline["sample_count"]
        old_mean = baseline["mean"]
        new_mean = (old_mean * n + row_count) / (n + 1)
        # Welford's online variance update
        old_var = baseline["std"] ** 2
        new_var = (old_var * n + (row_count - old_mean) * (row_count - new_mean)) / (n + 1)
        return {
            "mean": new_mean,
            "std": new_var ** 0.5,
            "sample_count": n + 1,
        }
