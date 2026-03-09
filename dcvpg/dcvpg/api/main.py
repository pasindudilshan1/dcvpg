from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from .routers import contracts, pipelines, quarantine, reports, generate
import os

app = FastAPI(
    title="DCVPG Data Contract Validation API",
    description="Core API for Data Contract Validator & Pipeline Guardian",
    version="1.0.0"
)

# In-memory mock DBs for testing
fake_contracts_db = []
fake_pipelines_db = []
fake_quarantine_db = []

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Depends(api_key_header)):
    # Hardcode for simple verification, will use env in real usage
    expected = os.environ.get("DCVPG_API_KEY", "my-secret-key")
    if api_key == expected or (api_key and api_key.replace("Bearer ", "") == expected):
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# Routes included above at module level

app.include_router(contracts.router, prefix="/api/v1", tags=["Contracts"], dependencies=[Depends(get_api_key)])
app.include_router(pipelines.router, prefix="/api/v1", tags=["Pipelines"], dependencies=[Depends(get_api_key)])
app.include_router(quarantine.router, prefix="/api/v1", tags=["Quarantine"], dependencies=[Depends(get_api_key)])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"], dependencies=[Depends(get_api_key)])
app.include_router(generate.router, prefix="/api/v1", tags=["AI Generation"], dependencies=[Depends(get_api_key)])

@app.on_event("startup")
async def startup():
    from dcvpg.monitoring.metrics import start_metrics_server
    start_metrics_server(port=int(os.environ.get("METRICS_PORT", "9090")))


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
