# Changelog

All notable changes to DCVPG are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.4.6] — 2026-03-12

### Fixed
- `RootCauseAgent.analyze_incident()` in `rca_agent/rca.py` was a hardcoded stub returning a fake commit reference; now inherits `BaseAgent` and delegates to `ReportBuilder.build_rca_report()` which calls Claude via `call_llm()` with a structured prompt, and falls back to a template report if the LLM is unavailable
- `GitHubClient` in `auto_healer/github.py` had all three methods mocked (`create_branch`, `create_commit`, `create_pull_request` all returned hardcoded values); now uses real GitHub REST API v3 calls via `httpx` — creates branches from live HEAD SHA, commits files with base64-encoded content (handles create and update), and opens real PRs returning the actual HTML URL

---

## [1.4.5] — 2026-03-12

### Fixed
- `AlertManager._initialize_alerters()` crashed with `'NoneType' object has no attribute 'get'` when any alerter (pagerduty, teams, custom_alerter) was absent from config — `model_dump()` serializes missing optional alerters as `None`, and `dict.get(key, {})` returns `None` (not `{}`) when the key exists with a `None` value; fixed by using `or {}` pattern
- Dashboard: replaced deprecated Streamlit `use_container_width=True` with `width='stretch'` in all four pages (violations, contract_registry, quarantine, ownership)

---

## [1.4.4] — 2026-03-12

### Fixed
- `SlackAlerter`, `PagerDutyAlerter`, `WebhookAlerter` — all three had the actual HTTP call commented out and only logged `DUMMY DISPATCH`; now use `httpx.post()` with timeout and proper error handling
- `SlackAlerter` silently returned `False` when the `webhook_env` variable name was set in config but the env var itself was not exported in the running process — added clear `logger.warning` explaining exactly what is missing, and added `webhook_url` as a direct URL fallback (useful for dev without env var setup)
- `AlertManager.dispatch_alert()` never checked the return value of `send_alert()` — alerter failures (missing URL, HTTP errors) were completely invisible; now logs a `WARNING` when `send_alert` returns `False`
- `dcvpg validate` CLI printed nothing when alert dispatch failed/succeeded; now shows `🔔 Alerts dispatched via: SlackAlerter` on success or `ℹ️ No alerters enabled` when config has no active channels
- Autowatch background thread was only started inside the API server (`dcvpg serve api`); `dcvpg serve dashboard` had no validation loop. Both serve commands now start autowatch when `autowatch.enabled: true`
- Autowatch first validation run now happens **immediately** on startup instead of waiting one full `interval_seconds`
- Extracted shared autowatch logic into `dcvpg/engine/autowatch.py` (`start_if_enabled(config_path)`) to eliminate duplicated threading code

---

## [1.4.2] — 2026-03-12

### Changed
- `dcvpg watch` now reads `autowatch.interval_seconds` from config automatically; `--interval` flag overrides it. No need to pass a value manually if config is set
- Dashboard overview page: removed `<meta>` auto-refresh; replaced with a manual **Refresh** button so the user controls when to reload

### Fixed
- Autowatch background thread only runs when the API server (`uvicorn`) is started; `dcvpg watch` is the correct way to run continuous validation without the server

---

## [1.4.1] — 2026-03-12

### Added
- `autowatch` config block in `dcvpg.config.yaml` — when `enabled: true`, the API server automatically starts a background thread that runs validation every `interval_seconds` (default 60); alerts fire on failure; dashboard reflects each run automatically. When `enabled: false` (default), validation is manual only via `dcvpg validate --all` or `dcvpg watch`

---

## [1.4.0] — 2026-03-12

### Added
- `dcvpg watch --interval N` command — continuously runs `dcvpg validate --all` every N seconds; alerts fire automatically on failure; dashboard updates after each run
- Automatic alert dispatch in `dcvpg validate` — on contract failure, `AlertManager` is invoked to fire Slack, PagerDuty, or custom alerts if configured in `dcvpg.config.yaml`
- Dashboard overview page auto-refreshes every 30 seconds via `<meta http-equiv="refresh">`; configurable via `DCVPG_DASHBOARD_REFRESH_SECS` env var

