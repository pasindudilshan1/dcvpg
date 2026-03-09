# Connector Reference

DCVPG ships connectors for all major data sources. Set the `type` in your `dcvpg.config.yaml` connections block.

## PostgreSQL / MySQL

```yaml
connections:
  - name: postgres_main
    type: postgres        # or: mysql
    host: ${DB_HOST}
    port: 5432
    database: production_db
    user: ${DB_USER}
    password: ${DB_PASSWORD}
```

**Install extras:**
```bash
pip install dcvpg           # postgres (psycopg2) included
pip install dcvpg pymysql   # for MySQL
```

## Snowflake

```yaml
connections:
  - name: snowflake_prod
    type: snowflake
    account: ${SNOWFLAKE_ACCOUNT}   # e.g. xy12345.us-east-1
    user: ${SNOWFLAKE_USER}
    password: ${SNOWFLAKE_PASSWORD}
    warehouse: COMPUTE_WH
    database: PROD_DB
    schema: PUBLIC
```

```bash
pip install "dcvpg[snowflake]"   # or: pip install snowflake-sqlalchemy
```

## BigQuery

```yaml
connections:
  - name: bq_prod
    type: bigquery
    project: my-gcp-project
    dataset: analytics
    credentials_json_env: GOOGLE_APPLICATION_CREDENTIALS  # path to service account JSON
```

```bash
pip install "dcvpg[bigquery]"   # or: pip install pandas-gbq google-cloud-bigquery
```

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

```bash
pip install "dcvpg[s3]"   # or: pip install s3fs boto3
```

## Google Cloud Storage

```yaml
connections:
  - name: gcs_lake
    type: gcs
    bucket: my-gcs-bucket
    project: my-gcp-project
    credentials_env: GOOGLE_APPLICATION_CREDENTIALS
    file_type: parquet
```

```bash
pip install gcsfs google-cloud-storage
```

## REST API

```yaml
connections:
  - name: orders_api
    type: rest
    base_url: https://api.example.com/v1
    endpoint: /orders
    auth_type: bearer         # bearer | api_key | basic | none
    token_env: API_TOKEN
    json_path: data.orders    # Dot-notation path to the array in the response
```

## File (Local / Network)

```yaml
connections:
  - name: local_csv
    type: file
    file_type: csv            # csv | json | parquet
```

In the contract, set `source_table` to the file path:
```yaml
source_table: /data/orders/today.csv
```

## Custom Connector

1. Copy the template:
   ```bash
   cp dcvpg/templates/custom_connector.py.template my_project/custom_connectors/my_connector.py
   ```
2. Implement `connect()`, `fetch_batch()`, and `fetch_sample()`.
3. Register in config:
   ```yaml
   extensions:
     custom_connectors_dir: ./custom_connectors
   connections:
     - name: my_source
       type: my_connector   # matches file name without .py
   ```
