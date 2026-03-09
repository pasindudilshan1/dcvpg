# Contract Authoring Guide

A DCVPG contract is a YAML file describing the **expected schema, quality rules, and ownership** of a data pipeline's output. Contracts live in your `contracts/` directory.

## Minimal Contract

```yaml
contract:
  name: orders_raw
  version: "1.0"
  owner_team: data-engineering
  source_owner: backend-team
  source_connection: postgres_main
  source_table: orders
  schema:
    - field: id
      type: integer
      nullable: false
      unique: true
    - field: status
      type: string
      nullable: false
```

## Full Contract Reference

```yaml
contract:
  # ── Identity ────────────────────────────────────────────
  name: orders_raw             # Unique contract identifier
  version: "1.2"               # Semantic version (bump on breaking changes)
  description: "Raw orders …"  # Human-readable description

  # ── Ownership ───────────────────────────────────────────
  owner_team: data-engineering  # Team responsible for this contract
  source_owner: backend-team    # Team that produces this data source
  pipeline_tags: [crm, revenue] # Optional tags for grouping

  # ── Source ──────────────────────────────────────────────
  source_connection: postgres_main   # Must match a connection in dcvpg.config.yaml
  source_table: orders               # Table/file/endpoint to read from

  # ── Row-Count SLA ───────────────────────────────────────
  row_count_min: 1000   # Raise ROW_COUNT_TOO_LOW if fewer rows
  row_count_max: 5000000 # Raise ROW_COUNT_TOO_HIGH if more rows

  # ── Freshness ───────────────────────────────────────────
  sla_freshness_hours: 6  # Source must be updated within N hours

  # ── Schema Fields ───────────────────────────────────────
  schema:
    - field: id
      type: integer         # integer | float | string | timestamp | boolean
      nullable: false
      unique: true          # All values must be distinct

    - field: status
      type: string
      nullable: false
      allowed_values: ["active", "inactive", "pending"]

    - field: amount
      type: float
      nullable: true
      min: 0.0
      max: 999999.99

    - field: email
      type: string
      nullable: false
      format: email         # Regex-based format validation

    - field: created_at
      type: timestamp
      nullable: false

    - field: category
      type: string
      nullable: true
      min_length: 2
      max_length: 50

  # ── Custom Rules ────────────────────────────────────────
  custom_rules:
    - rule: my_project.custom_rules.NoWeekendOrders
      params:
        date_field: created_at
```

## Field Types

| Type      | Description                             | Example values          |
|-----------|-----------------------------------------|------------------------|
| integer   | Whole numbers (int32/int64)             | 1, 42, -7              |
| float     | Decimal numbers                         | 3.14, 0.001            |
| string    | Text                                    | "Alice", "active"      |
| boolean   | True/False                              | true, false, 1, 0      |
| timestamp | Date+time (ISO 8601 or datetime dtype)  | 2024-01-15T10:30:00Z   |

## Field-Level Rules

| Rule key          | Trigger                                            |
|-------------------|----------------------------------------------------|
| `nullable: false` | Any NULL in the column                             |
| `unique: true`    | Duplicate values                                   |
| `min` / `max`     | Numeric value outside range                        |
| `min_length` / `max_length` | String length outside range              |
| `allowed_values`  | Value not in the whitelist                         |
| `format`          | String doesn't match the regex pattern             |

## Versioning

- **Patch** (1.0 → 1.0.1): Add optional fields, relax constraints
- **Minor** (1.0 → 1.1): Add required fields (backward-compatible)
- **Major** (1.0 → 2.0): Remove fields, rename, tighten types (breaking)

When you make a breaking change, the AutoHealer agent will detect drift and open a PR automatically.
