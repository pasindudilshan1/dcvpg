from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import uuid
import time

router = APIRouter()

class ContractResponse(BaseModel):
    name: str
    version: str
    status: str
    owner_team: str = None
    source_owner: str = None
    source_connection: str = None
    source_table: str = None
    description: str = None
    schema: list = []

def _load_registry():
    """Load contracts from the registry using the project config."""
    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry
        config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        return registry.list_contracts()
    except Exception:
        return []

@router.get("/contracts")
def list_contracts():
    contracts = _load_registry()
    return [
        {
            "name": c.name,
            "version": c.version,
            "status": "active",
            "owner_team": c.owner_team,
            "source_owner": c.source_owner,
            "source_connection": c.source_connection,
            "source_table": c.source_table,
            "description": c.description,
            "schema": [f.model_dump() for f in c.schema_fields],
        }
        for c in contracts
    ]

@router.get("/contracts/{name}")
def get_contract(name: str):
    contracts = _load_registry()
    match = next((c for c in contracts if c.name == name), None)
    if not match:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {
        "name": match.name,
        "version": match.version,
        "owner_team": match.owner_team,
        "source_connection": match.source_connection,
        "source_table": match.source_table,
        "description": match.description,
        "schema": [f.model_dump() for f in match.schema_fields],
    }

@router.post("/contracts/{name}/fix")
def auto_fix_contract(name: str, body: Optional[Dict[str, Any]] = None):
    """
    AutoHealer: validate the contract against its live source, then use the LLM
    to propose a corrected YAML and open a GitHub PR.
    Requires GITHUB_TOKEN and GITHUB_REPO env vars.
    """
    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPO", "")
    if not github_token or not github_repo:
        raise HTTPException(
            status_code=400,
            detail="GITHUB_TOKEN and GITHUB_REPO env vars must be set for AutoHealer",
        )

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.validator import Validator
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.mysql_connector import MySQLConnector
        from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
        from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
        from dcvpg.engine.connectors.s3_connector import S3Connector
        from dcvpg.engine.connectors.gcs_connector import GCSConnector
        from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
        from dcvpg.engine.connectors.file_connector import FileConnector
        from dcvpg.ai_agents.auto_healer.agent import AutoHealerAgent

        config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        contract = next((c for c in registry.list_contracts() if c.name == name), None)
        if not contract:
            raise HTTPException(status_code=404, detail=f"Contract '{name}' not found")

        conn_cfg = next((x for x in config.connections if x.name == contract.source_connection), None)
        if not conn_cfg:
            raise HTTPException(status_code=404, detail=f"Connection '{contract.source_connection}' not found")

        _CONNECTOR_MAP = {
            "postgres": PostgresConnector, "mysql": MySQLConnector,
            "snowflake": SnowflakeConnector, "bigquery": BigQueryConnector,
            "s3": S3Connector, "gcs": GCSConnector,
            "rest": RestApiConnector, "file": FileConnector,
        }
        connector_cls = _CONNECTOR_MAP.get(conn_cfg.type)
        if not connector_cls:
            raise HTTPException(status_code=400, detail=f"Unsupported connector: {conn_cfg.type}")

        connector = connector_cls()
        connector.connect(conn_cfg.model_dump())
        source = contract.source_table or contract.name
        start = time.time()
        df = connector.fetch_batch(source=source, batch_id=str(uuid.uuid4()))
        duration_ms = int((time.time() - start) * 1000)

        engine = Validator(contract)
        report = engine.validate_batch(df, pipeline_name=contract.name, duration_ms=duration_ms)

        if report.status == "PASSED":
            return {"status": "ok", "message": "No violations found — no fix needed"}

        # Load raw YAML for patching
        contract_yaml = ""
        yaml_candidates = [
            os.path.join(config.contracts.directory, f"{name}.yaml"),
            os.path.join(config.contracts.directory, f"{name}.yml"),
        ]
        for p in yaml_candidates:
            if os.path.exists(p):
                with open(p) as f:
                    contract_yaml = f.read()
                break

        healer = AutoHealerAgent(
            github_token=github_token,
            repo_name=github_repo,
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        batch_id = str(uuid.uuid4())
        pr_url = healer.process_failure(
            report=report,
            batch_id=batch_id,
            contract_yaml=contract_yaml,
        )

        if pr_url:
            return {"status": "pr_created", "pr_url": pr_url, "violations": report.violations_count}
        return {"status": "skipped", "reason": "Violations not auto-patchable (not TYPE_MISMATCH/FIELD_MISSING)"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contracts")
def register_contract(content: Dict[str, Any]):
    return {"status": "registered", "contract": content.get("name", "unknown")}


@router.put("/contracts/{name}")
def update_contract(name: str, content: Dict[str, Any]):
    return {"status": "updated", "version": "1.1"}


@router.delete("/contracts/{name}")
def deregister_contract(name: str):
    return {"status": "deregistered"}
