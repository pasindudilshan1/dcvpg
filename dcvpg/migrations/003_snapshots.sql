-- Migration 003: Schema Snapshots
-- Stores historical live-schema captures for drift detection

CREATE TABLE IF NOT EXISTS schema_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_name VARCHAR(255) NOT NULL,
    source_connection VARCHAR(255) NOT NULL,
    source_table VARCHAR(255),
    schema_json JSONB NOT NULL,       -- array of {field, type, nullable}
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schema_snapshots_contract
    ON schema_snapshots (contract_name, captured_at DESC);

-- Schema drift events table
CREATE TABLE IF NOT EXISTS schema_drift_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_name VARCHAR(255) NOT NULL,
    drift_type VARCHAR(50) NOT NULL,   -- FIELD_ADDED | FIELD_REMOVED | TYPE_CHANGED
    field_name VARCHAR(255) NOT NULL,
    contract_type VARCHAR(100),
    live_type VARCHAR(100),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    auto_heal_pr_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_drift_events_contract
    ON schema_drift_events (contract_name, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_drift_events_unresolved
    ON schema_drift_events (contract_name) WHERE resolved_at IS NULL;
