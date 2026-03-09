from fastapi import APIRouter, HTTPException
from typing import List, Dict

router = APIRouter()

@router.get("/pipelines", response_model=List[Dict])
def list_pipelines():
    return [{"pipeline_name": "orders_pipeline", "status": "HEALTHY", "violations_count": 0}]

@router.get("/pipelines/{name}/health")
def pipeline_health(name: str):
    if name != "orders_pipeline":
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"status": "HEALTHY", "last_run": "2026-03-09T10:00:00Z", "failed_batches": 0}
