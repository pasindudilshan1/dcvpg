# Quick Start Guide

## Prerequisites
- Python 3.11+
- PostgreSQL 15+ (for quarantine/audit storage)
- `pip install dcvpg`

## 1. Initialize a Project

```bash
dcvpg init my_data_project
cd my_data_project
```

This scaffolds:
```
my_data_project/
├── contracts/          # Your YAML contract files go here
├── custom_rules/       # Optional Python rule extensions
├── custom_connectors/  # Optional connector overrides
├── pipelines/
│   ├── airflow/        # Example DAG
│   └── prefect/        # Example Prefect flow
└── dcvpg.config.yaml   # Main configuration
```

## 2. Configure Your Project

Edit `dcvpg.config.yaml`:

```yaml
project:
  name: my_data_project
  team: data-engineering
  environment: production

database:
  host: localhost
  port: 5432
  name: dcvpg
  user: dcvpg_user
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
```

## 3. Generate a Contract with AI

```bash
export ANTHROPIC_API_KEY=sk-ant-...
dcvpg generate --source postgres_main --table orders --output-dir ./contracts/generated
```

DCVPG will:
1. Connect to your source
2. Profile field statistics
3. Call Claude to infer types, nullability, and constraints
4. Save a ready-to-review YAML

## 4. Review and Register

Edit the generated YAML, then register:

```bash
dcvpg register contracts/generated/orders.yaml
```

## 5. Validate

```bash
# Validate all registered contracts
dcvpg validate --all

# Validate a specific one
dcvpg validate --contract orders
```

## 6. Start the API & Dashboard

```bash
# Using Docker Compose
cd dcvpg/infra
docker-compose up -d

# Or run directly
uvicorn dcvpg.api.main:app --reload &
streamlit run dcvpg/dashboard/app.py
```

- **API docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

## Next Steps

- [Contract Authoring Guide](contract_authoring.md)
- [Connector Reference](connectors.md)
- [Custom Rules](custom_rules.md)
- [MCP Server Setup](mcp_setup.md)
