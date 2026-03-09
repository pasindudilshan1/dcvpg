import pandas as pd
from typing import Dict, Any, List
from .models import ContractSpec, ValidationReport, ValidationResult
from .rules.schema_rules import SchemaPresenceRule
from .rules.type_rules import TypeRule, FormatRule
from .rules.quality_rules import NullabilityRule, RangeRule, AllowedValuesRule
from .rules.uniqueness_rules import UniquenessRule
from .rules.freshness_rules import FreshnessRule
from .rules.custom_rule_loader import load_custom_rule
from .rules.base_rule import BaseRule

class Validator:
    def __init__(self, contract: ContractSpec, custom_rules_dir: str = None):
        self.contract = contract
        self.custom_rules_dir = custom_rules_dir
        
        # Instantiate built-in rules once per validator
        self.built_in_rules: Dict[str, BaseRule] = {
            "schema_presence": SchemaPresenceRule(),
            "type": TypeRule(),
            "format": FormatRule(),
            "nullability": NullabilityRule(),
            "range": RangeRule(),
            "allowed_values": AllowedValuesRule(),
            "uniqueness": UniquenessRule(),
            "freshness": FreshnessRule(),
        }
        
    def _execute_rule(self, rule_instance: BaseRule, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        try:
            return rule_instance.validate(data, field, params)
        except Exception as e:
            return ValidationResult(
                passed=False,
                field=field,
                violation_type="RULE_CRASH",
                rows_affected=len(data),
                sample_values=[],
                expected_value=f"Error executing rule {rule_instance.__class__.__name__}: {str(e)}"
            )

    def validate_batch(self, data: pd.DataFrame, pipeline_name: str, duration_ms: int = 0) -> ValidationReport:
        results: List[ValidationResult] = []
        
        # 1. Run standard field-level rules
        for field_spec in self.contract.schema_fields:
            field = field_spec.field
            params = field_spec.model_dump(exclude_none=True)
            
            # Sequence: Presence -> Type -> Quality
            res_presence = self._execute_rule(self.built_in_rules["schema_presence"], data, field, params)
            if not res_presence.passed:
                results.append(res_presence)
                continue # Skip further validation on missing fields
                
            for rule_key in ["type", "format", "nullability", "range", "allowed_values", "uniqueness", "freshness"]:
                res = self._execute_rule(self.built_in_rules[rule_key], data, field, params)
                if not res.passed:
                    results.append(res)
        
        # 2. Run user's custom rules
        if self.contract.custom_rules:
            for custom in self.contract.custom_rules:
                try:
                    rule_class = load_custom_rule(custom.rule, self.custom_rules_dir)
                    rule_instance = rule_class()
                    # Custom rules might operate on specific fields or the whole batch
                    # This depends on how the user implements 'validate'
                    field = custom.params.get("field", "whole_batch") if custom.params else "whole_batch"
                    res = self._execute_rule(rule_instance, data, field, custom.params or {})
                    if not res.passed:
                        results.append(res)
                except Exception as e:
                    results.append(ValidationResult(
                        passed=False, 
                        field=custom.rule, 
                        violation_type="CUSTOM_RULE_LOAD_ERROR", 
                        rows_affected=len(data),
                        expected_value=f"Successfully loaded {custom.rule}. Error: {str(e)}"
                    ))
                    
        # 3. Row count validation
        total_rows = len(data)
        if self.contract.row_count_min is not None and total_rows < self.contract.row_count_min:
            results.append(ValidationResult(
                passed=False,
                field="__row_count__",
                violation_type="ROW_COUNT_TOO_LOW",
                rows_affected=total_rows,
                expected_value=f">= {self.contract.row_count_min}",
                sample_values=[total_rows]
            ))
        if self.contract.row_count_max is not None and total_rows > self.contract.row_count_max:
            results.append(ValidationResult(
                passed=False,
                field="__row_count__",
                violation_type="ROW_COUNT_TOO_HIGH",
                rows_affected=total_rows,
                expected_value=f"<= {self.contract.row_count_max}",
                sample_values=[total_rows]
            ))

        # 4. Compile report
        failed_results = [r for r in results if not r.passed]
        violations_count = len(failed_results)
        status = "FAILED" if violations_count > 0 else "PASSED"
        
        return ValidationReport(
            pipeline_name=pipeline_name,
            contract_name=self.contract.name,
            contract_version=self.contract.version,
            status=status,
            rows_processed=total_rows,
            violations_count=violations_count,
            duration_ms=duration_ms,
            violation_details=failed_results
        )
