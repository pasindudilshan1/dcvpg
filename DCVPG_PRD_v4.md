# Data Contract Validator & Pipeline Guardian (DCVPG)
## Product Requirements Document — v4.0

---

| Field | Value |
|---|---|
| **Version** | 4.0.0 |
| **Date** | March 2026 |
| **Status** | Draft — Ready for Engineering Review |
| **Audience** | Data Engineers, Platform Engineers, Tech Leads |
| **Changelog** | v4.0 — Corrected two-layer architecture (framework vs user project); generic structure; `dcvpg init` command; `dcvpg.config.yaml` spec; full AI + MCP + publishing integrated into one unified structure |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [Stakeholders & Users](#4-stakeholders--users)
5. [Architecture Philosophy — Two Layers](#5-architecture-philosophy--two-layers)
6. [Functional Requirements](#6-functional-requirements)
7. [Technology Stack — Full Stack](#7-technology-stack--full-stack)
8. [System Architecture](#8-system-architecture)
9. [Data Model](#9-data-model)
10. [API Specification](#10-api-specification)
11. [Project Structure — Layer 1: DCVPG Framework](#11-project-structure--layer-1-dcvpg-framework)
12. [Project Structure — Layer 2: User Project](#12-project-structure--layer-2-user-project)
13. [Configuration — dcvpg.config.yaml](#13-configuration--dcvpgconfigyaml)
14. [Contract Definition Specification](#14-contract-definition-specification)
15. [Extensibility — Custom Connectors & Rules](#15-extensibility--custom-connectors--rules)
16. [AI Agent Layer](#16-ai-agent-layer)
17. [MCP Server Integration](#17-mcp-server-integration)
18. [CLI Command Reference](#18-cli-command-reference)
19. [Implementation Roadmap](#19-implementation-roadmap)
20. [Non-Functional Requirements](#20-non-functional-requirements)
21. [Security Considerations](#21-security-considerations)
22. [Open Source Publishing Strategy](#22-open-source-publishing-strategy)
23. [End-to-End User Journey](#23-end-to-end-user-journey)
24. [Distribution & Publishing Tech Stack](#24-distribution--publishing-tech-stack)
25. [Success Metrics](#25-success-metrics)
26. [Risks & Mitigations](#26-risks--mitigations)
27. [Open Questions](#27-open-questions)
28. [Glossary](#28-glossary)
29. [Document Sign-Off](#29-document-sign-off)

---

## 1. Executive Summary

Data pipelines are the critical infrastructure of every modern data-driven organisation. Yet the #1 cause of pipeline failure is silent, unexpected schema changes introduced by upstream data producers. When a field is renamed, a type is changed, or a new nullable column is added without notice, downstream pipelines break, dashboards go dark, and business decisions are made on stale or zero data.

**DCVPG (Data Contract Validator & Pipeline Guardian)** is a free, open-source Python framework that solves this problem by introducing a formal, enforced contract layer between every data producer and every data consumer. Any data engineer on Earth can install it with one command, plug it into their existing pipeline in minutes, and connect it to their AI assistant in under 10 minutes.

### What DCVPG Does

- **Validates** 100% of incoming data against a declared contract on every pipeline run
- **Quarantines** bad data before it reaches the warehouse — the dashboard always shows clean data
- **Alerts** the right engineers via Slack within 60 seconds of any violation
- **Heals** itself — an AI agent diagnoses violations and opens a fix PR automatically
- **Generates** contracts from live data sources using AI — no manual YAML writing required
- **Exposes** an MCP Server so any AI assistant (Claude, Cursor) can query pipeline health conversationally

### Design Principle

DCVPG is a **generic framework**, not a hardcoded tool. It knows nothing about any user's business — no field names, no table names, no company-specific logic are baked in. Users bring their own contracts, their own connectors, and their own rules. DCVPG provides the engine; users build the car.

> **Business Impact:** Pipeline incidents cost an average of 4+ engineering hours each. At a mid-size company running 20+ pipelines, this is 80–200+ lost hours per month. DCVPG targets a 90% reduction in incident MTTR and a 95% reduction in bad data reaching the warehouse.

---

## 2. Problem Statement

### 2.1 The Core Problem

Modern data engineering teams work in an environment where data is produced by many independent teams — backend engineers, third-party APIs, event tracking systems, and operational databases. These producers evolve their schemas continuously without coordinating with downstream consumers.

| Problem | Frequency | Avg. Detect Time | Avg. Resolution Time | Business Impact |
|---|---|---|---|---|
| Field renamed in source API | Weekly | 6–8 hours (next morning) | 2–4 hours | Dashboard shows 0 or NULL |
| Data type change (string → int) | Bi-weekly | At next pipeline run | 1–3 hours | Silent failures, wrong aggregates |
| New NOT NULL field added | Monthly | 2–6 hours | 1–2 hours | Insert errors, data loss |
| Field deleted from source | Monthly | 6–8 hours | 2–4 hours | Downstream reports break |
| Value range violation | Weekly | Hours to days | 4–8 hours | Incorrect KPIs, bad decisions |

### 2.2 Why Existing Solutions Fall Short

- **Ad-hoc monitoring:** One-off checks that are never maintained and miss new failure modes
- **Manual communication:** Slack messages and Confluence pages are unreliable and not enforced
- **Schema registries (Confluent etc.):** Solve Kafka schemas only — do not cover REST APIs, databases, or files
- **Great Expectations standalone:** Powerful but requires per-pipeline setup with no orchestration integration or contract ownership model
- **Commercial tools (Monte Carlo, Soda):** $50K+/year, vendor lock-in, black-box logic — unaffordable for most teams

---

## 3. Goals & Non-Goals

### 3.1 Goals

1. Provide a **generic framework** — no business-specific names or logic baked in; works for any company, any domain
2. Allow users to define contracts in human-readable YAML and store them in their own Git repository
3. Validate 100% of incoming data against its contract on every pipeline run with zero manual intervention
4. Detect and surface contract violations within **60 seconds** of ingestion
5. Quarantine bad data automatically so it never reaches the data warehouse
6. Alert the correct team members via Slack within **2 minutes** of detection
7. Be installable globally via `pip install dcvpg` with no infrastructure required to try
8. Support all major data sources: PostgreSQL, MySQL, Snowflake, BigQuery, REST APIs, Kafka, S3/GCS, flat files
9. Support all major orchestrators: Apache Airflow, Prefect, Dagster — and plain Python
10. Allow users to extend the framework with **custom connectors** and **custom validation rules**
11. Expose an **MCP Server** so any AI assistant can query pipeline health conversationally
12. Generate contracts from live data sources automatically using AI (`dcvpg generate`)
13. Be deployable with Docker Compose in under **30 minutes**

### 3.2 Non-Goals

- DCVPG does not fix or transform bad data automatically — it quarantines and alerts; the AI proposes fixes that humans approve
- DCVPG is not a data lineage tool — lineage tracking is out of scope for v1
- DCVPG is not a schema migration tool — it detects drift; it does not auto-migrate
- DCVPG does not replace Great Expectations — it wraps and orchestrates it
- Real-time streaming validation is not supported in v1 — batch pipeline focus only
- DCVPG does not store or access user data — it reads metadata and statistics only

---

## 4. Stakeholders & Users

| Stakeholder | Role | Primary Need | How They Use DCVPG |
|---|---|---|---|
| Data Engineers | Primary Users | Know when pipelines break before stakeholders notice | Run `dcvpg init`, write contracts, add operator to DAGs, use MCP with Claude |
| Backend Engineers | Data Producers | Understand impact of API/DB schema changes | Receive alerts when their changes break a contract; approve AI fix PRs |
| Analytics Engineers | Data Consumers | Trust that data in the warehouse is correct | Passive beneficiary; view contract status in dashboard |
| Data Engineering Lead | Decision Maker | Reduce pipeline incident MTTR, enforce data quality standards | Review metrics dashboard, manage contract ownership, approve roadmap |
| Business / Finance | End Users | Accurate, available dashboards | Indirect — benefit from stable, validated pipelines |
| DevOps / Platform Eng. | Infrastructure | Reliable deployment, monitoring hooks | Deploy Docker stack, configure infra, manage secrets |
| Open Source Community | External Contributors | Free, reliable data contract tooling for their own pipelines | Install via pip, contribute PRs, report issues, extend with custom rules |

---

## 5. Architecture Philosophy — Two Layers

This is the most important design decision in the project. DCVPG is built as **two completely separate layers**.

### Layer 1 — DCVPG Framework (What You Build and Publish)

This is the open-source tool published on PyPI. It is **completely generic**. It contains no business field names, no company-specific table names, no hardcoded pipeline logic. It is a pure framework — an engine that works for any company, any domain, any data.

```
What DCVPG Framework knows:    What DCVPG Framework does NOT know:
✅ How to load a YAML contract  ❌ What fields are in your orders table
✅ How to validate field types  ❌ What your customer ID format looks like
✅ How to connect to Postgres   ❌ What your pipeline is called
✅ How to send a Slack alert    ❌ What your team's Slack channel is
✅ How to open a GitHub PR      ❌ Which GitHub repo your contracts live in
```

### Layer 2 — User Project (What Each User Creates)

Every user creates their own project using `dcvpg init`. This project contains their contracts, their config, their custom connectors, their pipeline DAGs. DCVPG reads this project at runtime but never ships any of it.

```
What lives in user's project:
✅ contracts/orders.yaml          (their pipeline contracts)
✅ dcvpg.config.yaml              (their configuration)
✅ custom_connectors/crm.py       (their proprietary data sources)
✅ custom_rules/currency_rule.py  (their business-specific validation)
✅ pipelines/airflow/orders.py    (their Airflow DAGs)
```

### Why This Matters

| If we hardcode names | If we keep it generic |
|---|---|
| Only works for ShopFast | Works for any company |
| Users cannot customise | Users extend with custom rules/connectors |
| Cannot publish on PyPI | Any engineer can `pip install dcvpg` |
| Breaks when business changes | Framework never changes for business reasons |
| One user | Millions of users |

---

## 6. Functional Requirements

### 6.1 Framework Initialisation — `dcvpg init`

When a user runs `dcvpg init` in a new directory, the framework scaffolds a complete, ready-to-use user project. This is the zero-to-running experience.

```bash
$ dcvpg init my-data-platform

Creating project: my-data-platform/
  ✅ dcvpg.config.yaml          (master config — edit this first)
  ✅ contracts/                 (put your contract YAMLs here)
  ✅ contracts/_schema/         (JSON Schema for YAML validation)
  ✅ custom_connectors/         (extend for your proprietary sources)
  ✅ custom_rules/              (extend for your business-specific rules)
  ✅ pipelines/airflow/         (example Airflow DAG — copy and adapt)
  ✅ pipelines/prefect/         (example Prefect flow)
  ✅ tests/                     (example contract tests)
  ✅ .github/workflows/         (CI: validate contracts on every PR)

Next steps:
  1. Edit dcvpg.config.yaml — add your data source connections
  2. Run: dcvpg generate --source <your-db-connection>
  3. Review the generated contract YAML
  4. Run: dcvpg validate --all
  5. Add DataContractValidatorOperator to your first pipeline
```

### 6.2 Contract Definition Engine

Contracts are plain YAML files stored in the user's own Git repository. Each contract describes the expected schema, quality rules, ownership, and SLA for one data source. The user owns and writes these files; DCVPG reads and enforces them.

The contract schema is fully generic — field names, types, and rules are all user-defined:

```yaml
# Example: user writes this for their own pipeline
# DCVPG reads it — knows nothing about "orders" or "total_price"

contract:
  name: orders_raw                  # user chooses this name
  version: 1.0
  description: Raw orders from payment API
  owner_team: data-engineering
  source_owner: payments-team
  sla_freshness_hours: 6
  pipeline_tags: [critical, revenue]

  schema:
    - field: order_id               # user defines their own fields
      type: string
      nullable: false
      unique: true

    - field: total_amount
      type: float
      nullable: false
      min: 0.0
      max: 1000000.0

    - field: currency
      type: string
      allowed_values: [USD, EUR, GBP, SGD, AED]

    - field: status
      type: string
      allowed_values: [pending, confirmed, shipped, cancelled, refunded]

    - field: customer_id
      type: string
      nullable: false
      format: uuid

    - field: created_at
      type: timestamp
      nullable: false

  custom_rules:                     # user can attach their own rule classes
    - rule: custom_rules.currency_rule.CurrencyValidator
      params:
        supported_currencies: [USD, EUR, GBP]
```

### 6.3 Contract Auto-Discovery & Registry

When DCVPG starts, it scans the user's contracts directory (defined in `dcvpg.config.yaml`) and automatically discovers, loads, and registers all contract YAML files. No manual registration required.

```
User drops a new file: contracts/services/inventory/stock_levels.yaml
         ↓
DCVPG detects it on next startup (or immediately if watch_mode: true)
         ↓
Validates the YAML against the contract JSON Schema
         ↓
Registers it in the PostgreSQL contract store
         ↓
Available immediately in the dashboard and MCP tools
```

### 6.4 Validation Engine

The Validation Engine runs every rule defined in a contract against incoming data. It is invoked by the orchestrator operator, the CLI, or the API — it does not care which.

| Validation Type | Description | Severity |
|---|---|---|
| Schema Presence | All required fields exist in the incoming data | CRITICAL |
| Type Validation | Field values match declared type (int, float, string, timestamp, bool) | CRITICAL |
| Nullability | Non-nullable fields contain no null values | CRITICAL |
| Uniqueness | Fields declared unique contain no duplicates | CRITICAL |
| Range Validation | Numeric fields within declared min/max bounds | Configurable |
| Format Validation | String fields match declared format (uuid, email, phone, date, regex) | Configurable |
| Allowed Values | Categorical fields contain only declared values | Configurable |
| Freshness Check | Data timestamp within SLA window | WARNING |
| Row Count Check | Row count within expected range | WARNING |
| Custom Rules | User-defined rule classes loaded from custom_rules/ | User-defined |

### 6.5 Quarantine System

When validation fails at CRITICAL severity, the entire batch is held in a quarantine table. It never touches the target warehouse. The dashboard freezes on the last known-good run rather than showing zero or wrong data.

```sql
-- Quarantine table — generic, works for any user's pipeline
quarantine_events (
  id                SERIAL PRIMARY KEY,
  pipeline_name     VARCHAR(255),     -- user's pipeline name
  contract_name     VARCHAR(255),     -- user's contract name
  contract_version  VARCHAR(50),
  batch_id          UUID,
  violation_type    VARCHAR(100),     -- e.g. FIELD_MISSING, TYPE_MISMATCH
  affected_field    VARCHAR(255),     -- the specific field that failed
  expected_value    TEXT,             -- what the contract expected
  actual_sample     TEXT,             -- what was found in the data
  rows_affected     INTEGER,
  total_rows        INTEGER,
  quarantined_at    TIMESTAMP,
  resolved          BOOLEAN DEFAULT FALSE,
  resolved_by       VARCHAR(255),
  resolved_at       TIMESTAMP
)
```

### 6.6 Alerting System

Alerts are structured and actionable. The user configures alerting destinations in `dcvpg.config.yaml`. DCVPG supports Slack, PagerDuty, Microsoft Teams, and generic webhooks out of the box. Users can implement custom alerters by extending `base_alerter.py`.

```
🚨 [CRITICAL] Contract Violation

Pipeline:      orders_raw  v1.0
Violation:     FIELD_MISSING — total_amount
Suggestion:    Found similar field: totalAmount (possible rename?)
Rows Affected: 14,823 / 14,823 (100%)
Action Taken:  All rows quarantined. Pipeline halted.
Dashboard:     Frozen on last successful run

Owners: @data-eng-team  @payments-team
Quarantine ID: q_20260309_001
Fix: AI Agent has opened PR #47 for review
```

### 6.7 Contract Versioning & Audit Log

Every contract change is tracked in Git (the user's own repo) and mirrored to the DCVPG PostgreSQL audit log. Engineers can see the full history: who changed what, when, and whether the change was breaking or non-breaking.

### 6.8 Dashboard — Pipeline Guardian UI

A Streamlit dashboard provides a real-time view of all registered pipelines, their health, violation history, and ownership. It reads from the DCVPG API — it knows nothing specific about any user's pipelines beyond what the contracts and validation reports say.

| Page | Contents |
|---|---|
| Overview | Total contracts, pass rate last 24h, active violations, at-risk pipelines |
| Contract Registry | All contracts: owner, version, last run status, SLA, tags |
| Violation History | Timeline of all violations: filter by pipeline, date, severity, team |
| Schema Drift | Side-by-side diff of contract vs current source schema for each pipeline |
| Quarantine Manager | View quarantined batches, mark resolved, trigger replay |
| Ownership Map | Matrix showing which team owns which pipelines |

---

## 7. Technology Stack — Full Stack

### Core Framework (v1)

| Layer | Technology | Version | Purpose | Justification |
|---|---|---|---|---|
| Language | Python | 3.11+ | Primary implementation language | Ecosystem, async support, DE community standard |
| Schema Enforcement | Pydantic | v2 | Contract YAML parsing and model validation | Fast, type-safe, Python-native |
| Data Validation | Great Expectations | 0.18+ | Statistical data validation engine | Industry standard, extensible, rich rule set |
| Contract Storage | YAML + Git | Any | Human-readable contract definitions in user's repo | Version-controlled, diff-friendly, reviewable |
| Runtime DB | PostgreSQL | 15+ | Contract store, audit log, quarantine table | ACID guarantees, JSON support, universally available |
| Airflow Integration | Apache Airflow | 2.8+ | DAG scheduling and operator | Industry standard orchestrator, largest DE community |
| Prefect Integration | Prefect | 2.x+ | Flow task for Prefect users | Fast-growing orchestrator, Python-native |
| Dagster Integration | Dagster | 1.x+ | Asset/op for Dagster users | Type-safe, asset-centric orchestration |
| Object Storage | AWS S3 / GCS | — | Quarantine storage for large batches | Cost-effective, durable, cloud-agnostic |
| Alerting | Slack SDK + PagerDuty + httpx | — | Real-time incident notification | Ubiquitous tools, extensible base class |
| Dashboard | Streamlit | 1.32+ | Contract health UI | Rapid development, Python-native |
| REST API | FastAPI | 0.110+ | HTTP interface for all system operations | Fast, async, auto-documented |
| CLI | Click | 8.x | Command-line interface (dcvpg init, generate, validate) | Pythonic, composable, widely used |
| Containerisation | Docker + Docker Compose | 24+ / 2.x | Local and production deployment | Reproducible, easy onboarding |
| CI/CD | GitHub Actions | — | Test, lint, publish on every tag | Git-native, free tier sufficient |
| Monitoring | Prometheus + Grafana | — | Pipeline and infrastructure metrics | Open source, integrates with Airflow |
| Secret Management | HashiCorp Vault / AWS Secrets Manager | — | All credentials and API keys | Security best practice |
| Testing | pytest | 7+ | Unit and integration tests | Python ecosystem standard |

### AI Agent Layer (v2)

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| LLM Reasoning | Claude API (claude-sonnet-4-6) | Latest | Root cause diagnosis, contract generation, RCA reports |
| Agent Framework | Python asyncio + custom agent loop | 3.11+ | Orchestrates multi-step autonomous actions |
| Schema Diffing | DeepDiff | 6.x | Structural comparison of contract vs live source schema |
| Statistical Analysis | scipy + numpy + pandas | Latest | Anomaly detection: Z-scores, distribution shift |
| GitHub Automation | PyGithub | 2.x | PR creation, commit, merge from Python |
| Slack Interactive | Slack Bolt SDK | 1.x | Approval buttons in Slack alert messages |
| Report Publishing | Confluence REST API / Notion API | — | Auto-publish RCA post-mortems |

### MCP & Distribution (v3)

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| MCP Server | Python mcp SDK (Anthropic) | Latest | Exposes DCVPG tools to AI assistants via MCP protocol |
| Async HTTP Client | httpx | 0.27+ | Async calls from MCP server to DCVPG REST API |
| Package Build | python-build + twine | Latest | Builds and publishes to PyPI |
| Docs Site | MkDocs + Material theme | Latest | Hosted documentation at docs.dcvpg.io |

---

## 8. System Architecture

### 8.1 Full Runtime Flow

```
USER'S DATA SOURCES (anything — user configures in dcvpg.config.yaml)
  └─ Databases:   PostgreSQL, MySQL, Snowflake, BigQuery, Oracle
  └─ REST APIs:   Any HTTP endpoint (Shopify, Stripe, internal APIs)
  └─ File Stores: S3, GCS, SFTP, local filesystem
  └─ Streaming:   Kafka topics (v2 roadmap)
  └─ Custom:      User extends base_connector.py for proprietary sources
         ↓
[1] DCVPG FRAMEWORK — CONTRACT LOADER
  └─ Reads dcvpg.config.yaml from user's project
  └─ Scans user's contracts/ directory for all YAML files
  └─ Parses + validates each contract using Pydantic ContractSpec
  └─ Loads user's custom_rules/ and custom_connectors/
         ↓
[2] DCVPG FRAMEWORK — VALIDATION ENGINE
  └─ Connects to user's data source via configured connector
  └─ Samples incoming batch data
  └─ Runs all contract rules: built-in + user custom rules
  └─ Classifies each result: PASS / WARNING / CRITICAL
  └─ Produces ValidationReport
         ↓
         ├── ALL PASS ✅                    ├── WARNING ⚠️                 └── CRITICAL ❌
         │                                  │                                   │
[3] PIPELINE CONTINUES             Slack WARNING alert              [4] QUARANTINE ENGINE
  └─ Normal ETL/ELT runs             Pipeline continues               └─ Writes batch to quarantine_events
  └─ Data loads to warehouse                                          └─ Tags with full violation metadata
  └─ last_run updated                                                 └─ Dashboard frozen on last good run
                                                                           │
                                                                   [5] ALERT ENGINE
                                                                     └─ Slack CRITICAL alert (with AI suggestion)
                                                                     └─ PagerDuty if enabled
                                                                     └─ Audit log written
                                                                           │
                                                                   [6] AI AUTO-HEALER AGENT (v2)
                                                                     └─ Wakes up on CRITICAL violation
                                                                     └─ Fetches live source schema
                                                                     └─ Computes diff vs contract
                                                                     └─ LLM diagnoses: rename/type/delete?
                                                                     └─ Opens GitHub PR with fix
                                                                     └─ Engineer approves → merged → replay
         ↓
[7] DASHBOARD + MCP SERVER
  └─ Dashboard: real-time pipeline health, violations, quarantine
  └─ MCP Server: any AI assistant can query live pipeline status
```

### 8.2 Orchestrator Integration (Generic Operator Pattern)

The `DataContractValidatorOperator` is completely generic. The user passes in the contract path and connection ID from their own config. DCVPG does not need to know anything about their pipeline.

```python
# User's Airflow DAG — they write this, plug in their own values
from dcvpg.airflow.operators import DataContractValidatorOperator

with DAG(dag_id='orders_pipeline', schedule='0 2 * * *') as dag:

    # One line to add DCVPG to any existing pipeline
    validate = DataContractValidatorOperator(
        task_id='validate_orders',
        contract='orders/orders_raw',       # path in user's contracts/ dir
        source_conn='postgres_orders_prod', # user's connection ID
        on_failure='quarantine_and_alert',
    )

    extract   = PythonOperator(task_id='extract',   ...)
    transform = PythonOperator(task_id='transform', ...)
    load      = PythonOperator(task_id='load',      ...)

    validate >> extract >> transform >> load
```

---

## 9. Data Model

All tables are generic — they store metadata about any user's pipeline contracts and violations.

| Table | Purpose | Key Fields |
|---|---|---|
| `contracts` | All registered contract definitions | id, name, version, owner_team, source_owner, yaml_content, tags, created_at, updated_at |
| `contract_history` | Full audit log of every contract change | id, contract_id, version, changed_by, change_type (breaking/non-breaking), diff_json, changed_at |
| `pipeline_runs` | Log of every pipeline execution and outcome | id, contract_id, batch_id, status, rows_processed, violations_count, duration_ms, run_at |
| `quarantine_events` | All quarantined data batches with full metadata | id, pipeline_name, contract_name, violation_type, affected_field, rows_affected, quarantined_at, resolved |
| `alert_log` | Record of every alert sent via any channel | id, pipeline_name, channel, alert_type, severity, payload_json, sent_at, acknowledged_at |
| `schema_snapshots` | Periodic snapshots of live source schema for drift detection | id, contract_id, inferred_schema_json, snapshotted_at, drift_detected |
| `baseline_stats` | Rolling statistical baselines for anomaly detection (v2) | id, contract_id, field_name, metric, value, window_days, computed_at |
| `mcp_audit_log` | Log of every AI tool call made via MCP Server | id, tool_name, called_by, params_json, result_summary, called_at |

---

## 10. API Specification

All endpoints are generic — they work for any user's pipelines and contracts.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/contracts` | List all registered contracts with current status | API Key |
| GET | `/api/v1/contracts/{name}` | Get contract detail, rules, ownership, history | API Key |
| POST | `/api/v1/contracts` | Register a new contract from YAML content | API Key |
| PUT | `/api/v1/contracts/{name}` | Update contract — creates new version in audit log | API Key |
| DELETE | `/api/v1/contracts/{name}` | Deregister a contract (does not delete YAML from user's repo) | API Key |
| POST | `/api/v1/validate` | Run on-demand validation: pass contract name + source conn | API Key |
| GET | `/api/v1/pipelines` | List all pipelines with last run status | API Key |
| GET | `/api/v1/pipelines/{name}/health` | Health status for one pipeline | API Key |
| GET | `/api/v1/quarantine` | List all quarantined batches with filter options | API Key |
| PATCH | `/api/v1/quarantine/{id}/resolve` | Mark quarantine event resolved + optional replay | API Key |
| GET | `/api/v1/reports/drift` | Schema drift report for all pipelines | API Key |
| GET | `/api/v1/reports/incidents` | Incident history with MTTR stats | API Key |
| POST | `/api/v1/contracts/generate` | Trigger AI contract generation from a source connection | API Key |
| POST | `/api/v1/webhooks/alert` | Inbound webhook for external alert routing | HMAC Sig |

---

## 11. Project Structure — Layer 1: DCVPG Framework

This is the codebase you build, maintain, and publish on PyPI. It is fully generic — no business names, no hardcoded field names, no company-specific logic anywhere.

```
dcvpg/                                      ← root of the published package
│
├── engine/                                 ← Core library (the heart of the framework)
│   ├── __init__.py
│   ├── contract_loader.py                  ← Loads ANY contract YAML from ANY path
│   ├── validator.py                        ← Validates ANY data against ANY contract
│   ├── registry.py                         ← Auto-discovers + registers all contracts
│   │                                          from user's contracts/ directory
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base_rule.py                    ← Abstract base class; users extend this
│   │   │                                      to write their own custom rules
│   │   ├── schema_rules.py                 ← Checks: required fields present
│   │   ├── type_rules.py                   ← Checks: field types match declaration
│   │   ├── quality_rules.py                ← Checks: null, range, format, allowed values
│   │   ├── freshness_rules.py              ← Checks: data within SLA freshness window
│   │   ├── uniqueness_rules.py             ← Checks: declared unique fields have no dups
│   │   └── custom_rule_loader.py           ← Dynamically loads user's custom_rules/
│   │
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base_connector.py               ← Abstract base class; users extend this
│   │   │                                      for proprietary/internal data sources
│   │   ├── postgres_connector.py
│   │   ├── mysql_connector.py
│   │   ├── snowflake_connector.py
│   │   ├── bigquery_connector.py
│   │   ├── rest_api_connector.py           ← Generic REST API connector
│   │   ├── s3_connector.py
│   │   ├── gcs_connector.py
│   │   ├── kafka_connector.py              ← v2 roadmap
│   │   └── file_connector.py              ← CSV, JSON, Parquet, AVRO
│   │
│   ├── quarantine_engine.py                ← Isolates bad data, writes to quarantine table
│   ├── reporting/
│   │   ├── schema_diff.py                  ← Computes diff between contract and live schema
│   │   └── violation_report.py             ← Formats ValidationReport for alerts/API
│   └── models.py                           ← Pydantic models: ContractSpec, FieldSpec,
│                                              ValidationReport, QuarantineEvent, etc.
│
├── orchestrators/                          ← One sub-package per supported orchestrator
│   ├── airflow/
│   │   ├── operators/
│   │   │   └── contract_validator.py       ← DataContractValidatorOperator (generic)
│   │   └── plugins/
│   │       └── dcvpg_plugin.py
│   ├── prefect/
│   │   └── tasks/
│   │       └── contract_validator_task.py  ← @task for Prefect flows
│   └── dagster/
│       └── ops/
│           └── contract_validator_op.py    ← @op for Dagster jobs
│
├── alerting/
│   ├── __init__.py
│   ├── base_alerter.py                     ← Abstract base class; users extend for
│   │                                          custom alert destinations
│   ├── alert_manager.py                    ← Routes alerts to configured destinations
│   ├── slack_alerter.py
│   ├── pagerduty_alerter.py
│   ├── teams_alerter.py                    ← Microsoft Teams
│   └── webhook_alerter.py                  ← Generic outbound webhook
│
├── api/
│   ├── main.py                             ← FastAPI application entrypoint
│   ├── routers/
│   │   ├── contracts.py
│   │   ├── pipelines.py
│   │   ├── quarantine.py
│   │   ├── reports.py
│   │   └── generate.py                     ← AI contract generation endpoint
│   ├── schemas.py                          ← Pydantic request/response models
│   └── auth.py                             ← API key authentication middleware
│
├── dashboard/
│   ├── app.py                              ← Streamlit main entrypoint
│   └── pages/
│       ├── 01_overview.py
│       ├── 02_contract_registry.py
│       ├── 03_violations.py
│       ├── 04_schema_drift.py
│       ├── 05_quarantine.py
│       └── 06_ownership.py
│
├── ai_agents/                              ← All AI-powered agents (optional: pip install dcvpg[ai])
│   ├── __init__.py
│   ├── base_agent.py                       ← Base class: LLM client, retry logic, logging
│   │
│   ├── auto_healer/                        ← Diagnoses violations + opens fix PRs
│   │   ├── __init__.py
│   │   ├── healer_agent.py                 ← Orchestrator: coordinates all healer steps
│   │   ├── schema_differ.py                ← Compares contract schema vs live source schema
│   │   ├── fix_proposer.py                 ← LLM generates updated contract YAML
│   │   ├── pr_manager.py                   ← Creates/merges GitHub PRs via PyGithub
│   │   └── prompts/
│   │       ├── diagnose_violation.txt       ← LLM prompt: what changed and why?
│   │       └── generate_fix.txt             ← LLM prompt: write the corrected contract YAML
│   │
│   ├── contract_generator/                 ← Generates contract YAML from live data sources
│   │   ├── __init__.py
│   │   ├── generator_agent.py              ← Orchestrator: sample → profile → generate
│   │   ├── profiler.py                     ← Profiles field types, nulls, ranges, formats
│   │   └── prompts/
│   │       └── generate_contract.txt        ← LLM prompt: write contract YAML from profile
│   │
│   ├── anomaly_detector/                   ← Catches valid-but-wrong data statistically
│   │   ├── __init__.py
│   │   ├── detector_agent.py               ← Orchestrator: runs all detectors, raises alerts
│   │   ├── baseline_store.py               ← Reads/writes 30-day rolling baselines
│   │   └── detectors/
│   │       ├── volume_detector.py           ← Z-score on row count vs baseline
│   │       ├── distribution_detector.py     ← Mean/median shift detection per field
│   │       └── null_rate_detector.py        ← Null rate spike detection per field
│   │
│   └── rca_agent/                          ← Writes post-mortem after every resolved incident
│       ├── __init__.py
│       ├── rca_agent.py                    ← Orchestrator: collect data → generate → publish
│       ├── report_builder.py               ← Assembles incident context for LLM
│       └── prompts/
│           └── write_postmortem.txt         ← LLM prompt: write structured RCA report
│
├── mcp_server/                             ← MCP Server (optional: pip install dcvpg[mcp])
│   ├── __init__.py
│   ├── server.py                           ← MCP entrypoint: registers all tools
│   ├── auth.py                             ← API key validation for MCP connections
│   ├── tools/
│   │   ├── pipeline_tools.py               ← get_pipeline_status, get_violation_detail
│   │   ├── contract_tools.py               ← get_contract_detail, create_fix_pr
│   │   ├── quarantine_tools.py             ← list_quarantine_batches, replay_quarantine
│   │   └── agent_tools.py                  ← generate_contract, get_incident_summary
│   └── dcvpg_client.py                     ← Async httpx client → DCVPG REST API
│
├── cli/
│   ├── __init__.py
│   ├── main.py                             ← Click CLI entrypoint (dcvpg command)
│   └── commands/
│       ├── init.py                         ← dcvpg init — scaffolds user project
│       ├── generate.py                     ← dcvpg generate — AI contract generation
│       ├── validate.py                     ← dcvpg validate — run validation manually
│       ├── register.py                     ← dcvpg register — add contract to store
│       ├── diff.py                         ← dcvpg diff — show schema drift
│       └── mcp.py                          ← dcvpg mcp-server start/stop/status/logs
│
├── config/
│   ├── config_loader.py                    ← Reads user's dcvpg.config.yaml
│   ├── config_validator.py                 ← Validates config against schema
│   └── config_schema.json                  ← JSON Schema for dcvpg.config.yaml
│
├── migrations/                             ← DCVPG's own database schema
│   ├── 001_init.sql                        ← Core tables: contracts, pipeline_runs, quarantine
│   ├── 002_alerts.sql                      ← Alert log table
│   ├── 003_snapshots.sql                   ← Schema snapshots for drift detection
│   ├── 004_baselines.sql                   ← Statistical baselines for anomaly detection
│   └── 005_mcp_audit.sql                   ← MCP call audit log
│
├── monitoring/
│   ├── metrics.py                          ← Prometheus metrics exporter
│   └── grafana.json                        ← Pre-built Grafana dashboard config
│
├── templates/                              ← Templates used by dcvpg init to scaffold user project
│   ├── dcvpg.config.yaml.template
│   ├── contract.yaml.template
│   ├── custom_connector.py.template
│   ├── custom_rule.py.template
│   ├── airflow_dag.py.template
│   ├── prefect_flow.py.template
│   └── github_workflow.yml.template
│
├── tests/                                  ← Framework tests only (not user's tests)
│   ├── unit/
│   │   ├── test_contract_loader.py
│   │   ├── test_validator.py
│   │   ├── test_rules.py
│   │   └── test_connectors.py
│   ├── integration/
│   │   ├── test_airflow_operator.py
│   │   ├── test_quarantine_engine.py
│   │   └── test_api_endpoints.py
│   └── perf/
│       └── test_1m_row_batch.py
│
├── infra/
│   ├── docker-compose.yml                  ← DCVPG services: postgres, api, dashboard
│   ├── docker-compose.prod.yml             ← Production-ready with resource limits
│   └── k8s/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
├── examples/                               ← Working reference projects for users to study
│   ├── airflow_project/                    ← Complete example using Airflow
│   │   ├── dcvpg.config.yaml
│   │   ├── contracts/
│   │   └── pipelines/
│   ├── prefect_project/                    ← Complete example using Prefect
│   └── standalone_project/                 ← No orchestrator — plain Python
│
├── docs/
│   ├── index.md
│   ├── quickstart.md
│   ├── contract_authoring.md
│   ├── connectors.md
│   ├── custom_rules.md
│   ├── mcp_setup.md
│   └── api_reference.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml                          ← Run tests on every PR
│       ├── cd.yml                          ← Publish to PyPI on every tag
│       └── contract_check.yml             ← Validate YAML schema on PR
│
├── pyproject.toml                          ← Package metadata, deps, extras, CLI entrypoint
├── README.md
├── CONTRIBUTING.md
├── LICENSE                                 ← Apache 2.0
└── CHANGELOG.md
```

---

## 12. Project Structure — Layer 2: User Project

This is what every user creates when they run `dcvpg init`. It is **entirely owned by the user**. DCVPG reads it at runtime. The framework ships none of this — it is all user-specific.

```
my-data-platform/                           ← User's own Git repository
│
├── dcvpg.config.yaml                       ← Master config: connections, alerting, AI settings
│                                              (See Section 13 for full spec)
│
├── contracts/                              ← ALL of the user's pipeline contracts
│   │                                          Organised however makes sense for their team
│   ├── services/                           ← Sub-folders per domain/microservice
│   │   ├── orders/
│   │   │   ├── orders_raw.yaml             ← e.g. raw data from payment API
│   │   │   └── orders_enriched.yaml        ← e.g. after joining with customer data
│   │   ├── customers/
│   │   │   ├── customers_raw.yaml
│   │   │   └── customers_enriched.yaml
│   │   ├── payments/
│   │   │   ├── payments_raw.yaml
│   │   │   └── payments_settled.yaml
│   │   ├── inventory/
│   │   │   └── stock_levels.yaml
│   │   └── marketing/
│   │       ├── events_raw.yaml
│   │       └── campaigns.yaml
│   │
│   └── _schema/
│       └── contract.schema.json            ← Copied from dcvpg; used by CI to validate all YAMLs
│
├── custom_connectors/                      ← User's own data source connectors
│   │                                          Extend dcvpg.engine.connectors.base_connector.BaseConnector
│   ├── __init__.py
│   ├── internal_crm_connector.py           ← e.g. connects to their proprietary CRM system
│   ├── legacy_oracle_connector.py          ← e.g. their old Oracle database
│   └── sap_connector.py                    ← e.g. their SAP ERP system
│
├── custom_rules/                           ← User's own validation rules
│   │                                          Extend dcvpg.engine.rules.base_rule.BaseRule
│   ├── __init__.py
│   ├── currency_rule.py                    ← e.g. validates ISO 4217 currency codes
│   ├── business_id_rule.py                 ← e.g. validates internal order ID format
│   └── geo_rule.py                         ← e.g. validates country codes against allowed list
│
├── pipelines/                              ← User's orchestrator DAGs/flows
│   ├── airflow/
│   │   ├── orders_pipeline.py              ← Uses DataContractValidatorOperator
│   │   ├── customers_pipeline.py
│   │   └── payments_pipeline.py
│   ├── prefect/
│   │   └── inventory_flow.py               ← Uses contract_validator_task
│   └── dagster/
│       └── marketing_assets.py             ← Uses contract_validator_op
│
├── tests/                                  ← User's own tests for their contracts and rules
│   ├── test_orders_contract.py
│   ├── test_payments_contract.py
│   └── test_custom_rules.py
│
└── .github/
    └── workflows/
        └── validate_contracts.yml          ← Generated by dcvpg init
                                               Runs: dcvpg validate --all on every PR
                                               Blocks merge if any contract YAML is invalid
```

---

## 13. Configuration — `dcvpg.config.yaml`

This is the single configuration file in the user's project. It is the only thing the user needs to edit to connect DCVPG to their infrastructure. The framework reads it at startup.

```yaml
# dcvpg.config.yaml
# Generated by: dcvpg init
# Edit this file to connect DCVPG to your infrastructure.
# Do NOT commit secrets — use environment variable references (${VAR_NAME})

project:
  name: my-data-platform              # user names their own project
  team: data-engineering
  environment: production             # production | staging | development

contracts:
  directory: ./contracts/services     # scan this folder recursively for all *.yaml files
  auto_register: true                 # automatically register new contracts on discovery
  watch_mode: false                   # set true in dev to reload contracts on file change

# ── Data Source Connections ────────────────────────────────────────────────────
# Each connection has a name (used in contracts) and a type (maps to a connector class)
# Users add as many connections as they have data sources

connections:
  - name: orders_db                   # referenced in contract: source_connection: orders_db
    type: postgres
    host: ${ORDERS_DB_HOST}
    port: 5432
    database: orders_prod
    user: ${ORDERS_DB_USER}
    password: ${ORDERS_DB_PASSWORD}

  - name: data_warehouse
    type: snowflake
    account: ${SNOWFLAKE_ACCOUNT}
    warehouse: COMPUTE_WH
    database: ANALYTICS
    user: ${SNOWFLAKE_USER}
    password: ${SNOWFLAKE_PASSWORD}

  - name: payment_api
    type: rest_api
    base_url: https://api.payments.internal/v1
    auth_type: bearer
    token_env: PAYMENT_API_TOKEN

  - name: reports_bucket
    type: s3
    bucket: ${S3_BUCKET_NAME}
    region: ap-southeast-1
    access_key_env: AWS_ACCESS_KEY_ID
    secret_key_env: AWS_SECRET_ACCESS_KEY

  - name: internal_crm                # custom connector — user wrote this
    type: custom
    module: custom_connectors.internal_crm_connector.CRMConnector
    params:
      base_url: https://crm.internal
      timeout_seconds: 30

# ── Custom Extensions ──────────────────────────────────────────────────────────
extensions:
  custom_rules_dir: ./custom_rules            # load all BaseRule subclasses from here
  custom_connectors_dir: ./custom_connectors  # load all BaseConnector subclasses from here

# ── Runtime DB (DCVPG's own PostgreSQL) ───────────────────────────────────────
database:
  host: ${DCVPG_DB_HOST}
  port: 5432
  name: dcvpg
  user: ${DCVPG_DB_USER}
  password: ${DCVPG_DB_PASSWORD}

# ── Alerting ───────────────────────────────────────────────────────────────────
alerting:
  default_severity_threshold: WARNING   # minimum severity to fire any alert

  slack:
    enabled: true
    webhook_env: SLACK_WEBHOOK_URL
    channel: "#data-ops"
    mention_owners: true                # @mention owner_team and source_owner on CRITICAL

  pagerduty:
    enabled: true
    api_key_env: PAGERDUTY_API_KEY
    service_id: ${PAGERDUTY_SERVICE_ID}
    severity_threshold: CRITICAL        # only page on CRITICAL violations

  teams:
    enabled: false
    webhook_env: TEAMS_WEBHOOK_URL

  custom_alerter:                       # user's own alerter class
    enabled: false
    module: custom_alerters.internal_ops_alerter.OpsAlerter

# ── AI Agent Layer (optional) ─────────────────────────────────────────────────
ai:
  enabled: true
  api_key_env: ANTHROPIC_API_KEY
  model: claude-sonnet-4-6

  auto_healer:
    enabled: true
    auto_merge: false                   # ALWAYS require human approval before merging
    github_token_env: GITHUB_TOKEN
    contracts_repo: my-org/my-data-platform  # user's own repo
    contracts_branch: main
    notify_source_owner: true

  contract_generator:
    enabled: true
    sample_rows: 1000
    output_dir: ./contracts/generated   # where generated contracts are saved

  anomaly_detector:
    enabled: true
    baseline_window_days: 30
    z_score_threshold: 3.0

  rca_agent:
    enabled: true
    publish_to: confluence              # confluence | notion | slack | none
    confluence_url_env: CONFLUENCE_URL
    confluence_token_env: CONFLUENCE_TOKEN
    confluence_space: DATA

# ── MCP Server ─────────────────────────────────────────────────────────────────
mcp:
  enabled: true
  port: 8765
  api_key_env: DCVPG_MCP_KEY
  transport: stdio                      # stdio (local) | sse (remote)
  audit_log: true                       # log every AI tool call to mcp_audit_log table

# ── API Server ─────────────────────────────────────────────────────────────────
api:
  host: 0.0.0.0
  port: 8000
  api_key_env: DCVPG_API_KEY

# ── Dashboard ──────────────────────────────────────────────────────────────────
dashboard:
  host: 0.0.0.0
  port: 8501
  title: "My Data Platform — Pipeline Guardian"
```

---

## 14. Contract Definition Specification

Each contract YAML the user writes must conform to this specification. The framework validates every contract against `_schema/contract.schema.json` automatically on load and in CI.

### Required Fields

| Field | Type | Description |
|---|---|---|
| `contract.name` | string | Unique identifier for this contract within the project |
| `contract.version` | string | Semantic version (e.g. 1.0, 2.3) — bumped on breaking changes |
| `contract.owner_team` | string | Team responsible for maintaining this contract |
| `contract.source_owner` | string | Team or system that produces this data |
| `contract.source_connection` | string | Name of connection from dcvpg.config.yaml |
| `contract.schema` | list | List of field definitions (see below) |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `contract.description` | string | Human-readable description of this data source |
| `contract.sla_freshness_hours` | integer | Max acceptable age of data in hours |
| `contract.pipeline_tags` | list | Tags for filtering in dashboard (e.g. [critical, revenue]) |
| `contract.row_count_min` | integer | Minimum expected rows per batch |
| `contract.row_count_max` | integer | Maximum expected rows per batch |
| `contract.custom_rules` | list | Custom rule classes to run (from user's custom_rules/) |

### Field Definition Options

| Option | Type | Description |
|---|---|---|
| `field` | string | Field name as it appears in the source data |
| `type` | string | One of: string, integer, float, boolean, timestamp, date, json |
| `nullable` | boolean | Whether null values are permitted (default: true) |
| `unique` | boolean | Whether values must be unique in the batch (default: false) |
| `min` | number | Minimum value for numeric fields |
| `max` | number | Maximum value for numeric fields |
| `min_length` | integer | Minimum string length |
| `max_length` | integer | Maximum string length |
| `format` | string | One of: uuid, email, phone, date, datetime, url, or a custom regex |
| `allowed_values` | list | Exhaustive list of permitted values (categorical fields) |
| `description` | string | Human-readable description of this field |

---

## 15. Extensibility — Custom Connectors & Rules

DCVPG is designed to be extended. Users who have proprietary data sources or business-specific validation logic can write their own connectors and rules without modifying the framework.

### 15.1 Custom Connector

```python
# user's file: custom_connectors/internal_crm_connector.py
from dcvpg.engine.connectors.base_connector import BaseConnector
import pandas as pd

class CRMConnector(BaseConnector):
    """
    Connects to our internal CRM system via its proprietary REST API.
    DCVPG loads this automatically from custom_connectors_dir in config.
    """

    def connect(self, config: dict) -> None:
        self.base_url = config["base_url"]
        self.session = self._create_session(config)

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        # source = the table/endpoint name from the contract
        response = self.session.get(f"{self.base_url}/{source}?limit={sample_rows}")
        return pd.DataFrame(response.json()["data"])

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        response = self.session.get(f"{self.base_url}/{source}?batch={batch_id}")
        return pd.DataFrame(response.json()["data"])
```

### 15.2 Custom Rule

```python
# user's file: custom_rules/currency_rule.py
from dcvpg.engine.rules.base_rule import BaseRule
from dcvpg.engine.models import ValidationResult
import pandas as pd

class CurrencyValidator(BaseRule):
    """
    Validates that a currency field contains only ISO 4217 codes
    that our company actually supports. Generic type/format checks
    alone cannot enforce our specific business currency list.
    """

    def validate(self, data: pd.DataFrame, field: str, params: dict) -> ValidationResult:
        supported = set(params.get("supported_currencies", []))
        invalid_mask = ~data[field].isin(supported)
        invalid_rows = data[invalid_mask]

        if invalid_rows.empty:
            return ValidationResult(passed=True, field=field)

        return ValidationResult(
            passed=False,
            field=field,
            violation_type="INVALID_CURRENCY",
            rows_affected=len(invalid_rows),
            sample_values=invalid_rows[field].unique().tolist()[:5]
        )
```

---

## 16. AI Agent Layer

### 16.1 What AI Adds Over the Core Framework

| Capability | Without AI (v1) | With AI (v2) | Time Saved |
|---|---|---|---|
| Violation detection | Automatic ✅ | Automatic ✅ | — |
| Root cause diagnosis | Manual — engineer reads logs | AI reasons from schema diff + history | 45–90 min |
| Fix proposal | Engineer writes YAML manually | AI drafts updated contract + opens PR | 30–60 min |
| Quarantine replay | Manual trigger | AI triggers after PR approval | 15–30 min |
| Incident report | Never written | AI writes post-mortem to Confluence | 60–120 min |
| Contract creation | Engineer writes YAML | AI generates from live data sample | 30–90 min |
| Anomaly detection | Not covered | AI detects statistically abnormal valid data | Hours of bad data |

### 16.2 Auto-Healer Agent

```
TRIGGER: CRITICAL violation detected in any user's pipeline
         |
Step 1:  Agent reads violation report (pipeline name, contract, affected field)
Step 2:  Agent fetches current live schema from user's configured source
Step 3:  Runs schema_differ.py: computes structured diff (contract vs live)
Step 4:  Sends diff to LLM: "What changed? rename / type change / deletion?"
Step 5:  LLM reasons and outputs: diagnosis + confidence score
Step 6:  fix_proposer.py: LLM generates corrected contract YAML
Step 7:  pr_manager.py: creates branch in user's repo, commits YAML, opens PR
Step 8:  Slack alert updated: "AI diagnosed rename. PR #47 ready for review."
                               [Approve ✅] [Reject ❌] [Need more info ℹ️]
Step 9:  Engineer clicks Approve
Step 10: pr_manager.py merges PR, triggers replay of quarantined batch
Step 11: Replay validation passes → data loads to warehouse → incident closed
Step 12: rca_agent.py writes post-mortem → published to Confluence
```

### 16.3 Contract Generator Agent

```bash
# User runs this for any of their data sources
$ dcvpg generate --source orders_db --table orders_raw

Connecting to orders_db (postgres)...
Sampling 1,000 rows from orders_raw...
Profiling 14 fields...
  order_id       → string, 0% null, all unique, format: uuid
  total_amount   → float, 0% null, range: 0.50 – 4823.99
  currency       → string, 0% null, cardinality: 4 (USD, EUR, GBP, SGD)
  status         → string, 0% null, cardinality: 5 values
  created_at     → timestamp, 0% null
  ... (9 more fields)

Generating contract with AI...

✅ Contract saved: contracts/services/orders/orders_raw.yaml
   Fields detected:  14
   Rules suggested:  31
   Custom rules:     1 (currency_rule — detected limited cardinality)
   Confidence:       97%

Review and register:
$ dcvpg register contracts/services/orders/orders_raw.yaml
```

### 16.4 Anomaly Detection Agent

Catches data that passes all contract rules but is statistically abnormal.

| Anomaly Type | What It Detects | Method |
|---|---|---|
| Volume anomaly | Row count significantly outside normal range | Z-score vs 30-day rolling baseline |
| Distribution shift | Field mean/median moved significantly | Statistical shift detection (IQR, Z-score) |
| Null rate spike | Null rate for a field increased suddenly | Rate comparison vs 30-day baseline |
| Cardinality explosion | New unexpected values appeared in categorical field | New value count vs baseline cardinality |
| Temporal gap | Missing data for a time window | Gap detection in timestamp distribution |
| Duplicate rate spike | Duplicate rate increased beyond baseline | Rate comparison vs baseline |

### 16.5 RCA Agent

After every resolved incident, automatically generates and publishes a structured post-mortem:

```
INCIDENT REPORT — [user's pipeline name] — [date]
Generated automatically by DCVPG RCA Agent

SEVERITY:       Critical
DURATION:       [X] minutes ([start time] – [end time])
DATA IMPACT:    [N] rows quarantined, 0 rows reached warehouse

WHAT HAPPENED:
[LLM-generated plain-English narrative of the incident]

ROOT CAUSE:
[LLM-identified root cause from schema diff and history]

RESOLUTION:
[Steps taken: who did what, when PR was opened, when it was merged]

PREVENTION:
[LLM-generated actionable recommendations to prevent recurrence]
```

---

## 17. MCP Server Integration

### 17.1 What MCP Enables

The MCP Server makes DCVPG conversational. Instead of opening dashboards or running CLI commands, engineers simply ask their AI assistant in plain English.

```
Engineer: "Anything broken in our pipelines this morning?"

Claude (via MCP → DCVPG API):
  "Yes, 2 issues detected overnight:
   🔴 CRITICAL — orders_raw pipeline failed at 2:01 AM
      Field 'total_amount' missing from source. 14,823 rows quarantined.
      AI has opened PR #47 with a proposed fix.
   🟡 WARNING  — inventory stock_levels row count 40% below 30-day average"

Engineer: "Merge the PR for orders"

Claude (via MCP → create_fix_pr tool):
  "Done. PR #47 merged. Quarantine replay triggered.
   14,823 rows re-validated and loaded to warehouse. Incident closed."
```

### 17.2 How MCP Works — Technical Flow

```
User types to Claude: "What pipelines are failing?"
         |
         | Claude identifies it needs live data
         ↓
Claude sends JSON-RPC call to DCVPG MCP Server:
{ "method": "tools/call",
  "params": { "name": "get_pipeline_status" } }
         |
         | MCP Server validates API key
         ↓
MCP Server calls DCVPG REST API:
GET http://localhost:8000/api/v1/pipelines
         |
         | DCVPG queries PostgreSQL
         ↓
Live data returned → MCP Server → Claude
         |
         ↓
Claude replies in plain English

Total time: < 3 seconds
```

### 17.3 MCP Tool Catalogue

| Tool | Description | Returns |
|---|---|---|
| `get_pipeline_status()` | Live pass/fail for all registered pipelines | List: pipeline name, status, last run, violation count |
| `get_violation_detail(name)` | Full detail of most recent violation for a pipeline | Violation type, field, row count, schema diff, suggested fix |
| `list_quarantine_batches()` | All currently quarantined batches | Batch ID, pipeline, rows, reason, timestamp |
| `get_schema_diff(name)` | Contract vs live source schema comparison | Structured diff: added / removed / changed fields |
| `create_fix_pr(pipeline, changes)` | Open a GitHub PR to update a contract | PR number, URL, diff summary |
| `replay_quarantine(batch_id)` | Re-validate and replay quarantined batch after fix | Row count, pass/fail result |
| `approve_contract_update(pr_id)` | Merge an approved fix PR, reload contract | Merge status, new contract version |
| `generate_contract(source, table)` | Run AI Contract Generator on a user's data source | Draft contract YAML |
| `get_incident_summary(days)` | Summary of all incidents in last N days | Count, MTTR, top failing pipelines |
| `get_contract_detail(name)` | Full contract spec, rules, ownership, version history | Contract YAML + metadata |

### 17.4 Engineer Setup — One-Time, 5 Minutes

```bash
# Step 1 — Install with MCP support
pip install dcvpg[mcp]

# Step 2 — Start MCP Server
dcvpg mcp-server start --api-key my-secret-key

# Step 3 — Get the config snippet for Claude Desktop
dcvpg mcp-server config
# Outputs:
# {
#   "mcpServers": {
#     "dcvpg": {
#       "command": "dcvpg",
#       "args": ["mcp-server", "start"],
#       "env": {
#         "DCVPG_API_URL": "http://localhost:8000",
#         "DCVPG_API_KEY": "my-secret-key"
#       }
#     }
#   }
# }

# Step 4 — Paste into ~/.claude/mcp_config.json and restart Claude Desktop
# Done. Claude now has live access to all your pipelines.
```

---

## 18. CLI Command Reference

All CLI commands work within the user's project directory (where `dcvpg.config.yaml` lives).

| Command | Description | Example |
|---|---|---|
| `dcvpg init <name>` | Scaffold a new user project with all directories and templates | `dcvpg init my-data-platform` |
| `dcvpg generate` | AI-generate a contract from a live data source | `dcvpg generate --source orders_db --table orders_raw` |
| `dcvpg validate` | Run validation for one or all contracts | `dcvpg validate --contract orders/orders_raw` or `--all` |
| `dcvpg register` | Register a contract YAML into the runtime store | `dcvpg register contracts/orders/orders_raw.yaml` |
| `dcvpg diff` | Show schema drift between contract and live source | `dcvpg diff --contract orders/orders_raw` |
| `dcvpg status` | Show pass/fail status of all registered contracts | `dcvpg status` |
| `dcvpg replay` | Replay a quarantined batch after a fix | `dcvpg replay --batch-id q_20260309_001` |
| `dcvpg mcp-server start` | Start the MCP Server as a background process | `dcvpg mcp-server start --api-key $KEY` |
| `dcvpg mcp-server stop` | Stop the MCP Server | `dcvpg mcp-server stop` |
| `dcvpg mcp-server status` | Check if MCP Server is running and list registered tools | `dcvpg mcp-server status` |
| `dcvpg mcp-server logs` | Tail MCP Server logs — see all AI tool calls in real time | `dcvpg mcp-server logs --follow` |
| `dcvpg mcp-server config` | Print the JSON to paste into Claude Desktop config | `dcvpg mcp-server config` |

---

## 19. Implementation Roadmap

### Phase 1 — Core Framework Foundation (Weeks 1–2)
> **Goal:** Working contract parser + validation engine + generic operator running locally

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Framework repo setup | Monorepo with all top-level directories as per Section 11 | GitHub repo (private) | Lead DE |
| Pydantic models | ContractSpec, FieldSpec, ValidationReport, QuarantineEvent | engine/models.py | Lead DE |
| Contract JSON Schema | JSON Schema for validating all user contract YAMLs | config/contract.schema.json | DE |
| Config loader | Reads and validates dcvpg.config.yaml; resolves env vars | config/config_loader.py | DE |
| Contract loader | Loads ANY contract YAML from ANY path; validates against schema | engine/contract_loader.py | DE |
| Contract registry | Auto-discovers all YAMLs in user's contracts/ directory | engine/registry.py | DE |
| Validation rules — core | Schema presence, type, nullability, uniqueness, range, format, allowed values | engine/rules/*.py | DE |
| Base classes | BaseConnector, BaseRule, BaseAlerter — abstract, extensible | engine/*/base_*.py | DE |
| Built-in connectors | PostgreSQL, MySQL, REST API, S3, file (CSV/JSON/Parquet) | engine/connectors/*.py | DE |
| Custom loader | Dynamically loads user's custom_rules/ and custom_connectors/ | engine/rules/custom_rule_loader.py | DE |
| PostgreSQL schema | All DB tables: contracts, pipeline_runs, quarantine, alerts, snapshots | migrations/001–003.sql | DE |
| Unit tests | Full pytest suite for all rules, connectors, models | tests/unit/ | DE |
| Docker Compose v1 | PostgreSQL + Python service | infra/docker-compose.yml | DevOps |

### Phase 2 — Orchestrator Integration (Week 3)
> **Goal:** Generic operator working in Airflow, Prefect, and Dagster

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Airflow operator | Generic DataContractValidatorOperator; reads contract + conn from params | orchestrators/airflow/ | DE |
| Prefect task | @task wrapper around validation engine | orchestrators/prefect/ | DE |
| Dagster op | @op wrapper around validation engine | orchestrators/dagster/ | DE |
| Quarantine engine | Write failed batches to quarantine table with full metadata | engine/quarantine_engine.py | DE |
| Example projects | Working examples for Airflow, Prefect, Dagster — generic, no business names | examples/ | DE |
| Integration tests | End-to-end: intentional violation → quarantine → alert → replay | tests/integration/ | DE |

### Phase 3 — Alerting, API & Dashboard (Weeks 4–5)
> **Goal:** Real-time alerts + REST API + Streamlit dashboard

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Alert manager | Routes alerts to all configured destinations from dcvpg.config.yaml | alerting/alert_manager.py | DE |
| Slack alerter | Structured Slack messages with violation detail and suggested fix | alerting/slack_alerter.py | DE |
| PagerDuty alerter | Fire PagerDuty on CRITICAL only | alerting/pagerduty_alerter.py | DE |
| Teams + webhook alerters | Microsoft Teams and generic webhook | alerting/*.py | DE |
| FastAPI REST API | All 14 endpoints from Section 10 | api/ | DE |
| Streamlit dashboard | 6-page dashboard reading from API | dashboard/ | DE |
| Prometheus metrics | Expose /metrics: violations_total, quarantine_count, run_duration | monitoring/metrics.py | DevOps |
| Grafana dashboard | Pre-built dashboard JSON for import | monitoring/grafana.json | DevOps |

### Phase 4 — CLI & Open Source Prep (Week 6)
> **Goal:** `dcvpg init` works; package publishable to PyPI

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| CLI — init command | Scaffolds complete user project from templates/ | cli/commands/init.py | DE |
| CLI — validate, register, diff, status, replay | All utility commands | cli/commands/*.py | DE |
| Templates | All init templates: config, contract, connector, rule, DAG, CI workflow | templates/ | DE |
| pyproject.toml | Package metadata, all extras (dcvpg[mcp], dcvpg[ai], dcvpg[all]) | pyproject.toml | Lead DE |
| Documentation | Quickstart, contract authoring, connectors, custom rules, API reference | docs/ | Lead DE |
| Performance tests | 1M row batches, 50 concurrent pipelines | tests/perf/ | DE |
| GitHub Actions CI/CD | Run tests on PR; publish to PyPI on tag | .github/workflows/ | DevOps |

### Phase 5 — AI Contract Generator + MCP Server (Weeks 7–8)
> **Goal:** `dcvpg generate` live; MCP Server working with Claude Desktop

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Contract generator agent | Profiler + LLM contract YAML generation + `dcvpg generate` CLI | ai_agents/contract_generator/ | DE |
| MCP Server scaffold | Register all 10 tools; connect to DCVPG API via httpx | mcp_server/server.py | Lead DE |
| All MCP tools | Pipeline, contract, quarantine, agent tools | mcp_server/tools/ | DE |
| MCP auth + audit log | API key validation; log all AI calls to mcp_audit_log table | mcp_server/auth.py + migrations/005 | DevOps |
| MCP CLI commands | `dcvpg mcp-server start/stop/status/logs/config` | cli/commands/mcp.py | DE |
| Claude Desktop test | End-to-end: query pipeline health from Claude conversation | tests/mcp/ | DE |
| PyPI publish (v1) | Publish dcvpg + dcvpg[mcp] to pypi.org | PyPI listing | Lead DE |
| Airflow Provider | Package apache-airflow-providers-dcvpg separately | Provider package | DE |

### Phase 6 — Auto-Healer Agent (Weeks 9–10)
> **Goal:** CRITICAL violations diagnosed + fix PR opened automatically within 60 seconds

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Schema differ | DeepDiff contract vs live schema; structured diff output | ai_agents/auto_healer/schema_differ.py | DE |
| LLM diagnosis prompts | Prompts covering: rename, type change, deletion, new required field | prompts/diagnose_violation.txt | DE |
| Fix proposer | LLM generates corrected contract YAML from diagnosis | ai_agents/auto_healer/fix_proposer.py | DE |
| PR manager | PyGithub: branch → commit → PR → merge on approval | ai_agents/auto_healer/pr_manager.py | DE |
| Slack approval flow | Interactive buttons: Approve / Reject / More Info | alerting/slack_alerter.py (update) | DE |
| Healer integration test | Full E2E: inject violation → agent → PR opened → approve → replay | tests/integration/test_healer.py | DE |

### Phase 7 — Anomaly Detection + RCA Agent (Weeks 11–12)
> **Goal:** Catch valid-but-wrong data; auto-write every incident post-mortem

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Baseline store | 30-day rolling stats per pipeline per field in PostgreSQL | ai_agents/anomaly_detector/baseline_store.py | DE |
| All detectors | Volume, distribution, null rate, cardinality, temporal gap, duplicate | detectors/ | DE |
| Anomaly alerts | Separate Slack alert for statistical anomalies vs contract violations | alerting/alert_manager.py (update) | DE |
| RCA report builder | Collect full incident context for LLM | ai_agents/rca_agent/report_builder.py | DE |
| RCA publisher | Generate post-mortem with Claude API; publish to Confluence/Notion | ai_agents/rca_agent/rca_agent.py | DE |
| PyPI publish (v2) | Publish dcvpg[ai] with all AI agent dependencies | PyPI update | Lead DE |

### Phase 8 — Distribution & Community Launch (Weeks 13–14)
> **Goal:** Public GitHub repo; listed on all registries; first 100 stars

| Task | Description | Deliverable | Owner |
|---|---|---|---|
| Make repo public | Open-source the GitHub repository | Public GitHub repo | Lead DE |
| MCP registry listing | Submit to MCP Server registry | Registry listing | DE |
| Astronomer registry | Submit Airflow Provider to Astronomer Registry | Registry listing | DE |
| Demo GIF / video | Screen recording: install → generate → violation → Claude fixes it | README demo | Lead DE |
| Launch posts | Reddit r/dataengineering, LinkedIn, HackerNews | Community posts | Lead DE |
| Discord / community | Set up community server for users + contributors | Discord server | Lead DE |
| DCVPG Cloud (MVP) | Hosted version: managed PostgreSQL + API + dashboard + auth | cloud.dcvpg.io | DevOps |

---

## 20. Non-Functional Requirements

| Requirement | Target | Measurement |
|---|---|---|
| Validation latency | < 30 seconds for batches up to 1M rows | Benchmark test in CI |
| Alert delivery time | < 60 seconds from violation detection to Slack | End-to-end integration test |
| Auto-Healer response time | < 60 seconds from violation to PR open | End-to-end integration test |
| API response time | < 200ms p99 for all read endpoints | Load test with k6 |
| Dashboard load time | < 3 seconds for Overview page | Streamlit profiler |
| MCP tool response time | < 3 seconds for any tool call | MCP integration test |
| Availability | 99.9% uptime for API and dashboard | Uptime monitoring |
| Scalability | Support 200+ active contracts, 1,000+ pipeline runs/day | Load test |
| Test coverage | Minimum 85% line coverage for engine package | pytest-cov in CI |
| `dcvpg init` time | User project scaffolded in under 10 seconds | Manual test |
| Full install time | `pip install dcvpg[all]` completes in under 60 seconds | CI smoke test |
| Docker Compose startup | Full stack running in under 5 minutes | Onboarding test |

---

## 21. Security Considerations

- All API endpoints authenticated via API key in `Authorization` header
- MCP Server has its own API key, separate from the REST API key — principle of least privilege
- All credentials in `dcvpg.config.yaml` use `${ENV_VAR}` references — no secrets ever in config files or code
- Secret management via HashiCorp Vault or AWS Secrets Manager in production
- Quarantine tables may contain sensitive user data — row-level security applied; only accessible to contract owner teams
- All API and MCP traffic over HTTPS in production — TLS termination at load balancer
- GitHub Actions secrets for CI/CD — no credentials in workflow YAML files
- AI Auto-Healer requires explicit human approval before any PR is merged — no automated changes to production contracts without sign-off
- MCP audit log records every AI tool call — full traceability of AI actions
- Framework ships no user data — contracts, config, and quarantine data all live in the user's own infrastructure
- All MCP tools are read-only by default; write tools (create_fix_pr, approve) require elevated API key scope

---

## 22. Open Source Publishing Strategy

### 22.1 Open-Core Business Model

| Tier | Price | What's Included |
|---|---|---|
| Core (Open Source) | Free forever | Framework, validator, quarantine, alerting, Airflow/Prefect/Dagster operators, dashboard, MCP Server, CLI, all connectors |
| DCVPG Cloud — Starter | $49/month | Hosted PostgreSQL + API + Dashboard, 10 pipelines, zero infra to manage |
| DCVPG Cloud — Pro | $199/month | Everything in Starter + hosted AI Agents, 50 pipelines, team SSO |
| Enterprise | Custom | Unlimited pipelines, SAML SSO, SLA, dedicated support, self-hosted VPC deployment |

### 22.2 `pyproject.toml` — Package Definition

```toml
[project]
name = "dcvpg"
version = "1.0.0"
description = "Data Contract Validator and Pipeline Guardian — generic, open-source"
authors = [{ name = "Your Name", email = "you@email.com" }]
license = { text = "Apache-2.0" }
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
  "pydantic>=2.0",
  "great-expectations>=0.18",
  "pyyaml>=6.0",
  "httpx>=0.27",
  "click>=8.0",
  "fastapi>=0.110",
  "streamlit>=1.32",
  "psycopg2-binary>=2.9",
]

[project.optional-dependencies]
airflow  = ["apache-airflow>=2.8"]
prefect  = ["prefect>=2.0"]
dagster  = ["dagster>=1.0"]
mcp      = ["mcp>=1.0"]
ai       = ["anthropic>=0.25", "deepdiff>=6.0", "scipy", "numpy", "pandas", "PyGithub>=2.0", "slack-bolt>=1.0"]
all      = ["dcvpg[mcp,ai]"]

[project.scripts]
dcvpg = "dcvpg.cli.main:cli"          # enables: dcvpg init, dcvpg generate, etc.
```

### 22.3 Publishing to PyPI

```bash
python -m build                        # build wheel + sdist
python -m twine upload dist/*          # publish to pypi.org

# After this, anyone on Earth runs:
pip install dcvpg               # core only
pip install dcvpg[mcp]          # + MCP Server
pip install dcvpg[ai]           # + AI agents
pip install dcvpg[airflow]      # + Airflow operator
pip install dcvpg[all]          # everything
```

### 22.4 Registry & Marketplace Listing Plan

| Registry | Package Name | Target Audience | Timeline |
|---|---|---|---|
| PyPI (pypi.org) | `dcvpg` | All Python / data engineers globally | Phase 5 (Week 14) |
| Airflow Provider Registry | `apache-airflow-providers-dcvpg` | Airflow users — largest DE community | Phase 5 (Week 14) |
| Astronomer Registry | `dcvpg` | Managed Airflow users | Week 15 |
| MCP Server Registry | `dcvpg-mcp` | Claude / AI assistant users | Phase 5 (Week 14) |
| dbt Hub | `dcvpg-dbt` | dbt users | v2.1 future |
| Prefect Collections | `prefect-dcvpg` | Prefect users | v2.1 future |

---

## 23. End-to-End User Journey

### 23.1 New User — Zero to Operational (15 Minutes)

| Step | Command / Action | Time | What Happens |
|---|---|---|---|
| 1 — Install | `pip install dcvpg[all]` | 30 sec | PyPI installs framework + all extras |
| 2 — Init project | `dcvpg init my-data-platform` | 10 sec | Full user project scaffolded with all directories and templates |
| 3 — Configure | Edit `dcvpg.config.yaml` — add your database connections | 5 min | User fills in their connection strings using ${ENV_VAR} references |
| 4 — Generate contracts | `dcvpg generate --source orders_db --table orders_raw` | 2 min | AI profiles data, generates contract YAML — user reviews |
| 5 — Add to pipeline | Add `DataContractValidatorOperator` to existing DAG | 5 min | Copy 5 lines from example into their DAG. Zero pipeline rebuild. |
| 6 — Start MCP Server | `dcvpg mcp-server start --api-key $KEY` | 30 sec | MCP Server starts; 10 tools registered |
| 7 — Connect Claude | Paste `dcvpg mcp-server config` output into `~/.claude/mcp_config.json` | 2 min | Claude Desktop connects; has live access to user's pipelines |
| 8 — First conversation | Ask Claude: "Are my pipelines healthy?" | Instant | Claude calls `get_pipeline_status()` via MCP; responds in plain English |

### 23.2 Three User Personas

**Persona A — Solo DE at a Startup**
> Ahmed manages 15 pipelines alone at a fintech in Dubai. Pipelines break at 2am; he finds out at 9am. After installing DCVPG: violations are detected and quarantined at 2am, Claude tells Ahmed at 7:45am exactly what broke and opens a fix PR. Fixed before standup. CEO never knew.

**Persona B — DE Team at a Mid-Size Company**
> Priya leads 5 DEs managing 80 pipelines at an e-commerce company in Singapore. `dcvpg generate` produces all 80 contracts in 2 hours. After rollout: pipeline incident tickets drop from 18/month to 2. Resolution time drops from 4 hours to 18 minutes. Priya upgrades to DCVPG Cloud for hosted dashboard + team SSO.

**Persona C — Platform Team at Enterprise**
> James works at a bank in London serving 30 data teams with 200+ pipelines. Month 1: pilot 2 teams. Month 3: full rollout. Month 4: central MCP Server for all engineers. Enterprise contract signed for self-hosted deployment with SAML SSO, audit logs for SOC2, and dedicated support SLA.

---

## 24. Distribution & Publishing Tech Stack

| Tool | Purpose | When Used |
|---|---|---|
| `python-build` | Builds wheel + sdist distributable package | Every release: `python -m build` |
| `twine` | Uploads built package to PyPI securely | Every release: `twine upload dist/*` |
| GitHub Actions (CD) | Auto-runs build + publish on every git tag | Automated — triggers on `git tag vX.Y.Z` |
| GitHub Releases | Creates release page with changelog and download links | Automated from CD workflow |
| TestPyPI | Test registry — verify install before publishing to real PyPI | Before every major release |
| MkDocs + Material | Documentation site generated from `docs/` Markdown files | Live at docs.dcvpg.io via GitHub Pages |
| Semantic Versioning | `MAJOR.MINOR.PATCH` — MAJOR for breaking changes | All releases, communicated in CHANGELOG.md |
| Dependabot | Auto-creates PRs when dependencies have security vulnerabilities | Always enabled on GitHub repo |

---

## 25. Success Metrics

### 25.1 Core Pipeline Health Metrics (Per User)

| Metric | Baseline (Before DCVPG) | Target (3 Months) | Measurement |
|---|---|---|---|
| Pipeline incident MTTR | 4+ hours avg | < 30 min (v1), < 10 min (v2 AI) | Incident log timestamps |
| % bad data reaching warehouse | ~5% of runs | < 0.1% of runs | Quarantine event rate |
| Contract violation detection time | 6–8 hours | < 1 minute | Alert delivery timestamp |
| Engineer hours lost to debugging | 80–200h/month | < 10h/month | Jira ticket tracking |
| Pipeline incident count | 20+/month | < 5/month | Incident log |

### 25.2 AI Layer Metrics

| Metric | Target | Measurement |
|---|---|---|
| Auto-Healer PR accuracy | > 85% PRs approved without manual edit | PR approval vs edit rate |
| Contract generator adoption | > 70% of new contracts generated via AI | `dcvpg generate` usage in MCP audit log |
| Anomaly detection recall | > 90% of test set anomalies detected | Benchmark test suite |
| RCA report coverage | > 95% of resolved incidents have auto-report | Confluence page creation rate |

### 25.3 Open Source Distribution Metrics

| Metric | Month 1 | Month 3 | Month 6 |
|---|---|---|---|
| GitHub stars | 100 | 500 | 2,000+ |
| PyPI monthly downloads | 200 | 2,000 | 10,000+ |
| Airflow Provider installs | 50 | 500 | 2,000+ |
| Community contributors | 3 | 15 | 50+ |
| DCVPG Cloud paying customers | 0 | 10 | 50 |
| Docs site monthly visits | 300 | 3,000 | 15,000+ |
| % users connecting MCP | N/A | 30% | 60% |

---

## 26. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Adoption resistance — teams don't add operator to DAGs | Medium | High | `dcvpg init` generates a ready-to-copy example DAG; operator is a 5-line addition; publish case studies showing time saved |
| False positives cause alert fatigue | Medium | High | Configurable severity levels; WARNING mode for onboarding; track and surface false positive rate in dashboard |
| Validation latency unacceptable for fast pipelines | Low | Medium | Sampling mode (validate 10% of rows); async validation option; configurable batch timeout |
| Contract YAML maintenance overhead | Medium | Medium | `dcvpg generate` auto-generates from live data; `dcvpg diff` shows drift; AI Auto-Healer proposes updates |
| AI Auto-Healer proposes wrong fix | Medium | Medium | All AI PRs require explicit human approval; no auto-merge; confidence score shown in Slack alert |
| MCP Server becomes attack surface | Low | High | Separate API key for MCP; all tool calls logged; read-only by default; write tools require elevated scope |
| Users build coupling to business names in framework | Low | High | Strict code review: zero business names in framework code; `contracts/` dir in user project only |
| Streaming / Kafka support gap in v1 | Low | Low | Documented as v2 roadmap; batch pipelines cover 90% of use cases |
| Single point of failure in validator | Low | High | Stateless design; Docker/K8s restart policies; validator failure defaults to WARNING not block |
| Community fragmentation (too many orchestrators to support) | Medium | Medium | Prioritise Airflow (largest community); Prefect and Dagster as community contributions |

---

## 27. Open Questions

1. Should the `dcvpg generate` AI feature be in the free tier (pip package) or cloud-only? Free tier drives adoption but exposes Claude API costs to us if self-hosted.
2. Should the MCP Server be started automatically as a background service by `dcvpg init`, or always opt-in via explicit `dcvpg mcp-server start`?
3. What is the data retention policy for quarantine events and MCP audit logs? 30 days? 90 days? User-configurable?
4. Should the AI Auto-Healer have a "confidence threshold" below which it will not open a PR and instead only sends a Slack explanation?
5. Should contract updates require PR approval from the source team owner (`source_owner` in the contract), or can the pipeline team update their contracts unilaterally?
6. For the Airflow Provider: should it be a separate PyPI package (`apache-airflow-providers-dcvpg`) or included in `dcvpg[airflow]`? Separate gives better discovery in Airflow registry.
7. Should DCVPG support a "dry-run" mode where violations are logged and alerted but the pipeline is never halted — useful for teams doing initial onboarding?

---

## 28. Glossary

| Term | Definition |
|---|---|
| **DCVPG** | Data Contract Validator & Pipeline Guardian — the name of this framework |
| **Framework (Layer 1)** | The DCVPG codebase published on PyPI; generic, no business-specific logic |
| **User Project (Layer 2)** | The project created by `dcvpg init`; contains the user's contracts, config, custom extensions, and pipeline code |
| **Contract** | A user-written YAML file defining the expected schema, quality rules, ownership, and SLA for one data source |
| **Contract Violation** | Any mismatch between incoming data and the rules declared in a contract |
| **Data Producer** | The team or system that generates or exposes the source data (e.g. a backend API team) |
| **Data Consumer** | The team or system that reads transformed data downstream (e.g. analytics, BI, ML) |
| **Quarantine** | The act of isolating a batch of invalid data in a separate table, preventing it from reaching the warehouse |
| **Schema Drift** | Gradual, unannounced changes to a data source's structure over time |
| **MTTR** | Mean Time To Resolve — average time from incident detection to resolution |
| **SLA Freshness** | The maximum acceptable age of data in hours before it is considered stale |
| **ContractSpec** | The Pydantic model representing a fully parsed and validated contract YAML |
| **ValidationReport** | The structured output of a validation run: pass/fail, violations, affected fields, row counts |
| **BaseConnector** | Abstract base class in the framework; users extend this to implement custom data source connectors |
| **BaseRule** | Abstract base class in the framework; users extend this to implement custom validation rules |
| **BaseAlerter** | Abstract base class in the framework; users extend this to implement custom alert destinations |
| **MCP Server** | Model Context Protocol Server — exposes DCVPG tools to AI assistants like Claude via the MCP protocol |
| **MCP Tool** | A named, callable function exposed by the MCP Server that an AI can invoke to read from or act on DCVPG |
| **AI Agent** | An autonomous Python process that uses an LLM to reason, make decisions, and take actions across systems |
| **Auto-Healer Agent** | DCVPG agent that diagnoses violations, proposes a contract fix, and opens a GitHub PR automatically |
| **Contract Generator Agent** | DCVPG agent that samples a live data source and generates a contract YAML using LLM reasoning |
| **Anomaly Detection** | Statistical analysis that flags data which passes all contract rules but is unusual vs historical baseline |
| **RCA Report** | Root Cause Analysis — structured post-mortem: what broke, why, how it was fixed, how to prevent recurrence |
| **Schema Diff** | Structured comparison between a contract's declared schema and the actual live source schema |
| **Open-Core Model** | Business model: core product is free open source; paid hosted/enterprise tier generates revenue |
| **PyPI** | Python Package Index — global registry where Python packages are published and installed via `pip` |
| **Airflow Provider** | Official Apache Airflow extension package adding DCVPG operators and hooks to any Airflow installation |
| **`dcvpg init`** | CLI command that scaffolds a complete, ready-to-use user project directory |
| **`dcvpg.config.yaml`** | The single configuration file in a user's project; connects DCVPG to their infrastructure |

---

## 29. Document Sign-Off

This PRD is considered approved when the following stakeholders have reviewed and confirmed readiness to proceed to engineering implementation.

| Role | Name | Signature | Date |
|---|---|---|---|
| Lead Data Engineer | | | |
| Engineering Manager | | | |
| Platform / DevOps Lead | | | |
| Head of Data | | | |

---

*DCVPG Product Requirements Document — v4.0 — March 2026*
*CONFIDENTIAL — Internal Engineering Document*
