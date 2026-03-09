# Changelog

All notable changes to DCVPG are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

## [1.3.1]

## [1.3.0] — 2026-03-09

### Added
- `dcvpg serve api` CLI command — starts the FastAPI REST API via uvicorn without needing to know uvicorn directly
- `dcvpg serve dashboard` CLI command — resolves the installed Streamlit dashboard path automatically; no repo clone required

### Fixed
- Dashboard could not be started from an installed package (`streamlit run dcvpg/dashboard/app.py` failed outside the repo); `dcvpg serve dashboard` resolves the correct path via `importlib`

---

## [1.2.0] — 2026-03-09

### Added
- GCS connector (`gcs_connector.py`)
- `config/config_validator.py` for pre-flight config checks
- Dashboard pages 02–06 (contract registry, violations, schema drift, quarantine, ownership)
- CLI commands: `register`, `diff`, `status`, `replay`, `mcp-server`
- MCP server support files: `dcvpg_client.py`, `auth.py`, tool stubs
- AI agent: `base_agent.py`, `profiler.py`, `fix_proposer.py`, `schema_differ.py`
- Anomaly detectors: `volume_detector.py`, `null_rate_detector.py`, `distribution_detector.py`
- `AnomalyDetectorAgent` and `BaselineStore`
- `ReportBuilder` for LLM-powered RCA reports
- Templates: `airflow_dag.py.template`, `prefect_flow.py.template`, `github_workflow.yml.template`
- Migrations: `002_alerts.sql`, `003_snapshots.sql`, `004_baselines.sql`
- Infra: `Dockerfile`, `docker-compose.prod.yml`, `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/configmap.yaml`
- GitHub Actions: `ci.yml`, `cd.yml`, `contract_check.yml`
- Tests: `test_contract_loader.py`, `test_validator.py`, `test_connectors.py`, `test_quarantine_engine.py`, `test_api_endpoints.py`, `test_1m_row_batch.py`
- Documentation: `quickstart.md`, `contract_authoring.md`, `connectors.md`, `custom_rules.md`, `mcp_setup.md`, `api_reference.md`

### Fixed
- CLI entry point in `pyproject.toml`: `cli.main:cli` → `dcvpg.cli.main:cli`
- `DCPVGConfig` typo in `config_loader.py` → `DCVPGConfig`
- Slack/PagerDuty alerters: env var names were passed as URLs; now resolved via `os.environ.get()`
- `alert_manager.py`: broken `load_custom_rule` import replaced with `importlib`-based loader
- `auto_healer/agent.py`: `report.batch_id` field doesn't exist; fixed to accept `batch_id` parameter
- All orchestrator operators: bare `from engine.` imports → `from dcvpg.engine.`
- `api/main.py`: Prometheus metrics server now wired on startup; `/metrics` endpoint added
- `mcp_server/server.py`: was 3 tools; all 10 tools now implemented
- `engine/validator.py`: `row_count_min`/`row_count_max` were parsed but never validated; now checked
- `infra/docker-compose.yml`: wrong Dockerfile context path; dashboard service was missing

---

## [1.0.0] — 2024-01-15

### Added
- Initial release of DCVPG framework
- Core engine: `ContractSpec`, `Validator`, `QuarantineEngine`, `ContractRegistry`
- Built-in rules: schema presence, type, format, nullability, range, allowed values, uniqueness, freshness
- Connectors: PostgreSQL, File (CSV/JSON/Parquet)
- Alerting: Slack, PagerDuty
- AI agents: ContractGeneratorAgent, AutoHealerAgent, RootCauseAgent (initial stubs)
- CLI: `dcvpg init`, `dcvpg generate`, `dcvpg validate`
- FastAPI REST API with authentication
- Streamlit Dashboard (overview page)
- MCP Server (3 initial tools)
- Airflow, Prefect, Dagster operators
- Docker Compose development environment
- Migration 001 (core tables) and 005 (MCP audit)
