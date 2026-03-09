# Contract Authoring Guide

A DCVPG contract is a YAML file that describes the **expected schema, quality rules, SLAs, and ownership** of a data asset. Contracts are the source of truth DCVPG validates against — keep them in version control alongside your pipeline code.

Contracts live in your project's `contracts/` directory and are registered with `dcvpg register <file>`.

---

---

## Minimal Contract

The only required fields are `name`, `source_connection`, `source_table`, and at least one `schema` entry:

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

Register it:

```bash
dcvpg register contracts/services/orders_raw.yaml
```

---

## Full Contract Reference

```yaml
contract:
  # ── Identity ────────────────────────────────────────────
  name: orders_raw               # Unique contract identifier (used in CLI commands)
  version: "1.2"                 # Semantic version — bump on every change
  description: "Raw orders from the e-commerce backend."

  # ── Ownership ───────────────────────────────────────────
  owner_team: data-engineering   # Team responsible for enforcing this contract
  source_owner: backend-team     # Team that produces the upstream data
  pipeline_tags: [crm, revenue]  # Optional — used for grouping/filtering in the dashboard

  # ── Source ──────────────────────────────────────────────
  source_connection: postgres_main   # Must match a connection name in dcvpg.config.yaml
  source_table: orders               # Table name, file path, or API endpoint

  # ── Row-Count SLA ───────────────────────────────────────
  row_count_min: 1000        # Violation: ROW_COUNT_TOO_LOW if fewer rows arrive
  row_count_max: 5000000     # Violation: ROW_COUNT_TOO_HIGH if more rows arrive

  # ── Freshness SLA ───────────────────────────────────────
  sla_freshness_hours: 6     # Violation: STALE_DATA if source not updated within N hours

  # ── Schema Fields ───────────────────────────────────────
  schema:
    - field: id
      type: integer        # integer | float | string | timestamp | boolean
      nullable: false
      unique: true         # All values must be distinct → UNIQUE_VIOLATION if duplicates found

    - field: status
      type: string
      nullable: false
      allowed_values: ["active", "inactive", "pending"]  # INVALID_VALUE if not in list

    - field: amount
      type: float
      nullable: true
      min: 0.0             # OUT_OF_RANGE if value < min
      max: 999999.99       # OUT_OF_RANGE if value > max

    - field: email
      type: string
      nullable: false
      format: email        # FORMAT_MISMATCH if string does not match the email regex

    - field: created_at
      type: timestamp
      nullable: false

    - field: category
      type: string
      nullable: true
      min_length: 2        # FORMAT_MISMATCH if string shorter than this
      max_length: 50       # FORMAT_MISMATCH if string longer than this

  # ── Custom Rules ────────────────────────────────────────
  custom_rules:
    - rule: no_weekend_orders.NoWeekendOrders   # <module>.<ClassName> relative to custom_rules_dir
      params:
        date_field: created_at
```

---

## Field Types

| Type | Description | Accepted values |
|---|---|---|
| `integer` | Whole numbers (int32/int64) | `1`, `42`, `-7` |
| `float` | Decimal numbers | `3.14`, `0.001` |
| `string` | Text | `"Alice"`, `"active"` |
| `boolean` | True/False | `true`, `false`, `1`, `0` |
| `timestamp` | Date + time (ISO 8601 or datetime dtype) | `2024-01-15T10:30:00Z` |

---

## Field-Level Rules Reference

| Rule key | Violation type raised | Description |
|---|---|---|
| `nullable: false` | `NULL_VALUES_FOUND` | Any NULL in the column fails |
| `unique: true` | `UNIQUE_VIOLATION` | Duplicate values fail |
| `min` / `max` | `OUT_OF_RANGE` | Numeric value outside the specified range |
| `min_length` / `max_length` | `FORMAT_MISMATCH` | String length outside the specified range |
| `allowed_values` | `INVALID_VALUE` | Value not present in the whitelist |
| `format: email` | `FORMAT_MISMATCH` | String does not match the built-in email regex |
| `format: <regex>` | `FORMAT_MISMATCH` | String does not match the custom regex pattern |

---

## Built-in Format Patterns

The `format` key accepts either a named pattern or a raw regex:

| Named pattern | Matches |
|---|---|
| `email` | Standard email address |
| `uuid` | UUID v4 |
| `url` | HTTP/HTTPS URL |
| `date` | `YYYY-MM-DD` |
| `iso_datetime` | ISO 8601 datetime |
| `phone` | International phone number |
| Any regex string | Custom pattern, e.g. `"^\d{5}$"` for US zip codes |

---

## Contract Versioning

Follow [Semantic Versioning](https://semver.org/) for contracts:

| Change type | Version bump | Example | Notes |
|---|---|---|---|
| Add optional field or relax constraint | Patch | `1.0` → `1.0.1` | Non-breaking |
| Add required field | Minor | `1.0` → `1.1` | Backward-compatible |
| Remove field, rename, tighten type | Major | `1.0` → `2.0` | **Breaking** — triggers Auto-Healer |

When a breaking change is detected by `dcvpg diff`, the AI Auto-Healer will propose an updated contract and open a GitHub PR for human review.

---

## Workflow: Adding a New Contract

```bash
# 1. Generate a draft from a live table (requires AI extras)
dcvpg generate --source postgres_main --table payments --output-dir ./contracts/services

# 2. Review and edit the YAML
code contracts/services/payments.yaml

# 3. Diff against the live source to sanity-check
dcvpg diff --contract payments

# 4. Register
dcvpg register contracts/services/payments.yaml

# 5. Validate immediately
dcvpg validate --contract payments
```

---

## IDE Support

The scaffolded `contracts/_schema/contract.schema.json` file enables YAML validation and autocompletion in VS Code. Add this to the top of each contract file:

```yaml
# yaml-language-server: $schema=./_schema/contract.schema.json
contract:
  name: ...
```

Or configure it globally in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "./contracts/_schema/contract.schema.json": "contracts/**/*.yaml"
  }
}
```
