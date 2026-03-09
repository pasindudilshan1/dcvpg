-- Migration 002: Alert History
-- Stores all delivered alerts and their outcomes

CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(255) NOT NULL,
    contract_name VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    channel VARCHAR(100) NOT NULL,  -- slack | pagerduty | teams | webhook
    delivered BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_history_pipeline
    ON alert_history (pipeline_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_alert_history_severity
    ON alert_history (severity, created_at DESC);

-- Alert suppression / dedup table
CREATE TABLE IF NOT EXISTS alert_suppressions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_name VARCHAR(255) NOT NULL,
    violation_type VARCHAR(100) NOT NULL,
    suppressed_until TIMESTAMP WITH TIME ZONE NOT NULL,
    reason TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_suppression_contract_violation
    ON alert_suppressions (contract_name, violation_type);
