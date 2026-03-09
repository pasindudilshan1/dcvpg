import pandas as pd
from typing import Dict, Any
from .base_rule import BaseRule
from ..models import ValidationResult

class NullabilityRule(BaseRule):
    """
    Validates that a field does not contain nulls if it's declared nullable=False.
    """
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)  # Schema rule catches missing fields

        nullable = params.get("nullable", True)
        if nullable:
            return ValidationResult(passed=True, field=field)

        nulls = data[data[field].isna()]
        if not nulls.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="NULLABILITY_VIOLATION",
                rows_affected=len(nulls),
                sample_values=[],
                expected_value="NOT NULL"
            )

        return ValidationResult(passed=True, field=field)

class RangeRule(BaseRule):
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        min_val = params.get("min")
        max_val = params.get("max")
        
        if min_val is None and max_val is None:
            return ValidationResult(passed=True, field=field)
            
        series = data[field].dropna()
        violations = pd.Series(False, index=series.index)
        
        expected_parts = []
        if min_val is not None:
            violations = violations | (series < min_val)
            expected_parts.append(f">= {min_val}")
        if max_val is not None:
            violations = violations | (series > max_val)
            expected_parts.append(f"<= {max_val}")
            
        invalid_rows = series[violations]
        if not invalid_rows.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="RANGE_VIOLATION",
                rows_affected=len(invalid_rows),
                sample_values=invalid_rows.head(5).tolist(),
                expected_value=" and ".join(expected_parts)
            )
            
        return ValidationResult(passed=True, field=field)

class AllowedValuesRule(BaseRule):
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        allowed_values = params.get("allowed_values")
        if not allowed_values:
            return ValidationResult(passed=True, field=field)
            
        series = data[field].dropna()
        invalid_mask = ~series.isin(allowed_values)
        invalid_rows = series[invalid_mask]
        
        if not invalid_rows.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="ALLOWED_VALUES_VIOLATION",
                rows_affected=len(invalid_rows),
                sample_values=invalid_rows.unique()[:5].tolist(),
                expected_value=f"One of {allowed_values}"
            )
            
        return ValidationResult(passed=True, field=field)
