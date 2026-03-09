# Quick Start Guide

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Required |
| PostgreSQL | 15+ | Required for quarantine & audit storage |
| pip | latest | `pip install --upgrade pip` |

---

## 1. Install DCVPG

```bash
# Core — validation engine, CLI, REST API, dashboard
pip install dcvpg

# With AI features (contract generation, auto-healer, anomaly detection)
pip install "dcvpg[ai]"

# With MCP server (Claude Desktop / Cursor integration)
pip install "dcvpg[mcp]"

# Everything
pip install "dcvpg[all]"
```

---

## 2. Initialize a Project

```bash
dcvpg init my_data_project
cd my_data_project
```

This scaffolds a ready-to-use project structure:

```
my_data_project/
├── dcvpg.config.yaml          # Main configuration — edit this first
├── contracts/
│   ├── _schema/               # JSON schema for IDE validation
│   └── services/
│       └── example_contract.yaml
├── custom_rules/              # Optional Python validation rules
├── custom_connectors/         # Optional connector extensions
├── pipelines/
│   ├── airflow/               # Example Airflow DAG
│   └── prefect/               # Example Prefect flow
└── .github/
    └── workflows/
        └── validate_contracts.yml   # CI contract check
```

---

## 3. Configure Your Project

Edit `dcvpg.config.yaml` to point at your database and data sources:

```yaml
project:
  name: my_data_project
  team: data-engineering
  environment: production

database:
  host: ${DCVPG_DB_HOST}       # PostgreSQL for quarantine & audit
  port: 5432
  name: dcvpg
  user: ${DCVPG_DB_USER}
  password: ${DCVPG_DB_PASSWORD}

connections:
  - name: postgres_main
    type: postgres
    host: ${DB_HOST}
    port: 5432
    database: production_db
    user: ${DB_USER}
    password: ${DB_PASSWORD}

contracts:
  directory: ./contracts
  auto_register: true

alerting:
  slack_webhook_env: SLACK_WEBHOOK_URL   # Optional
```

All `${VAR}` placeholders are resolved from environment variables at runtime. Never hardcode credentials in this file.

---

## 4. Generate a Contract with AI (Optional)

If you have an Anthropic API key, DCVPG can profile a live table and draft the contract YAML automatically:

```bash
export ANTHROPIC_API_KEY=sk-ant-...

dcvpg generate \
  --source postgres_main \
  --table orders \
  --output-dir ./contracts/services
```

DCVPG will:
1. Connect to the source and sample the table
2. Profile field statistics (types, null rates, value distributions)
3. Call Claude to infer constraints and rules
4. Write a ready-to-review YAML file

You can also write contracts by hand — see the [Contract Authoring Guide](contract_authoring.md).

---

## 5. Review and Register a Contract

Inspect and adjust the generated YAML, then register it:

```bash
dcvpg register contracts/services/orders.yaml
```

To see all registered contracts:

```bash
dcvpg status
```

To compare a contract against the current live source schema:

```bash
dcvpg diff --contract orders
```

---

## 6. Validate

```bash
# Validate all registered contracts
dcvpg validate --all

# Validate a single contract
dcvpg validate --contract orders
```

A passing run exits with code `0`. A failing run prints a violation table and exits with code `1`, making it easy to fail CI pipelines.

---

## 7. Start the REST API

The REST API powers the dashboard and the MCP server. Start it in its own terminal:

```bash
export DCVPG_API_KEY=your-secret-key

dcvpg serve api
```

| Default | Value |
|---|---|
| URL | `http://localhost:8000` |
| Interactive docs | `http://localhost:8000/docs` |
| Port | `8000` |

Options:

```bash
dcvpg serve api --port 9000 --reload   # custom port, dev auto-reload
```

---

## 8. Start the Dashboard

In a second terminal:

```bash
export DCVPG_API_KEY=your-secret-key
export DCVPG_API_URL=http://localhost:8000/api/v1

dcvpg serve dashboard
```

| Default | Value |
|---|---|
| URL | `http://localhost:8501` |
| Port | `8501` |

Options:

```bash
dcvpg serve dashboard --port 8502 --api-url http://myhost:8000/api/v1
```

> **Note:** `dcvpg serve dashboard` resolves the correct path to the installed Streamlit app automatically. You do **not** need to clone the repository or know where the package is installed.

---

## 9. Start the MCP Server (Optional)

To use natural-language pipeline management from Claude Desktop or Cursor:

```bash
pip install "dcvpg[mcp]"
dcvpg mcp-server start
```

See the [MCP Server Setup Guide](mcp_setup.md) for full Claude Desktop configuration.

---

## All CLI Commands

```
dcvpg init <name>             Scaffold a new project
dcvpg generate                AI-generate a contract from a live table
dcvpg register <file>         Register a contract YAML
dcvpg validate                Run validation against registered contracts
dcvpg diff                    Compare contract vs live source schema
dcvpg status                  Show all registered contracts and their health
dcvpg replay                  Re-validate a quarantined batch
dcvpg serve api               Start the FastAPI REST API
dcvpg serve dashboard         Start the Streamlit Dashboard
dcvpg mcp-server start        Start the MCP server (stdio mode)
dcvpg mcp-server status       Check MCP server configuration
```

---

## Next Steps

- [Contract Authoring Guide](contract_authoring.md) — full YAML field reference
- [Connector Reference](connectors.md) — Postgres, Snowflake, BigQuery, S3, GCS, REST, file
- [Custom Rules](custom_rules.md) — write Python validation rules
- [MCP Server Setup](mcp_setup.md) — connect Claude Desktop or Cursor
- [API Reference](api_reference.md) — REST endpoints
