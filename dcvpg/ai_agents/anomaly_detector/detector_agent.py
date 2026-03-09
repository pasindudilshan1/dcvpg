import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from dcvpg.engine.models import ContractSpec
from .baseline_store import BaselineStore
from .detectors.volume_detector import VolumeDetector
from .detectors.null_rate_detector import NullRateDetector
from .detectors.distribution_detector import DistributionDetector

logger = logging.getLogger(__name__)


class AnomalyDetectorAgent:
    """
    Runs statistical anomaly checks on incoming batches using per-field baselines.
    Detects: volume drift, null-rate spikes, distribution shifts.
    """

    def __init__(self, store_path: str = ".dcvpg/baselines", z_threshold: float = 3.0):
        self.store = BaselineStore(store_path)
        self.volume = VolumeDetector(z_threshold=z_threshold)
        self.null_rate = NullRateDetector(z_threshold=z_threshold)
        self.distribution = DistributionDetector(z_threshold=z_threshold)

    def detect(
        self, contract: ContractSpec, df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Run all detectors and return a list of anomaly dicts (empty = clean batch).
        Also updates baselines after detection.
        """
        anomalies: List[Dict[str, Any]] = []
        name = contract.name

        # Volume check
        row_count = len(df)
        vol_baseline = self.store.load(name, "__row_count__")
        anomaly = self.volume.check(row_count, vol_baseline)
        if anomaly:
            anomalies.append(anomaly)
        updated = self.volume.update_baseline(row_count, vol_baseline)
        self.store.save(name, "__row_count__", updated)

        # Per-field checks
        for field_spec in contract.schema_fields:
            field = field_spec.field
            if field not in df.columns:
                continue

            series = df[field]

            # Null-rate check
            null_rate = float(series.isna().mean())
            nr_baseline = self.store.load(name, f"{field}__null_rate")
            anomaly = self.null_rate.check(field, null_rate, nr_baseline)
            if anomaly:
                anomalies.append(anomaly)
            updated = self.null_rate.update_baseline(null_rate, nr_baseline)
            self.store.save(name, f"{field}__null_rate", updated)

            # Distribution check (numeric only)
            if pd.api.types.is_numeric_dtype(series):
                dist_baseline = self.store.load(name, f"{field}__dist")
                anomaly = self.distribution.check(field, series, dist_baseline)
                if anomaly:
                    anomalies.append(anomaly)
                updated = self.distribution.update_baseline(series, dist_baseline)
                self.store.save(name, f"{field}__dist", updated)

        if anomalies:
            logger.warning(
                f"AnomalyDetector found {len(anomalies)} anomaly(ies) in '{name}': "
                + ", ".join(a["anomaly_type"] for a in anomalies)
            )
        return anomalies
