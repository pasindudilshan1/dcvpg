# MCP Server Setup

DCVPG includes a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes 10 tools to AI assistants. Once connected, you can manage your data pipelines entirely through natural language — asking Claude or Cursor to check pipeline health, diagnose violations, replay quarantined batches, and more.

---

## Prerequisites

- DCVPG REST API running (see [Quick Start](quickstart.md#7-start-the-rest-api))
- `pip install "dcvpg[mcp]"`
- Claude Desktop or any MCP-compatible client

---

## Available Tools

| Tool | What it does |
|---|---|
| `get_pipeline_status` | Live health status of all registered pipelines |
| `get_violation_detail` | Full violation breakdown for a specific pipeline's last run |
| `list_quarantine_batches` | All quarantined batches with metadata and failure reason |
| `get_schema_diff` | Drift report — contract definition vs live source schema |
| `create_fix_pr` | Opens a GitHub PR with an AI-proposed contract fix |
| `replay_quarantine` | Re-validates a quarantined batch and releases it if it now passes |
| `approve_contract_update` | Merges an approved fix PR and hot-reloads the contract |
| `generate_contract` | AI-generates a contract YAML from a live data source |
| `get_incident_summary` | Summary of incidents over the last N days |
| `get_contract_detail` | Full spec, field rules, ownership, and version history |

---

## Step 1 — Install

```bash
pip install "dcvpg[mcp]"
```

---

## Step 2 — Start the DCVPG REST API

The MCP server is a thin proxy that forwards tool calls to the DCVPG REST API. The API must be running before the MCP server starts:

```bash
export DCVPG_API_KEY=your-api-key

dcvpg serve api
# API running at http://localhost:8000
```

---

## Step 3 — Configure Environment Variables

```bash
# The running DCVPG REST API
export DCVPG_API_URL=http://localhost:8000/api/v1

# Must match DCVPG_API_KEY on the API server
export DCVPG_API_KEY=your-api-key

# Optional: comma-separated keys to authenticate MCP clients themselves
export MCP_API_KEYS=mcp-key-1,mcp-key-2
```

Check your current configuration at any time:

```bash
dcvpg mcp-server status
```

---

## Step 4 — Start the MCP Server

```bash
dcvpg mcp-server start
```

The server runs on **stdio** (standard input/output) — the protocol used by Claude Desktop, Cursor, and most MCP clients. It does not open a network port.

---

## Step 5 — Connect Claude Desktop

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dcvpg": {
      "command": "python",
      "args": ["-m", "dcvpg.mcp_server.server"],
      "env": {
        "DCVPG_API_URL": "http://localhost:8000/api/v1",
        "DCVPG_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dcvpg": {
      "command": "python",
      "args": ["-m", "dcvpg.mcp_server.server"],
      "env": {
        "DCVPG_API_URL": "http://localhost:8000/api/v1",
        "DCVPG_API_KEY": "your-api-key"
      }
    }
  }
}
```

Restart Claude Desktop after saving. You will see **dcvpg** listed in the MCP tools panel (hammer icon).

---

## Step 6 — Connect Cursor

In Cursor settings → MCP → Add server:

```json
{
  "dcvpg": {
    "command": "python",
    "args": ["-m", "dcvpg.mcp_server.server"],
    "env": {
      "DCVPG_API_URL": "http://localhost:8000/api/v1",
      "DCVPG_API_KEY": "your-api-key"
    }
  }
}
```

---

## Example Prompts

Once connected, try these in Claude or Cursor:

```
What pipelines are currently failing?
Show me the full violation details for the orders pipeline.
How many batches are in quarantine right now?
Is there any schema drift in the payments contract?
Generate a contract for the users table in my postgres_main connection.
Open a PR to fix the type mismatch in the orders contract.
Replay batch abc-123 now that the contract fix is merged.
Give me an incident summary for the last 7 days.
```

---

## Troubleshooting

**"MCP server not found" in Claude Desktop**  
Restart Claude Desktop after editing the config file. MCP servers are loaded only at startup.

**"Connection refused" / API errors in tool responses**  
Verify the DCVPG REST API is running: `curl http://localhost:8000/health` should return `{"status": "ok"}`.  
Check that `DCVPG_API_URL` in the MCP config matches the actual API address.

**Authentication errors (403)**  
Ensure `DCVPG_API_KEY` in the MCP server env matches the key the API was started with.  
Use `dcvpg mcp-server status` to see which values are currently configured.

**Tool not appearing in Claude**  
Run `dcvpg mcp-server start` manually in a terminal and look for import errors. If you see `ModuleNotFoundError: mcp`, run `pip install "dcvpg[mcp]"`.

**MCP server exits immediately**  
The server runs on stdio and is managed by the MCP client. It is not a long-running background process — it starts when the client needs it and exits when done. This is expected behaviour.
