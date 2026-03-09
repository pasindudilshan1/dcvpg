# MCP Server Setup

DCVPG includes a Model Context Protocol (MCP) server that exposes 10 tools to AI assistants (Claude Desktop, Cursor, etc.), enabling natural-language pipeline management.

## Tools Available

| Tool                   | Description                                                  |
|------------------------|--------------------------------------------------------------|
| `get_pipeline_status`  | Live health of all pipelines                                 |
| `get_violation_detail` | Full violation breakdown for a specific pipeline             |
| `list_quarantine_batches` | All quarantined batches with metadata                    |
| `get_schema_diff`      | Contract vs live source schema drift report                  |
| `create_fix_pr`        | Open a GitHub PR to update a broken contract                 |
| `replay_quarantine`    | Re-validate and release a quarantined batch                  |
| `approve_contract_update` | Merge an approved PR and reload the contract             |
| `generate_contract`    | AI-generate a contract YAML from a live data source          |
| `get_incident_summary` | Summary of incidents in the last N days                      |
| `get_contract_detail`  | Full spec, rules, ownership, and version history             |

## Installation

```bash
pip install "dcvpg[mcp]"
```

## Configuration

Set environment variables before starting the server:

```bash
export DCVPG_API_URL=http://localhost:8000/api/v1   # Your running DCVPG API
export DCVPG_API_KEY=your-api-key                   # API authentication key
export MCP_API_KEYS=key1,key2                        # Optional: MCP-level auth keys
```

## Starting the MCP Server

```bash
# Via DCVPG CLI
dcvpg mcp-server start

# Or directly
python -m dcvpg.mcp_server.server
```

The server runs on **stdio** (standard input/output), which is the protocol used by Claude Desktop and most MCP clients.

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

Restart Claude Desktop and you'll see "dcvpg" in the MCP tools panel.

## Example Prompts

Once connected, you can ask Claude:

- *"What pipelines are currently failing?"*
- *"Show me the violation details for the orders pipeline."*
- *"How many batches are in quarantine?"*
- *"Is there any schema drift in the payments contract?"*
- *"Generate a contract for the `users` table in my postgres_main connection."*
- *"Open a PR to fix the type mismatch in the orders contract."*
- *"Replay batch abc-123 now that the contract is fixed."*

## Troubleshooting

**Server can't connect to API:**  
Check `DCVPG_API_URL` and that the DCVPG API service is running. Test with `dcvpg mcp-server status`.

**Authentication errors:**  
Ensure `DCVPG_API_KEY` matches the key configured in your API service (`DCVPG_API_KEY` env var on the server side).

**Tool not showing in Claude:**  
Restart Claude Desktop after editing the config file. MCP servers are loaded at startup.
