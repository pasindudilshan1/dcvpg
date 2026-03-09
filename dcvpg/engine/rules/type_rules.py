import pandas as pd
from typing import Dict, Any
from .base_rule import BaseRule
from ..models import ValidationResult
import re

class TypeRule(BaseRule):
    """
    Validates that a field type matches the expected declared type.
    """
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        expected_type = params.get("type", "").lower()
        if not expected_type:
            return ValidationResult(passed=True, field=field)
            
        series = data[field].dropna()
        if series.empty:
            return ValidationResult(passed=True, field=field)
            
        def check_type(val):
            if expected_type in ("string", "text", "varchar"):
                return isinstance(val, str)
            elif expected_type in ("integer", "int"):
                try: 
                    int(val)
                    return True
                except (ValueError, TypeError):
                    return False
            elif expected_type in ("float", "double", "numeric"):
                try:
                    float(val)
                    return True
                except (ValueError, TypeError):
                    return False
            elif expected_type in ("boolean", "bool"):
                if isinstance(val, bool): return True
                val_str = str(val).lower()
                return val_str in ("true", "false", "1", "0", "yes", "no")
            elif expected_type in ("timestamp", "datetime", "date"):
                try:
                    pd.to_datetime(val)
                    return True
                except (ValueError, TypeError):
                    return False
            elif expected_type == "json":
                if isinstance(val, (dict, list)): return True
                try:
                    import json
                    json.loads(str(val))
                    return True
                except (ValueError, TypeError):
                    return False
            return True # Fallback

        invalid_mask = ~series.apply(check_type)
        invalid_rows = series[invalid_mask]
        
        if not invalid_rows.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="TYPE_MISMATCH",
                rows_affected=len(invalid_rows),
                sample_values=invalid_rows.unique()[:5].tolist(),
                expected_value=f"{expected_type}"
            )
            
        return ValidationResult(passed=True, field=field)

class FormatRule(BaseRule):
    """
    Validates string fields match a specified pattern/format (regex).
    """
    
    PATTERNS = {
        "uuid": r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        "email": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        "phone": r"^\+?[1-9]\d{1,14}$", # E.164 roughly
    }
    
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        if field not in data.columns:
            return ValidationResult(passed=True, field=field)
            
        fmt = params.get("format")
        if not fmt:
            return ValidationResult(passed=True, field=field)
            
        series = data[field].dropna().astype(str)
        if series.empty:
            return ValidationResult(passed=True, field=field)
            
        pattern = self.PATTERNS.get(fmt, fmt) # Fallback to using the format string itself as regex
        
        try:
            compiled_regex = re.compile(pattern)
        except re.error:
            return ValidationResult(passed=True, field=field) # Ignore invalid regex
            
        invalid_mask = ~series.str.match(compiled_regex)
        invalid_rows = series[invalid_mask]
        
        if not invalid_rows.empty:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="FORMAT_VIOLATION",
                rows_affected=len(invalid_rows),
                sample_values=invalid_rows.unique()[:5].tolist(),
                expected_value=f"Matches format: {fmt}"
            )
            
        return ValidationResult(passed=True, field=field)
