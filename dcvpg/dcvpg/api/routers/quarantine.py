from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter()

@router.get("/quarantine")
def list_quarantine_batches(pipeline: Optional[str] = None):
    # Dummy list
    return [{
        "batch_id": "q_20260309_001",
        "pipeline_name": "orders_pipeline",
        "contract_name": "orders_raw",
        "violation_type": "FIELD_MISSING",
        "rows_affected": 14823,
        "resolved": False
    }]

@router.patch("/quarantine/{id}/resolve")
def resolve_quarantine(id: str, replay: bool = False):
    if id != "q_20260309_001":
        raise HTTPException(status_code=404, detail="Quarantine batch not found")
        
    response = {"status": "RESOLVED", "batch_id": id}
    if replay:
        # Trigger replay logic via orchestrator/CLI
        response["replay_status"] = "TRIGGERED"
        
    return response
