from typing import Any, Optional
from airflow.models import BaseOperator
from airflow.utils.context import Context

from dcvpg.engine.validator import Validator
from dcvpg.engine.registry import ContractRegistry
from dcvpg.config.config_loader import load_config
from dcvpg.engine.connectors.postgres_connector import PostgresConnector
from dcvpg.engine.connectors.mysql_connector import MySQLConnector
from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
from dcvpg.engine.connectors.s3_connector import S3Connector
from dcvpg.engine.connectors.gcs_connector import GCSConnector
from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
from dcvpg.engine.connectors.file_connector import FileConnector
from dcvpg.engine.quarantine_engine import QuarantineEngine
from dcvpg.engine.models import ValidationReport

import os
import uuid
import time
import pandas as pd

import logging
logger = logging.getLogger(__name__)

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

def load_connector(type_str: str) -> Any:
    connector_cls = _CONNECTOR_MAP.get(type_str)
    if connector_cls is None:
        supported = ", ".join(_CONNECTOR_MAP.keys())
        raise NotImplementedError(f"Connector for '{type_str}' not supported. Supported: {supported}")
    return connector_cls()

class DataContractValidatorOperator(BaseOperator):
    """
    Airflow Operator that reads the user's config, loads their contract, connects to the
    declared data source, fetches a batch (either full or sample for now), and validates it.
    """
    
    def __init__(
        self,
        contract: str,          # Name of the contract (e.g. 'orders_raw')
        source_conn: str,       # Name of the connection declared in dcvpg.config.yaml
        config_path: str = "./dcvpg.config.yaml",
        on_failure: str = "quarantine_and_alert",
        batch_id: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.contract_name = contract
        self.source_conn = source_conn
        self.config_path = config_path
        self.on_failure = on_failure
        self.batch_id = batch_id
        
    def execute(self, context: Context) -> ValidationReport:
        start_time = time.time()
        
        # 1. Load config
        if not os.path.exists(self.config_path):
             raise FileNotFoundError(f"DCVPG config file not found: {self.config_path}")
             
        config = load_config(self.config_path)
        
        # 2. Get the contract definition
        registry = ContractRegistry(config.contracts.directory)
        contract_spec = registry.get_contract(self.contract_name)
        
        # 3. Connection Setup
        conn_config = next((c for c in config.connections if c.name == self.source_conn), None)
        if not conn_config:
            raise ValueError(f"Connection {self.source_conn} not found in config.yaml")
        
        connector_instance = load_connector(conn_config.type)
        connector_instance.connect(conn_config.model_dump())
        
        batch = str(self.batch_id or context.get('run_id') or uuid.uuid4())
        
        # Assumes contract.source_connection defines the table/endpoint inside the connector
        # For simplicity, we fetch the batch here. In a real scenario, this would be highly contextualized
        source_name = getattr(contract_spec, "source_table", self.contract_name.split('/')[-1])
        df: pd.DataFrame = connector_instance.fetch_batch(source=source_name, batch_id=batch)
        
        # 4. Engine Validation
        custom_dir = config.extensions.custom_rules_dir if config.extensions else None
        engine = Validator(contract_spec, custom_dir)
        
        duration_ms = int((time.time() - start_time) * 1000)
        report: ValidationReport = engine.validate_batch(df, pipeline_name=self.task_id, duration_ms=duration_ms)
        
        # 5. Handle Failures & Quarantine
        if report.status == "FAILED":
             logger.error(f"Contract {self.contract_name} validation FAILED. Found {report.violations_count} violations.")
             
             if self.on_failure == "quarantine_and_alert":
                 quarantine = QuarantineEngine(config.database.model_dump())
                 quarantine.isolate_batch(report, batch)
                 # BaseAlerter logic would be called here
                 
             # Halt Airflow DAG by raising an exception, or soft-fail
             raise ValueError(f"Data contract validation failed for {self.contract_name}.")
             
        logger.info(f"Contract {self.contract_name} PASSED validation successfully.")
        return report.model_dump()
