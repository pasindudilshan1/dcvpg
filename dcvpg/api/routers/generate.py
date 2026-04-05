import os
from fastapi import APIRouter, HTTPException
from typing import Dict

router = APIRouter()


def _load_config():
    from dcvpg.config.config_loader import load_config
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    if not os.path.exists(config_path):
        return None
    return load_config(config_path)


@router.post("/contracts/generate")
def generate_contract(request: Dict[str, str]):
    """
    Fetch a live sample from the requested source/table and use the
    ContractGeneratorAgent (LLM) to produce a contract YAML.
    Saves the generated YAML to the contracts directory and returns it.
    """
    source_conn = request.get("source_conn") or request.get("source_connection", "")
    table = request.get("table") or request.get("table_name", "")

    if not source_conn or not table:
        raise HTTPException(status_code=400, detail="source_conn and table are required")

    config = _load_config()
    if not config:
        raise HTTPException(status_code=500, detail="DCVPG config not found — set DCVPG_CONFIG_PATH")

    conn_cfg = next((x for x in config.connections if x.name == source_conn), None)
    if not conn_cfg:
        raise HTTPException(status_code=404, detail=f"Connection '{source_conn}' not found in config")

    # Load connector
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
    connector_cls = _CONNECTOR_MAP.get(conn_cfg.type)
    if not connector_cls:
        raise HTTPException(status_code=400, detail=f"Unsupported connector type: {conn_cfg.type}")

    try:
        connector = connector_cls()
        connector.connect(conn_cfg.model_dump())
        df = connector.fetch_sample(source=table, sample_rows=200)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch sample from source: {e}")

    # Generate contract YAML via LLM (falls back to profile-based if ANTHROPIC_API_KEY not set)
    from dcvpg.ai_agents.contract_generator.generator_agent import ContractGeneratorAgent
    agent = ContractGeneratorAgent()
    try:
        yaml_content = agent.generate(source_name=source_conn, table_name=table, df_sample=df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract generation failed: {e}")

    # Persist to the contracts directory
    contracts_dir = os.path.join(
        os.path.dirname(os.path.abspath(os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml"))),
        config.contracts.directory.lstrip("./"),
        "generated",
    )
    os.makedirs(contracts_dir, exist_ok=True)
    file_name = f"{table}_generated.yaml"
    file_path = os.path.join(contracts_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return {
        "status": "generated",
        "contract": file_name,
        "file_path": file_path,
        "yaml": yaml_content,
        "rows_sampled": len(df),
    }
