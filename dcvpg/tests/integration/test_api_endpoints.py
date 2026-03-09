"""Integration tests for the DCVPG FastAPI endpoints."""
import os
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    os.environ.setdefault("DCVPG_API_KEY", "test-key")
    from dcvpg.api.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "test-key"}


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_contracts_list_requires_auth(client):
    resp = client.get("/api/v1/contracts")
    assert resp.status_code == 403


def test_contracts_list_authorized(client, auth_headers):
    resp = client.get("/api/v1/contracts", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_pipelines_list_authorized(client, auth_headers):
    resp = client.get("/api/v1/pipelines", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_quarantine_list_authorized(client, auth_headers):
    resp = client.get("/api/v1/quarantine", headers=auth_headers)
    assert resp.status_code in (200, 404)


def test_generate_contract_endpoint(client, auth_headers):
    payload = {"source_conn": "test_conn", "table": "test_table"}
    resp = client.post("/api/v1/contracts/generate", json=payload, headers=auth_headers)
    # May return 200 or 422; we just verify auth works
    assert resp.status_code != 403


def test_metrics_endpoint(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
