# DCVPG — Data Contract Validator & Pipeline Guardian

[![CI](https://github.com/your-org/dcvpg/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/dcvpg/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dcvpg)](https://pypi.org/project/dcvpg/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/dcvpg)](https://pypi.org/project/dcvpg/)

**DCVPG** is an open-source framework for defining, validating, and enforcing data contracts in modern data pipelines. It catches schema drift, quality violations, and freshness SLA breaches **before they reach production**.

---

## Features

- **Contract-as-Code** — Define schemas, nullability, value sets, ranges, and row-count SLAs in clean YAML
- **AI Generation** — Use Claude to profile a live table and generate contract YAML automatically
- **AI Auto-Healer** — On CRITICAL violations, an LLM proposes a fix and opens a GitHub PR automatically
- **Multi-Source Connectors** — PostgreSQL, MySQL, Snowflake, BigQuery, S3, GCS, REST API, File
- **Quarantine Engine** — Failed batches are isolated; replay them after a fix is merged
- **Schema Drift Detection** — Compares contract definition vs live source and alerts on changes
- **Anomaly Detection** — Statistical baseline monitoring per-field (volume, null-rate, distribution)
- **MCP Server** — 10 tools for AI assistants (Claude Desktop / Cursor) to manage pipelines by chat
- **Orchestrator Operators** — Native Airflow, Prefect, and Dagster operators
- **Streamlit Dashboard** — 6-page real-time monitoring UI
- **REST API** — Full FastAPI backend with Prometheus metrics

---

## Quick Start

```bash
pip install dcvpg

dcvpg init my_project
cd my_project
# Edit dcvpg.config.yaml …

# Generate a contract with AI
export ANTHROPIC_API_KEY=sk-ant-...
dcvpg generate --source postgres_main --table orders

# Validate
dcvpg validate --all
```

See the [Quick Start Guide](dcvpg/docs/quickstart.md) for full instructions.

---

## Installation

```bash
# Core
pip install dcvpg

# With AI features (contract generation & auto-healing)
pip install "dcvpg[ai]"

# With MCP server
pip install "dcvpg[mcp]"

# Full installation
pip install "dcvpg[all]"
```

---

## Documentation

| Guide | Description |
|---|---|
| [Quick Start](dcvpg/docs/quickstart.md) | Get up and running in 5 minutes |
| [Contract Authoring](dcvpg/docs/contract_authoring.md) | Full YAML reference |
| [Connectors](dcvpg/docs/connectors.md) | Configure data sources |
| [Custom Rules](dcvpg/docs/custom_rules.md) | Write Python validation rules |
| [MCP Setup](dcvpg/docs/mcp_setup.md) | AI assistant integration |
| [API Reference](dcvpg/docs/api_reference.md) | REST API endpoints |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DCVPG Framework (PyPI)                   │
│                                                             │
│  CLI  ──►  Validator  ──►  Quarantine Engine               │
│            │                │                              │
│            │  Rules         │  Alert Manager               │
│            │  (schema,      │  (Slack, PagerDuty,         │
│            │   type, null,  │   Teams, Webhook)            │
│            │   range, …)    │                              │
│            ▼                ▼                              │
│         Connectors       PostgreSQL                        │
│         (PG, MySQL,      (quarantine,                      │
│          Snowflake,       audit log)                       │
│          BigQuery,                                         │
│          S3, GCS, …)   AI Agents                          │
│                         ├─ ContractGenerator              │
│                         ├─ AutoHealer → GitHub PR         │
│                         ├─ AnomalyDetector                │
│                         └─ RCA Agent                      │
│                                                             │
│  FastAPI REST API  ──►  Streamlit Dashboard               │
│  MCP Server (10 tools for Claude Desktop)                  │
│  Orchestrators: Airflow | Prefect | Dagster                │
└─────────────────────────────────────────────────────────────┘
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
