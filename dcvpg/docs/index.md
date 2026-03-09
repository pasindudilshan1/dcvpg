# Data Contract Validator & Pipeline Guardian (DCVPG)

Welcome to the official documentation for **DCVPG v1.3.0**.

## What is DCVPG?

DCVPG is a generic, open-source framework that prevents silent data corruption and schema drift in data pipelines. It validates data flowing through your orchestrators (Airflow, Dagster, Prefect) against explicitly declared YAML contracts — catching schema changes, null violations, stale data, and row-count anomalies **before they reach production**.

---

## Key Features

| Category | Capability |
|---|---|
| **Validation Engine** | Schema, nullability, type, unique, range, allowed values, format (regex), row-count SLA, freshness SLA |
| **AI Contract Generation** | Claude profiles a live table and drafts the contract YAML automatically |
| **AI Auto-Healer** | On CRITICAL violations, opens a GitHub PR with a proposed contract fix |
| **AI Anomaly Detection** | Statistical baseline monitoring per field (volume, null-rate, value distribution) |
| **AI RCA Agent** | Root-cause analysis that explains exactly why a pipeline failed |
| **Quarantine Engine** | Isolates failing batches; replay them after a contract fix is merged |
| **Connectors** | PostgreSQL, MySQL, Snowflake, BigQuery, S3, GCS, REST API, CSV/Parquet |
| **Custom Rules** | Extend validation with plain Python classes |
| **Orchestrators** | Native Airflow operator, Prefect task, Dagster asset check |
| **REST API** | FastAPI backend with auth, pagination, and Prometheus metrics |
| **Streamlit Dashboard** | 6-page real-time monitoring UI |
| **MCP Server** | 10 tools for Claude Desktop / Cursor to manage pipelines by chat |
| **Alerting** | Slack, PagerDuty, Microsoft Teams, generic webhook |

---

## Getting Started

```bash
pip install dcvpg

dcvpg init my_data_platform
cd my_data_platform

# Start the REST API (terminal 1)
dcvpg serve api

# Start the dashboard (terminal 2)
dcvpg serve dashboard
```

The API runs at `http://localhost:8000` and the dashboard at `http://localhost:8501`.  
No repo clone needed — all services are started via the installed CLI.

---

## Documentation

| Guide | Description |
|---|---|
| [Quick Start](quickstart.md) | Install, scaffold, and validate your first contract end-to-end |
| [Contract Authoring](contract_authoring.md) | Full YAML contract reference and versioning conventions |
| [Connectors](connectors.md) | Configure data sources (Postgres, Snowflake, BigQuery, S3, GCS, REST, file) |
| [Custom Rules](custom_rules.md) | Write Python validation rules and reference them in contracts |
| [MCP Server Setup](mcp_setup.md) | Connect Claude Desktop or Cursor to manage pipelines by chat |
| [API Reference](api_reference.md) | REST API endpoints, authentication, and error codes |
