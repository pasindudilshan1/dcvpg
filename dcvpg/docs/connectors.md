# Connector Reference

Connectors tell DCVPG how to read data from your sources. Each connection is declared once in `dcvpg.config.yaml` under the `connections` key and then referenced by name in every contract that reads from it.

---

## How Connections Work

```yaml
# dcvpg.config.yaml
connections:
  - name: postgres_main        # ← this name is used in contracts
    type: postgres
    host: ${DB_HOST}
    ...
```

```yaml
# contracts/services/orders.yaml
contract:
  source_connection: postgres_main   # ← must match the name above
  source_table: orders
```

All `${VAR}` values are resolved from environment variables at runtime. Never hardcode passwords in config files.

---

## PostgreSQL

```yaml
connections:
  - name: postgres_main
    type: postgres
    host: ${DB_HOST}
    port: 5432
    database: production_db
    user: ${DB_USER}
    password: ${DB_PASSWORD}
```

**Included in:** `pip install dcvpg` (uses `psycopg2-binary`)

---

## MySQL

```yaml
connections:
  - name: mysql_main
    type: mysql
    host: ${DB_HOST}
    port: 3306
    database: production_db
    user: ${DB_USER}
    password: ${DB_PASSWORD}
```

**Install extra:**
```bash
pip install pymysql
```

---

## Snowflake

```yaml
connections:
  - name: snowflake_prod
    type: snowflake
    account: ${SNOWFLAKE_ACCOUNT}    # e.g. xy12345.us-east-1
    user: ${SNOWFLAKE_USER}
    password: ${SNOWFLAKE_PASSWORD}
    warehouse: COMPUTE_WH
    database: PROD_DB
    schema: PUBLIC
```

**Install extra:**
```bash
pip install snowflake-sqlalchemy
```

---

## BigQuery

```yaml
connections:
  - name: bq_prod
    type: bigquery
    project: my-gcp-project
    dataset: analytics
    credentials_json_env: GOOGLE_APPLICATION_CREDENTIALS   # env var pointing to service account JSON path
```

**Install extra:**
```bash
pip install pandas-gbq google-cloud-bigquery
```

Set the env var before running DCVPG:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## Amazon S3

```yaml
connections:
  - name: s3_datalake
    type: s3
    bucket: my-data-lake-bucket
    aws_access_key_env: AWS_ACCESS_KEY_ID
    aws_secret_key_env: AWS_SECRET_ACCESS_KEY
    region: us-east-1
    file_type: parquet    # csv | json | parquet
```

**Install extra:**
```bash
pip install s3fs boto3
```

In the contract, set `source_table` to the object key (path within the bucket):
```yaml
source_table: data/orders/2026-03-09/orders.parquet
```

---

## Google Cloud Storage

```yaml
connections:
  - name: gcs_lake
    type: gcs
    bucket: my-gcs-bucket
    project: my-gcp-project
    credentials_env: GOOGLE_APPLICATION_CREDENTIALS
    file_type: parquet    # csv | json | parquet
```

**Install extra:**
```bash
pip install gcsfs google-cloud-storage
```

In the contract, set `source_table` to the object path within the bucket:
```yaml
source_table: data/orders/today.parquet
```

---

## REST API

```yaml
connections:
  - name: orders_api
    type: rest
    base_url: https://api.example.com/v1
    endpoint: /orders
    auth_type: bearer          # bearer | api_key | basic | none
    token_env: API_TOKEN
    json_path: data.orders     # Dot-notation path to the array in the response body
```

DCVPG fetches the endpoint, extracts the array at `json_path`, and loads it into a DataFrame for validation.

---

## Local / Network File

```yaml
connections:
  - name: local_files
    type: file
    file_type: csv    # csv | json | parquet
```

In the contract, set `source_table` to the full file path:
```yaml
source_table: /data/orders/today.csv
```

Supported formats: `csv`, `json` (line-delimited or array), `parquet`.

---

## Custom Connector

If none of the built-in connectors fits your source, write one in Python:

**Step 1 — Scaffold**

```bash
# From your project directory (created by dcvpg init)
cp custom_connectors/example_connector.py custom_connectors/my_connector.py
```

**Step 2 — Implement**

```python
# custom_connectors/my_connector.py
from dcvpg.engine.connectors.base_connector import BaseConnector
import pandas as pd


class MyConnector(BaseConnector):
    def connect(self) -> None:
        """Establish connection using self.config dict."""
        ...

    def fetch_batch(self, table: str) -> pd.DataFrame:
        """Return the full batch as a DataFrame for validation."""
        ...

    def fetch_sample(self, table: str, n: int = 1000) -> pd.DataFrame:
        """Return a sample for AI contract generation profiling."""
        ...
```

**Step 3 — Register in config**

```yaml
extensions:
  custom_connectors_dir: ./custom_connectors

connections:
  - name: my_source
    type: my_connector   # matches the file name without .py
    # any extra keys here are passed as self.config to your connector
    api_url: https://internal.example.com
```

The connector class name must be `PascalCase` of the file name — `my_connector.py` → `MyConnector`.

---

## Connection Security Checklist

- Always use `${ENV_VAR}` syntax for passwords, tokens, and keys
- Never commit `dcvpg.config.yaml` with real credentials
- Add `dcvpg.config.yaml` to `.gitignore` or use a `.env` file with `python-dotenv`
- For production, prefer a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.) and inject values as environment variables
