from fastapi import APIRouter
from typing import Optional
import os

router = APIRouter()


def _get_store():
    from dcvpg.engine.report_store import ReportStore
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    base_dir = os.path.dirname(os.path.abspath(config_path))
    return ReportStore(base_dir)


@router.get("/quarantine")
def list_quarantine_batches(pipeline: Optional[str] = None):
    return _get_store().get_quarantine_events(pipeline=pipeline)


@router.patch("/quarantine/{id}/resolve")
def resolve_quarantine(id: str, replay: bool = False, discard: bool = False):
    store = _get_store()
    found = store.resolve_batch(id)
    if not found:
        return {"status": "NOT_FOUND", "batch_id": id}
    response = {"status": "RESOLVED", "batch_id": id}
    if replay:
        response["replay_status"] = "TRIGGERED"
    return response
