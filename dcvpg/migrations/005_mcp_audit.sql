-- Migration 005: MCP Audit Log
-- Creates the table for tracking MCP server tool executions

CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB,
    executed_by VARCHAR(100), -- user or API token identity
    status VARCHAR(50) NOT NULL, -- SUCCESS, ERROR
    error_message TEXT,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER
);

-- Optional index for faster queries on specific tools
CREATE INDEX IF NOT EXISTS idx_mcp_audit_tool ON mcp_audit_log(tool_name);
