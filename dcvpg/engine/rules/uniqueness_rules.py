import pandas as pd
from typing import Dict, Any
from .base_rule import BaseRule
from ..models import ValidationResult

class UniquenessRule(BaseRule):
    """
    Validates that a field declared as unique contains no duplicates.
    """
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        unique = params.get("unique", False)
        if not unique:
            return ValidationResult(passed=True, field=field)
            
        series = data[field].dropna()
        if series.empty:
            return ValidationResult(passed=True, field=field)
            
        duplicates = series[series.duplicated(keep=False)]
        
        if not duplicates.empty:
            try:
                sample_values = duplicates.unique()[:5].tolist()
            except TypeError:
                sample_values = duplicates.apply(str).unique()[:5].tolist()
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="UNIQUENESS_VIOLATION",
                rows_affected=len(duplicates),
                sample_values=sample_values,
                expected_value="Unique values"
            )
            
        return ValidationResult(passed=True, field=field)
