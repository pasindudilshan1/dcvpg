from typing import Optional, Dict, Any
from prefect import task, get_run_logger # Requires "prefect" in requirements
from dcvpg.config.config_loader import load_config
from dcvpg.engine.registry import ContractRegistry
from dcvpg.engine.validator import Validator
from dcvpg.engine.quarantine_engine import QuarantineEngine
from dcvpg.engine.connectors.postgres_connector import PostgresConnector
from dcvpg.engine.connectors.file_connector import FileConnector
import uuid
import time
import os

def _get_connector(type_str: str) -> Any:
    if type_str == "postgres":
        return PostgresConnector()
    if type_str == "file":
        return FileConnector()
    raise NotImplementedError(f"Connector {type_str} not implemented")

@task(name="dcvpg_validate", description="Validates incoming data against a declared data contract")
def validate_contract(
    contract_name: str,
    source_conn: str,
    config_path: str = "./dcvpg.config.yaml",
    on_failure: str = "quarantine_and_alert",
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    
    logger = get_run_logger()
    start_time = time.time()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config path {config_path} not found")
        
    config = load_config(config_path)
    registry = ContractRegistry(config.contracts.directory)
    contract_spec = registry.get_contract(contract_name)
    
    conn_config = next((c for c in config.connections if c.name == source_conn), None)
    if not conn_config:
        raise ValueError(f"Connection {source_conn} not defined in {config_path}")
        
    connector = _get_connector(conn_config.type)
    connector.connect(conn_config.model_dump())
    
    batch = batch_id or str(uuid.uuid4())
    logger.info(f"Starting validation for {contract_name} batch {batch}")
    
    # Generic extraction from contract settings
    source_name = getattr(contract_spec, "source_table", contract_name.split('/')[-1])
    df = connector.fetch_batch(source=source_name, batch_id=batch)
    
    custom_dir = config.extensions.custom_rules_dir if config.extensions else None
    engine = Validator(contract_spec, custom_dir)
    
    duration = int((time.time() - start_time) * 1000)
    report = engine.validate_batch(df, pipeline_name=f"prefect_{contract_name}", duration_ms=duration)
    
    if report.status == "FAILED":
        logger.error(f"Validation FAILED for {contract_name}: {report.violations_count} violations on {report.rows_processed} rows")
        
        if on_failure == "quarantine_and_alert":
            quarantine = QuarantineEngine(config.database.model_dump())
            quarantine.isolate_batch(report, batch)
            
        raise ValueError(f"Data contract validation failed for {contract_name}.")
        
    logger.info(f"Validation PASSED for {contract_name}.")
    return report.model_dump()
