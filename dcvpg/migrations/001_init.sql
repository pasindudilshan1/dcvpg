-- Migration 001: Core Tables
-- Creates the foundational tables for DCVPG framework

CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    owner_team VARCHAR(100),
    source_owner VARCHAR(100),
    yaml_content TEXT NOT NULL,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (name, version)
);

CREATE TABLE IF NOT EXISTS contract_history (
    id SERIAL PRIMARY KEY,
    contract_id UUID REFERENCES contracts(id),
    version VARCHAR(50) NOT NULL,
    changed_by VARCHAR(255),
    change_type VARCHAR(50), -- breaking, non-breaking
    diff_json JSONB,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID REFERENCES contracts(id),
    batch_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- PASSED, FAILED
    rows_processed INTEGER NOT NULL,
    violations_count INTEGER NOT NULL,
    duration_ms INTEGER,
    run_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quarantine_events (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    contract_version VARCHAR(50) NOT NULL,
    batch_id UUID,
    violation_type VARCHAR(100) NOT NULL,
    affected_field VARCHAR(255),
    expected_value TEXT,
    actual_sample TEXT,
    rows_affected INTEGER NOT NULL,
    total_rows INTEGER NOT NULL,
    quarantined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP WITH TIME ZONE
);
