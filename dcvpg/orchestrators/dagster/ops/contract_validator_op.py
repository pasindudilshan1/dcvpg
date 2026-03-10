from typing import Dict, Any
from dagster import op, OpExecutionContext, Config, Failure
from dcvpg.config.config_loader import load_config
from dcvpg.engine.registry import ContractRegistry
from dcvpg.engine.validator import Validator
from dcvpg.engine.quarantine_engine import QuarantineEngine
from dcvpg.engine.connectors.postgres_connector import PostgresConnector
from dcvpg.engine.connectors.mysql_connector import MySQLConnector
from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
from dcvpg.engine.connectors.s3_connector import S3Connector
from dcvpg.engine.connectors.gcs_connector import GCSConnector
from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
from dcvpg.engine.connectors.file_connector import FileConnector
import time
import os

class ValidationConfig(Config):
    contract_name: str
    source_conn: str
    config_path: str = "./dcvpg.config.yaml"
    on_failure: str = "quarantine_and_alert"

_CONNECTOR_MAP = {
    "postgres":  PostgresConnector,
    "mysql":     MySQLConnector,
    "snowflake": SnowflakeConnector,
    "bigquery":  BigQueryConnector,
    "s3":        S3Connector,
    "gcs":       GCSConnector,
    "rest":      RestApiConnector,
    "file":      FileConnector,
}

def _get_connector(type_str: str) -> Any:
    connector_cls = _CONNECTOR_MAP.get(type_str)
    if connector_cls is None:
        supported = ", ".join(_CONNECTOR_MAP.keys())
        raise NotImplementedError(f"Connector '{type_str}' not supported. Supported: {supported}")
    return connector_cls()

@op(name="validate_contract_op", description="Dagster op to validate data contracts using DCVPG")
def validate_contract(context: OpExecutionContext, config: ValidationConfig) -> Dict[str, Any]:
    context.log.info(f"Starting contract validation for {config.contract_name}")
    start_time = time.time()
    
    if not os.path.exists(config.config_path):
        raise FileNotFoundError(f"DCVPG config file not found: {config.config_path}")
        
    dcvpg_config = load_config(config.config_path)
    registry = ContractRegistry(dcvpg_config.contracts.directory)
    contract_spec = registry.get_contract(config.contract_name)
    
    conn_config = next((c for c in dcvpg_config.connections if c.name == config.source_conn), None)
    if not conn_config:
        raise ValueError(f"Connection {config.source_conn} not found in {config.config_path}")
        
    connector = _get_connector(conn_config.type)
    connector.connect(conn_config.model_dump())
    
    batch = str(context.run_id)
    source_name = getattr(contract_spec, "source_table", config.contract_name.split('/')[-1])
    
    context.log.info(f"Fetching batch id {batch} from {source_name}")
    df = connector.fetch_batch(source=source_name, batch_id=batch)
    
    custom_dir = dcvpg_config.extensions.custom_rules_dir if dcvpg_config.extensions else None
    engine = Validator(contract_spec, custom_dir)
    
    duration = int((time.time() - start_time) * 1000)
    report = engine.validate_batch(df, pipeline_name=context.op.name, duration_ms=duration)
    
    if report.status == "FAILED":
        context.log.error(f"Validation FAILED: {report.violations_count} violations found on {report.rows_processed} rows")
        
        if config.on_failure == "quarantine_and_alert":
            quarantine = QuarantineEngine(dcvpg_config.database.model_dump())
            quarantine.isolate_batch(report, batch)
            
        raise Failure(
            description=f"Data contract validation failed for {config.contract_name}",
            metadata={
                "violations_count": report.violations_count,
                "rows_affected": sum(d.rows_affected for d in report.violation_details if d.rows_affected)
            }
        )
        
    context.log.info(f"Validation PASSED for {config.contract_name}")
    return report.model_dump()
