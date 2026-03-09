import pandas as pd
from typing import Dict, Any
from .base_rule import BaseRule
from ..models import ValidationResult

class FreshnessRule(BaseRule):
    """
    Validates that a timestamp field is not older than the acceptable SLA window.
    """
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        sla_hours = params.get("sla_freshness_hours")
        if not sla_hours:
            return ValidationResult(passed=True, field=field)
            
        series = pd.to_datetime(data[field], errors='coerce').dropna()
        if series.empty:
            return ValidationResult(passed=True, field=field)
            
        now = pd.Timestamp.utcnow()
        if series.dt.tz is None:
            now = now.tz_localize(None) # Make timezone-naive for comparison
            
        threshold = now - pd.Timedelta(hours=sla_hours)
        
        stale_data = series[series < threshold]
        
        if not stale_data.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="FRESHNESS_VIOLATION",
                rows_affected=len(stale_data),
                sample_values=stale_data.dt.strftime('%Y-%m-%dT%H:%M:%S').unique()[:5].tolist(),
                expected_value=f"Within last {sla_hours} hours (> {threshold.strftime('%Y-%m-%dT%H:%M:%S')})"
            )
            
        return ValidationResult(passed=True, field=field)
