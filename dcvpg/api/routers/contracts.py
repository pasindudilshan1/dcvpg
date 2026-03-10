from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os

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

@router.post("/contracts")
def register_contract(content: Dict[str, Any]):
    return {"status": "registered", "contract": content.get("name", "unknown")}

@router.put("/contracts/{name}")
def update_contract(name: str, content: Dict[str, Any]):
    return {"status": "updated", "version": "1.1"}

@router.delete("/contracts/{name}")
def deregister_contract(name: str):
    return {"status": "deregistered"}
