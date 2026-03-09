from fastapi import APIRouter

router = APIRouter()

@router.get("/reports/drift")
def get_drift_report():
    return {
        "pipeline": "orders_pipeline",
        "contract": "orders_raw",
        "drift_detected": True,
        "diff": {
            "added_fields": [],
            "removed_fields": ["total_amount"],
            "type_changed": {}
        }
    }

@router.get("/reports/incidents")
def get_incident_history():
    return {
        "time_window": "30d",
        "incident_count": 2,
        "mean_time_to_resolve_minutes": 18.5,
        "incidents": [
            {"id": "inc_001", "pipeline": "orders", "severity": "CRITICAL", "resolved_in_mins": 25},
            {"id": "inc_002", "pipeline": "customers", "severity": "WARNING", "resolved_in_mins": 12}
        ]
    }
