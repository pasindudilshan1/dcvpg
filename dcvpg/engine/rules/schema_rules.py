import pandas as pd
from typing import Dict, Any, List
from .base_rule import BaseRule
from ..models import ValidationResult

# Added here to satisfy relative imports without circular dependencies
class SchemaPresenceRule(BaseRule):
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=False, field=field, violation_type="FIELD_MISSING", rows_affected=len(data), sample_values=[], expected_value="Present in schema")
        return ValidationResult(passed=True, field=field)
