# DCVPG — Data Contract Validator & Pipeline Guardian

[![CI](https://github.com/pasindudilshan1/dcvpg/actions/workflows/ci.yml/badge.svg)](https://github.com/pasindudilshan1/dcvpg/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dcvpg)](https://pypi.org/project/dcvpg/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/dcvpg)](https://pypi.org/project/dcvpg/)

**DCVPG** is an open-source framework for defining, validating, and enforcing data contracts in modern data pipelines. It catches schema drift, quality violations, and freshness SLA breaches **before they reach production**.

---

## The Problem

Data pipelines break silently. A backend team renames a column, an upstream job starts sending nulls, or an overnight load produces 10× fewer rows than expected — and nobody knows until a BI dashboard breaks or a finance report is wrong.

DCVPG solves this by making **data quality a first-class, code-reviewed, automatically enforced contract** between teams.

---

## How It Works

1. **Define** — Write a YAML contract that describes exactly what data you expect: field names, types, nullability, value ranges, allowed values, row-count SLAs, and freshness deadlines
2. **Validate** — Run DCVPG before your pipeline writes to production; violations are caught and reported immediately
3. **Quarantine** — Failed batches are isolated with full metadata; downstream jobs never see bad data
4. **Alert** — Slack, PagerDuty, Teams, or webhook notifications with violation details
5. **Heal** — AI Auto-Healer proposes an updated contract and opens a GitHub PR for human review

---

## Features

| Category | Capability |
|---|---|
| **Contracts** | Schema, nullability, type, unique, range, allowed values, format (regex), row-count SLA, freshness SLA |
| **AI Generation** | Claude profiles a live table and drafts the contract YAML automatically |
| **AI Auto-Healer** | On CRITICAL violations, an LLM proposes a fix and opens a GitHub PR |
| **AI Anomaly Detection** | Statistical baseline monitoring per-field (volume, null-rate, value distribution) |
| **AI RCA Agent** | Root-cause analysis agent that explains why a pipeline failed |
| **Quarantine Engine** | Isolates failed batches; replay after a contract fix is merged |
| **Schema Drift Detection** | Compares live source schema vs contract definition; alerts on changes |
| **Connectors** | PostgreSQL, MySQL, Snowflake, BigQuery, S3, GCS, REST API, CSV/Parquet file |
| **Custom Rules** | Write Python validation rules extending the built-in rule set |
| **Orchestrator Operators** | Native Airflow operator, Prefect task, and Dagster asset check |
| **REST API** | Full FastAPI backend with auth, pagination, and Prometheus metrics |
| **Streamlit Dashboard** | 6-page real-time monitoring UI |
| **MCP Server** | 10 tools for Claude Desktop / Cursor to manage pipelines by chat |
| **Alerting** | Slack, PagerDuty, Microsoft Teams, generic webhook |

---

## Quick Start

```bash
pip install dcvpg

dcvpg init my_project
cd my_project
```

Edit `dcvpg.config.yaml` to point at your database and connections, then:

```bash
# Optional: generate a contract from a live table using AI
export ANTHROPIC_API_KEY=sk-ant-...
dcvpg generate --source postgres_main --table orders --output-dir ./contracts

# Register the contract
dcvpg register contracts/orders.yaml

# Validate
dcvpg validate --all
```

See the [Quick Start Guide](dcvpg/docs/quickstart.md) for the full walkthrough including Docker Compose setup.

---

## Installation

```bash
# Core (PostgreSQL, file connectors, validation engine, CLI)
pip install dcvpg

# + AI features (contract generation, auto-healing, anomaly detection)
pip install "dcvpg[ai]"

# + MCP server (Claude Desktop / Cursor integration)
pip install "dcvpg[mcp]"

# + Airflow operator
pip install "dcvpg[airflow]"

# + Prefect task
pip install "dcvpg[prefect]"

# + Dagster asset check
pip install "dcvpg[dagster]"

# Everything
pip install "dcvpg[all]"
```

**Requirements:** Python 3.11+, PostgreSQL 15+ (for quarantine & audit storage)

---

## Contract Format

Contracts are plain YAML files. Here is a complete example:

```yaml
contract:
  name: orders_raw
  version: "1.2"
  description: "Raw orders table from the e-commerce backend."

  owner_team: data-engineering
  source_owner: backend-team
  pipeline_tags: [crm, revenue]

  source_connection: postgres_main
  source_table: orders

  # Row-count and freshness SLAs
  row_count_min: 1000
  row_count_max: 5000000
  sla_freshness_hours: 6

  schema:
    - field: id
      type: integer
      nullable: false
      unique: true

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
      format: email          # Regex-backed format validation

    - field: created_at
      type: timestamp
      nullable: false

  # Reference a custom Python validation rule
  custom_rules:
    - rule: no_weekend_orders.NoWeekendOrders
      params:
        date_field: created_at
```

Full field reference: [Contract Authoring Guide](dcvpg/docs/contract_authoring.md)

---

## Custom Validation Rules

Extend the built-in rule set with plain Python:

```python
# custom_rules/no_weekend_orders.py
import pandas as pd
from dcvpg.engine.rules.base_rule import BaseRule
from dcvpg.engine.models import ValidationResult

class NoWeekendOrders(BaseRule):
    def validate(self, data: pd.DataFrame, field: str, params: dict) -> ValidationResult:
        dates = pd.to_datetime(data[params.get("date_field", field)], errors="coerce")
        weekend_count = int((dates.dt.dayofweek >= 5).sum())
        if weekend_count > 0:
            return ValidationResult(
                passed=False, field=field,
                violation_type="WEEKEND_ORDER_FOUND",
                rows_affected=weekend_count,
                expected_value="Orders must be placed on weekdays (Mon–Fri)",
            )
        return ValidationResult(passed=True, field=field)
```

Register in config:
```yaml
extensions:
  custom_rules_dir: ./custom_rules
```

Full guide: [Custom Rules](dcvpg/docs/custom_rules.md)

---

## Orchestrator Integration

### Airflow

```python
from dcvpg.orchestrators.airflow.operators.contract_validator import DataContractValidatorOperator

validate = DataContractValidatorOperator(
    task_id="validate_orders",
    contract_name="orders_raw",
    config_path="/opt/airflow/dcvpg.config.yaml",
)
```

### Prefect

```python
from dcvpg.orchestrators.prefect.tasks import validate_contract

@flow
def my_flow():
    validate_contract(contract_name="orders_raw", config_path="./dcvpg.config.yaml")
```

### Dagster

```python
from dcvpg.orchestrators.dagster.assets import build_contract_asset_check

orders_check = build_contract_asset_check("orders_raw", config_path="./dcvpg.config.yaml")
```

---

## MCP Server — Chat-Driven Pipeline Management

DCVPG ships a [Model Context Protocol](https://modelcontextprotocol.io) server with 10 tools, letting you manage pipelines from Claude Desktop or Cursor by chat.

```bash
pip install "dcvpg[mcp]"
dcvpg mcp-server start
```

**Example prompts:**
- *"What pipelines are currently failing?"*
- *"Show me the violation details for the orders pipeline."*
- *"Is there any schema drift in the payments contract?"*
- *"Generate a contract for the `users` table in postgres_main."*
- *"Open a PR to fix the type mismatch in the orders contract."*
- *"Replay batch abc-123 now that the fix is merged."*

| Tool | Description |
|---|---|
| `get_pipeline_status` | Live health of all pipelines |
| `get_violation_detail` | Full violation breakdown for a pipeline |
| `list_quarantine_batches` | All quarantined batches with metadata |
| `get_schema_diff` | Contract vs live source schema drift report |
| `create_fix_pr` | Open a GitHub PR to update a broken contract |
| `replay_quarantine` | Re-validate and release a quarantined batch |
| `generate_contract` | AI-generate a contract from a live data source |
| `get_incident_summary` | Incidents in the last N days |
| `get_contract_detail` | Full spec, rules, ownership, version history |
| `approve_contract_update` | Merge an approved PR and reload the contract |

Full setup guide: [MCP Setup](dcvpg/docs/mcp_setup.md)

---

## REST API

```bash
uvicorn dcvpg.api.main:app --reload
# → http://localhost:8000/docs
```

Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/contracts` | List all contracts |
| `POST` | `/api/v1/contracts/generate` | AI-generate a contract |
| `GET` | `/api/v1/pipelines` | List pipeline run history |
| `GET` | `/api/v1/quarantine` | List quarantined batches |
| `GET` | `/metrics` | Prometheus metrics |

All endpoints (except `/health` and `/metrics`) require an `Authorization: <key>` header.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      DCVPG Framework                            │
│                                                                 │
│  CLI / REST API / MCP Server / Streamlit Dashboard              │
│           │                                                     │
│           ▼                                                     │
│       Validator  ◄──  Contract Registry  ◄──  YAML Contracts   │
│           │                                                     │
│     ┌─────┴──────┐                                             │
│     │   Rules    │   schema · type · null · range ·            │
│     │   Engine   │   unique · format · allowed_values ·        │
│     │            │   row-count SLA · freshness SLA ·           │
│     └─────┬──────┘   custom Python rules                       │
│           │                                                     │
│     ┌─────┴──────────────────┐                                 │
│     │      Connectors        │  PostgreSQL · MySQL · Snowflake │
│     │                        │  BigQuery · S3 · GCS · File     │
│     └─────┬──────────────────┘                                 │
│           │                                                     │
│     ┌─────┴──────────────────┐                                 │
│     │   Quarantine Engine    │──► PostgreSQL audit store        │
│     │   Alert Manager        │──► Slack · PagerDuty · Teams    │
│     └─────┬──────────────────┘                                 │
│           │                                                     │
│     ┌─────┴──────────────────┐                                 │
│     │      AI Agents         │  ContractGenerator              │
│     │  (Anthropic Claude)    │  AutoHealer → GitHub PR         │
│     │                        │  AnomalyDetector                │
│     │                        │  RCA Agent                      │
│     └────────────────────────┘                                 │
│                                                                 │
│  Orchestrators: Airflow · Prefect · Dagster                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation

| Guide | Description |
|---|---|
| [Quick Start](dcvpg/docs/quickstart.md) | Get up and running in 5 minutes |
| [Contract Authoring](dcvpg/docs/contract_authoring.md) | Full YAML field reference |
| [Connectors](dcvpg/docs/connectors.md) | Configure PostgreSQL, Snowflake, S3, and more |
| [Custom Rules](dcvpg/docs/custom_rules.md) | Write Python validation extensions |
| [MCP Setup](dcvpg/docs/mcp_setup.md) | Claude Desktop / Cursor integration |
| [API Reference](dcvpg/docs/api_reference.md) | REST API endpoints |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Pull requests are welcome for new connectors, rule types, and orchestrator integrations.

## License

Apache 2.0 — see [LICENSE](LICENSE).

