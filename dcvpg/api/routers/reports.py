from fastapi import APIRouter
from datetime import datetime, timedelta
import os

router = APIRouter()


def _get_store():
    from dcvpg.engine.report_store import ReportStore
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    base_dir = os.path.dirname(os.path.abspath(config_path))
    return ReportStore(base_dir)


def _load_config():
    from dcvpg.config.config_loader import load_config
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    if not os.path.exists(config_path):
        return None
    return load_config(config_path)


@router.get("/reports/drift")
def get_drift_report():
    """
    Computes real schema drift by fetching a live sample from each contract's
    source and comparing the inferred column schema against the contract declaration.
    """
    try:
        config = _load_config()
        if not config:
            return {"drifts": []}

        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff, infer_schema_from_dataframe
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.mysql_connector import MySQLConnector
        from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
        from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
        from dcvpg.engine.connectors.s3_connector import S3Connector
        from dcvpg.engine.connectors.gcs_connector import GCSConnector
        from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
        from dcvpg.engine.connectors.file_connector import FileConnector

        _CONNECTOR_MAP = {
            "postgres": PostgresConnector, "mysql": MySQLConnector,
            "snowflake": SnowflakeConnector, "bigquery": BigQueryConnector,
            "s3": S3Connector, "gcs": GCSConnector,
            "rest": RestApiConnector, "file": FileConnector,
        }

        registry = ContractRegistry(config.contracts.directory)
        contracts = registry.list_contracts()
        drifts = []

        for c in contracts:
            try:
                conn_cfg = next((x for x in config.connections if x.name == c.source_connection), None)
                if not conn_cfg:
                    continue
                connector_cls = _CONNECTOR_MAP.get(conn_cfg.type)
                if not connector_cls:
                    continue
                connector = connector_cls()
                connector.connect(conn_cfg.model_dump())
                source = c.source_table or c.name
                df = connector.fetch_sample(source=source, sample_rows=100)
                live_schema = infer_schema_from_dataframe(df)
                contract_schema = [
                    {"field": f.field, "type": f.type} for f in c.schema_fields
                ]
                diff = compute_schema_diff(contract_schema, live_schema)
                if diff["has_drift"]:
                    drifts.append({
                        "contract_name": c.name,
                        "source": c.source_connection,
                        "added_fields": diff["added_fields"],
                        "removed_fields": diff["removed_fields"],
                        "type_changed": diff["type_changed"],
                    })
            except Exception:
                # If we can't reach a source, skip it silently
                continue

        return {"drifts": drifts}

    except Exception:
        return {"drifts": []}


@router.get("/reports/incidents")
def get_incident_history():
    store = _get_store()
    runs = store.get_runs()
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    recent = [r for r in runs if r.get("run_at", "") >= cutoff]
    failed = [r for r in recent if r.get("status") == "FAILED"]
    return {
        "time_window": "30d",
        "incident_count": len(failed),
        "mean_time_to_resolve_minutes": 0,
        "incidents": [
            {
                "pipeline": r.get("pipeline_name"),
                "severity": "CRITICAL",
                "run_at": r.get("run_at"),
                "violations": r.get("violations_count", 0),
            }
            for r in failed[-10:]
        ],
    }
