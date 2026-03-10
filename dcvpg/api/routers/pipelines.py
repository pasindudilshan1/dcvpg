from fastapi import APIRouter, HTTPException
from typing import List, Dict
import os

router = APIRouter()


def _get_store():
    from dcvpg.engine.report_store import ReportStore
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    base_dir = os.path.dirname(os.path.abspath(config_path))
    return ReportStore(base_dir)


@router.get("/pipelines", response_model=List[Dict])
def list_pipelines():
    """Return the latest validation run per pipeline."""
    runs = _get_store().get_runs()
    # Keep only the most recent run per pipeline_name
    latest: Dict[str, dict] = {}
    for r in runs:
        name = r.get("pipeline_name", "")
        if name not in latest or r.get("run_at", "") > latest[name].get("run_at", ""):
            latest[name] = r
    return [
        {
            "pipeline_name": name,
            "status": r.get("status", "UNKNOWN"),
            "violations_count": r.get("violations_count", 0),
            "rows_processed": r.get("rows_processed", 0),
            "last_run": r.get("run_at"),
            "violation_details": r.get("violation_details", []),
        }
        for name, r in latest.items()
    ]


@router.get("/pipelines/{name}/health")
def pipeline_health(name: str):
    runs = _get_store().get_runs()
    pipeline_runs = [r for r in runs if r.get("pipeline_name") == name]
    if not pipeline_runs:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    latest = max(pipeline_runs, key=lambda r: r.get("run_at", ""))
    return {
        "status": latest.get("status"),
        "last_run": latest.get("run_at"),
        "failed_batches": sum(1 for r in pipeline_runs if r.get("status") == "FAILED"),
    }
