# Custom Rules Guide

DCVPG's built-in rule set covers the most common validation patterns (nullability, ranges, allowed values, formats, uniqueness). For business-specific logic that goes beyond these, you can write custom rules in plain Python and reference them directly in your contract YAML.

---

## How It Works

1. Write a Python class that extends `BaseRule`
2. Place it in your project's `custom_rules/` directory
3. Register the directory in `dcvpg.config.yaml`
4. Reference the class in the contract's `custom_rules` block

---

## Step 1 — Create the Rule File

```bash
# From your project directory (created by dcvpg init)
cp custom_rules/example_rule.py custom_rules/no_weekend_orders.py
```

---

## Step 2 — Implement the Rule

```python
# custom_rules/no_weekend_orders.py
import pandas as pd
from dcvpg.engine.rules.base_rule import BaseRule
from dcvpg.engine.models import ValidationResult


class NoWeekendOrders(BaseRule):
    """Orders must never be placed on a Saturday or Sunday."""

    def validate(self, data: pd.DataFrame, field: str, params: dict) -> ValidationResult:
        date_col = params.get("date_field", field)

        # Guard: column must exist
        if date_col not in data.columns:
            return ValidationResult(
                passed=False,
                field=date_col,
                violation_type="FIELD_MISSING",
                rows_affected=len(data),
                expected_value=f"Column '{date_col}' must exist in the DataFrame",
            )

        dates = pd.to_datetime(data[date_col], errors="coerce")
        weekend_mask = dates.dt.dayofweek >= 5   # 5 = Saturday, 6 = Sunday
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

---

## Step 3 — Register the Directory in Config

```yaml
# dcvpg.config.yaml
extensions:
  custom_rules_dir: ./custom_rules
```

---

## Step 4 — Reference in the Contract

```yaml
custom_rules:
  - rule: no_weekend_orders.NoWeekendOrders   # <module_file>.<ClassName>
    params:
      date_field: created_at
```

The `rule` value is `<filename_without_py>.<ClassName>`, resolved relative to `custom_rules_dir`.

---

## BaseRule Interface

Your class must extend `BaseRule` and implement one method:

```python
class BaseRule:
    def validate(
        self,
        data: pd.DataFrame,   # Full batch DataFrame being validated
        field: str,           # Field name from the contract schema
        params: dict,         # Params dict from the contract's custom_rules entry
    ) -> ValidationResult:
        ...
```

### ValidationResult Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `passed` | `bool` | Yes | `True` if validation passed |
| `field` | `str` | Yes | Field the violation applies to |
| `violation_type` | `str` | When failing | Short uppercase identifier, e.g. `WEEKEND_ORDER_FOUND` |
| `rows_affected` | `int` | When failing | Number of rows that triggered the violation |
| `expected_value` | `str` | When failing | Human-readable description of what was expected |
| `sample_values` | `list` | No | Up to 5 sample violating values for the report |

---

## Testing Your Rule

Always write a unit test alongside your rule:

```python
# tests/test_no_weekend_orders.py
import pandas as pd
from custom_rules.no_weekend_orders import NoWeekendOrders


def test_passes_on_weekdays():
    rule = NoWeekendOrders()
    df = pd.DataFrame({"created_at": ["2026-03-09", "2026-03-10"]})  # Mon, Tue
    result = rule.validate(df, "created_at", {"date_field": "created_at"})
    assert result.passed


def test_fails_on_weekend():
    rule = NoWeekendOrders()
    df = pd.DataFrame({"created_at": ["2026-03-07", "2026-03-08"]})  # Sat, Sun
    result = rule.validate(df, "created_at", {"date_field": "created_at"})
    assert not result.passed
    assert result.violation_type == "WEEKEND_ORDER_FOUND"
    assert result.rows_affected == 2


def test_fails_on_missing_column():
    rule = NoWeekendOrders()
    df = pd.DataFrame({"amount": [100, 200]})
    result = rule.validate(df, "created_at", {"date_field": "created_at"})
    assert not result.passed
    assert result.violation_type == "FIELD_MISSING"
```

Run with:
```bash
pytest tests/test_no_weekend_orders.py -v
```

---

## Built-in Violation Types Reference

| Violation type | Description |
|---|---|
| `FIELD_MISSING` | Required column not present in the DataFrame |
| `TYPE_MISMATCH` | Column dtype does not match the contract-declared type |
| `NULL_VALUES_FOUND` | Null values found in a `nullable: false` field |
| `INVALID_VALUE` | Value not in the `allowed_values` whitelist |
| `OUT_OF_RANGE` | Numeric value outside `min` / `max` bounds |
| `UNIQUE_VIOLATION` | Duplicate values in a `unique: true` field |
| `FORMAT_MISMATCH` | String does not match the `format` regex pattern |
| `STALE_DATA` | Source not refreshed within `sla_freshness_hours` |
| `ROW_COUNT_TOO_LOW` | Batch has fewer rows than `row_count_min` |
| `ROW_COUNT_TOO_HIGH` | Batch has more rows than `row_count_max` |

Use these same strings in your custom rules' `violation_type` field for consistent reporting in the dashboard and alerts.

---

## Tips

- Keep each rule in its own file named after the rule (snake_case)
- Rules receive the **full** DataFrame — you can reference multiple columns in one rule
- Use `params` to make rules configurable — avoid hardcoding thresholds inside the class
- Return early from `validate()` with a clear `FIELD_MISSING` result if a required column is absent, to avoid confusing errors downstream