---

## [1.3.9] — 2026-03-12

### Fixed
- `GET /reports/drift` — was always returning `{"drifts": []}` (stub); now performs real schema drift detection by fetching a live sample from each contract's source, inferring the column schema via `infer_schema_from_dataframe`, and diffing against the contract declaration using the existing `compute_schema_diff` engine

---

## [1.3.8] — 2026-03-12

### Fixed
- `AllowedValuesRule` — `series.isin()` and `.unique()` both crash with `TypeError: unhashable type: 'dict'` on columns containing JSON objects; rule now skips entirely for `type: json` fields and falls back to `.apply(str).unique()` for sample values on other unhashable columns

---

## [1.3.7] — 2026-03-10

### Fixed
- `GET /pipelines`, `GET /quarantine`, `GET /reports/incidents`, `GET /reports/drift` API endpoints were all hardcoded mock data (`orders_pipeline`, `q_20260309_001`, hard-coded incident counts, etc.); replaced with a lightweight JSONL file store (`engine/report_store.py`) that persists real validation runs and quarantine events under `{project}/.dcvpg_data/`
- `dcvpg validate` now persists each run and every quarantine event to the store so the dashboard immediately reflects actual validation results- `AllowedValuesRule` — `series.isin()` and `.unique()` both crash with `TypeError: unhashable type: 'dict'` on columns containing JSON objects; rule now skips gracefully for `type: json` fields and falls back to `.apply(str).unique()` for unhashable sample values in all other cases- Schema drift endpoint now returns an empty `{"drifts": []}` payload instead of fabricated `orders_raw` drift data

---

## [1.3.6] — 2026-03-10

### Fixed
- `RULE_CRASH` on columns containing nested JSON objects (`dict`/`list` values) — `TypeRule` and `UniquenessRule` both called `.unique()` which raises `TypeError: unhashable type: 'dict'`; now falls back to `.apply(str).unique()` safely
- Profiler now infers `type: json` (instead of `type: string`) for columns containing `dict` or `list` values, so generated contracts correctly type nested fields and avoid false type-mismatch violations on re-validation
- API `/contracts` endpoint was hardcoded to return a single dummy `orders_raw` contract; now reads from the real contract registry using `DCVPG_CONFIG_PATH` env var, so the dashboard reflects actual deployed contracts
- Dashboard contract registry page — `pyarrow.lib.ArrowInvalid` when rendering schema table with mixed-type `allowed_values` column (e.g. integer list in one contract, string list in another); list/dict cells are now serialised to comma-separated strings before passing to `st.dataframe`

---

## [1.3.5] — 2026-03-10

### Fixed
- `dcvpg generate` — crashed with `TypeError: unhashable type: 'dict'` when profiling REST API responses containing nested JSON objects (e.g. JSONPlaceholder `/users` with `address`, `company` fields); profiler now converts `dict`/`list` columns to strings before computing `nunique()` and `sample_values`

---

## [1.3.4] — 2026-03-10

### Fixed
- Airflow operator (`orchestrators/airflow/operators/contract_validator.py`) — hardcoded `PostgresConnector` replaced with full connector map (`postgres`, `mysql`, `snowflake`, `bigquery`, `s3`, `gcs`, `rest`, `file`)
- Prefect task (`orchestrators/prefect/tasks/contract_validator_task.py`) — same hardcoded connector bug fixed with full connector map
- Dagster op (`orchestrators/dagster/ops/contract_validator_op.py`) — same hardcoded connector bug fixed with full connector map
- Airflow DAG template (`templates/airflow_dag.py.template`) — hardcoded `PostgresConnector` in scaffolded DAG replaced with full connector map
- Prefect flow template (`templates/prefect_flow.py.template`) — same template connector bug fixed

---

## [1.3.3] — 2026-03-10

### Fixed
- `dcvpg validate` — REST connector (and all other connector types: `mysql`, `snowflake`, `bigquery`, `s3`, `gcs`) were unavailable in the CLI; `_get_connector` in `validate.py` now uses the same full connector map as `generate`

---

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
