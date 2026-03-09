# API Reference

The DCVPG REST API runs on FastAPI. Interactive docs are available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

## Authentication

All endpoints (except `/health` and `/metrics`) require an API key passed as the `Authorization` header:

```
Authorization: <api-key>
# or
Authorization: Bearer <api-key>
```

## Endpoints

### Health

**`GET /health`**  
Returns API health status. No auth required.

```json
{"status": "ok"}
```

---

### Contracts

**`GET /api/v1/contracts`**  
List all registered contracts.

**`GET /api/v1/contracts/{name}`**  
Get a specific contract by name.

**`POST /api/v1/contracts`**  
Register a new contract (body: contract YAML as JSON).

**`DELETE /api/v1/contracts/{name}`**  
Unregister a contract.

**`POST /api/v1/contracts/generate`**  
AI-generate a contract from a live data source.

```json
{"source_conn": "postgres_main", "table": "orders"}
```

---

### Pipelines

**`GET /api/v1/pipelines`**  
List all pipeline health records.

**`GET /api/v1/pipelines/{name}/health`**  
Get the most recent validation report for a pipeline.

---

### Quarantine

**`GET /api/v1/quarantine`**  
List all quarantined batches.

**`GET /api/v1/quarantine/{batch_id}`**  
Get details of a specific quarantined batch.

**`PATCH /api/v1/quarantine/{batch_id}/resolve`**  
Resolve (replay or discard) a quarantined batch.

```json
{"replay": true}   // re-validate and release if passes
{"discard": true}  // permanently drop the batch
```

---

### Reports

**`GET /api/v1/reports/incidents`**  
Incident summary. Optional query params: `?days=7`

**`GET /api/v1/reports/drift`**  
Schema drift report across all contracts.

---

## Error Responses

| Code | Description                              |
|------|------------------------------------------|
| 403  | Missing or invalid API key               |
| 404  | Contract / pipeline / batch not found    |
| 422  | Validation error in request body         |
| 500  | Internal server error (check API logs)   |

## Metrics

**`GET /metrics`**  
Prometheus-formatted metrics. No auth required. Scrape with Prometheus at this endpoint.
