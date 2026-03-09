from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()

# Normally we'd use the central ContractSpec from engine.models
class ContractResponse(BaseModel):
    name: str
    version: str
    status: str

@router.get("/contracts", response_model=List[ContractResponse])
def list_contracts():
    return [{"name": "orders_raw", "version": "1.0", "status": "active"}]

@router.get("/contracts/{name}")
def get_contract(name: str):
    if name != "orders_raw":
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"name": name, "version": "1.0", "rules": []}

@router.post("/contracts")
def register_contract(content: Dict[str, Any]):
    return {"status": "registered", "contract": content.get("name", "unknown")}

@router.put("/contracts/{name}")
def update_contract(name: str, content: Dict[str, Any]):
    return {"status": "updated", "version": "1.1"}

@router.delete("/contracts/{name}")
def deregister_contract(name: str):
    return {"status": "deregistered"}
