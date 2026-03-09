# Data Contract Validator & Pipeline Guardian (DCVPG)

Welcome to the official documentation for DCVPG!

## What is DCVPG?
DCVPG is a generic, open-source framework designed to prevent "silent data corruption" and schema drift in data pipelines. It intercepts data flowing through orchestrators (Airflow, Dagster, Prefect) and validates it against explicitly declared Data Contracts.

### Key Features
- **Contract Engine**: Validates schemas, data quality, uniqueness, and constraints using Pydantic and Pandas.
- **Auto-Discovery**: Instantly scan and load `.yaml` contracts from your directories.
- **Orchestrator Naive**: Drop-in operators for Airflow, Prefect, and Dagster.
- **AI-Powered**: Auto-Healer Agent for SQL drift adjustments, and Contract Generator for bootstrapping specs from live DBs.
- **Alerting & Dashboards**: Central quarantine database, Grafana metrics, and Real-time Streamlit monitoring.

## Getting Started

```bash
# General Setup
pip install dcvpg[all]

# Scaffold your pipeline directory
dcvpg init my_data_platform
cd my_data_platform

# Validate manually
dcvpg validate --all
```

See **Core Concepts** to understand how to write and connect Contracts to your pipeline.
