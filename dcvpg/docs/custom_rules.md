# Custom Rules Guide

DCVPG allows you to write custom validation rules in plain Python, extending the built-in rule set.

## 1. Create a Rule File

```bash
# Use the scaffold template
cp dcvpg/templates/custom_rule.py.template my_project/custom_rules/no_weekend_orders.py
```

## 2. Implement the Rule

```python
# my_project/custom_rules/no_weekend_orders.py
import pandas as pd
from dcvpg.engine.rules.base_rule import BaseRule
from dcvpg.engine.models import ValidationResult


class NoWeekendOrders(BaseRule):
    """Orders should never be placed on weekends."""

    def validate(self, data: pd.DataFrame, field: str, params: dict) -> ValidationResult:
        date_col = params.get("date_field", field)

        if date_col not in data.columns:
            return ValidationResult(
                passed=False,
                field=date_col,
                violation_type="FIELD_MISSING",
                rows_affected=len(data),
                expected_value=f"Column '{date_col}' must exist",
            )

        dates = pd.to_datetime(data[date_col], errors="coerce")
        weekend_mask = dates.dt.dayofweek >= 5  # 5=Sat, 6=Sun
        weekend_count = int(weekend_mask.sum())

        if weekend_count > 0:
            return ValidationResult(
                passed=False,
                field=date_col,
                violation_type="WEEKEND_ORDER_FOUND",
                rows_affected=weekend_count,
                expected_value="Orders must be placed on weekdays (Mon–Fri)",
                sample_values=data.loc[weekend_mask, date_col].head(3).tolist(),
            )

        return ValidationResult(passed=True, field=date_col)
```

## 3. Register in Config

```yaml
extensions:
  custom_rules_dir: ./custom_rules
```

## 4. Reference in Contract

```yaml
custom_rules:
  - rule: no_weekend_orders.NoWeekendOrders
    params:
      date_field: created_at
```

The `rule` value is `<module>.<ClassName>` relative to the `custom_rules_dir`.

## BaseRule Interface

```python
class BaseRule:
    def validate(
        self,
        data: pd.DataFrame,
        field: str,
        params: dict,
    ) -> ValidationResult:
        ...
```

Your rule receives the full DataFrame, the field name (from the contract YAML), and the params dict. Return a `ValidationResult` with `passed=True` for clean data or `passed=False` with violation details.

## Testing Your Rule

```python
import pandas as pd
from my_project.custom_rules.no_weekend_orders import NoWeekendOrders

def test_no_weekend_orders():
    rule = NoWeekendOrders()
    df = pd.DataFrame({"created_at": ["2024-01-06", "2024-01-07"]})  # Sat, Sun
    result = rule.validate(df, "created_at", {"date_field": "created_at"})
    assert not result.passed
    assert result.violation_type == "WEEKEND_ORDER_FOUND"
    assert result.rows_affected == 2
```

## Built-in Violation Types Reference

| Violation Type         | Description                          |
|------------------------|--------------------------------------|
| `FIELD_MISSING`        | Required column not in DataFrame     |
| `TYPE_MISMATCH`        | Column dtype doesn't match contract  |
| `NULL_VALUES_FOUND`    | Nulls in non-nullable field          |
| `INVALID_VALUE`        | Value not in `allowed_values`        |
| `OUT_OF_RANGE`         | Value outside `min`/`max`            |
| `UNIQUE_VIOLATION`     | Duplicate values in `unique: true` field |
| `FORMAT_MISMATCH`      | String doesn't match regex `format`  |
| `STALE_DATA`           | Source not refreshed within SLA      |
| `ROW_COUNT_TOO_LOW`    | Batch has fewer rows than `row_count_min` |
| `ROW_COUNT_TOO_HIGH`   | Batch has more rows than `row_count_max` |
