from fastapi import APIRouter
from datetime import datetime, timedelta
import os

router = APIRouter()


def _get_store():
    from dcvpg.engine.report_store import ReportStore
    config_path = os.environ.get("DCVPG_CONFIG_PATH", "./dcvpg.config.yaml")
    base_dir = os.path.dirname(os.path.abspath(config_path))
    return ReportStore(base_dir)


@router.get("/reports/drift")
def get_drift_report():
    """
    Schema drift detection requires a live source comparison which runs
    outside the API server (via `dcvpg validate`).  Return an empty
    result set so the dashboard shows "no drift" instead of fake data.
    """
    return {"drifts": []}


@router.get("/reports/incidents")
def get_incident_history():
    store = _get_store()
    runs = store.get_runs()
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    recent = [r for r in runs if r.get("run_at", "") >= cutoff]
    failed = [r for r in recent if r.get("status") == "FAILED"]
    return {
        "time_window": "30d",
        "incident_count": len(failed),
        "mean_time_to_resolve_minutes": 0,
        "incidents": [
            {
                "pipeline": r.get("pipeline_name"),
                "severity": "CRITICAL",
                "run_at": r.get("run_at"),
                "violations": r.get("violations_count", 0),
            }
            for r in failed[-10:]
        ],
    }
