-- Migration 004: Anomaly Detection Baselines
-- Stores rolling statistical baselines for anomaly detectors

CREATE TABLE IF NOT EXISTS anomaly_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_name VARCHAR(255) NOT NULL,
    field_key VARCHAR(512) NOT NULL,    -- e.g. "__row_count__" or "price__null_rate"
    detector_type VARCHAR(100) NOT NULL, -- volume | null_rate | distribution
    baseline_json JSONB NOT NULL,        -- {"mean": ..., "std": ..., "sample_count": ...}
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (contract_name, field_key, detector_type)
);

CREATE INDEX IF NOT EXISTS idx_anomaly_baselines_contract
    ON anomaly_baselines (contract_name);

-- Anomaly detection events
CREATE TABLE IF NOT EXISTS anomaly_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_name VARCHAR(255) NOT NULL,
    pipeline_name VARCHAR(255),
    batch_id VARCHAR(255),
    detector_type VARCHAR(100) NOT NULL,
    field_key VARCHAR(512) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    observed_value FLOAT,
    expected_mean FLOAT,
    expected_std FLOAT,
    z_score FLOAT,
    severity VARCHAR(50) DEFAULT 'WARNING',
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_contract
    ON anomaly_events (contract_name, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_anomaly_events_unacknowledged
    ON anomaly_events (contract_name) WHERE acknowledged_at IS NULL;
