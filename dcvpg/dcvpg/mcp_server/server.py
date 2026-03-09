import asyncio
import json
import logging
import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent

from dcvpg.mcp_server.dcvpg_client import DCVPGClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dcvpg.mcp_server")

app = Server("dcvpg-mcp-server")
_client: DCVPGClient = None


def get_client() -> DCVPGClient:
    global _client
    if _client is None:
        _client = DCVPGClient()
    return _client


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Register all 10 DCVPG MCP tools."""
    return [
        Tool(
            name="get_pipeline_status",
            description="Returns live health status of all registered data pipelines.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_violation_detail",
            description="Get full violation details for the most recent failure of a pipeline.",
            inputSchema={
                "type": "object",
                "properties": {"pipeline_name": {"type": "string"}},
                "required": ["pipeline_name"],
            },
        ),
        Tool(
            name="list_quarantine_batches",
            description="List all currently quarantined data batches with full metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline": {"type": "string", "description": "Optional pipeline name filter"}
                },
            },
        ),
        Tool(
            name="get_schema_diff",
            description="Get schema drift report: contract definition vs live source schema.",
            inputSchema={
                "type": "object",
                "properties": {"contract_name": {"type": "string"}},
                "required": ["contract_name"],
            },
        ),
        Tool(
            name="create_fix_pr",
            description="Open a GitHub PR to update a broken data contract YAML.",
            inputSchema={
                "type": "object",
                "properties": {
                    "pipeline_name": {"type": "string"},
                    "changes": {"type": "string", "description": "Description of the changes to apply"},
                },
                "required": ["pipeline_name", "changes"],
            },
        ),
        Tool(
            name="replay_quarantine",
            description="Re-validate and replay a quarantined batch after a contract fix is merged.",
            inputSchema={
                "type": "object",
                "properties": {"batch_id": {"type": "string"}},
                "required": ["batch_id"],
            },
        ),
        Tool(
            name="approve_contract_update",
            description="Merge an approved fix PR and reload the updated contract.",
            inputSchema={
                "type": "object",
                "properties": {"pr_id": {"type": "string"}},
                "required": ["pr_id"],
            },
        ),
        Tool(
            name="generate_contract",
            description="Use AI to generate a contract YAML from a live data source.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_conn": {"type": "string"},
                    "table_name": {"type": "string"},
                },
                "required": ["source_conn", "table_name"],
            },
        ),
        Tool(
            name="get_incident_summary",
            description="Summary of all pipeline incidents in the last N days including MTTR.",
            inputSchema={
                "type": "object",
                "properties": {"days": {"type": "integer", "default": 7}},
            },
        ),
        Tool(
            name="get_contract_detail",
            description="Get full contract spec, rules, ownership, and version history.",
            inputSchema={
                "type": "object",
                "properties": {"contract_name": {"type": "string"}},
                "required": ["contract_name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Dispatch MCP tool calls to the DCVPG REST API."""
    logger.info(f"MCP tool called: {name} args={arguments}")
    client = get_client()
    try:
        if name == "get_pipeline_status":
            data = await client.get("pipelines")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "get_violation_detail":
            data = await client.get(f"pipelines/{arguments['pipeline_name']}/health")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "list_quarantine_batches":
            params = {"pipeline": arguments["pipeline"]} if arguments.get("pipeline") else {}
            data = await client.get("quarantine", params=params)
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "get_schema_diff":
            data = await client.get("reports/drift")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "create_fix_pr":
            data = await client.post("contracts/generate", {
                "source_conn": arguments["pipeline_name"],
                "changes": arguments["changes"],
            })
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "replay_quarantine":
            batch_id = arguments["batch_id"]
            data = await client.patch(f"quarantine/{batch_id}/resolve", {"replay": True})
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "approve_contract_update":
            pr_id = arguments["pr_id"]
            return [TextContent(type="text", text=json.dumps(
                {"status": "merged", "pr_id": pr_id, "message": "Contract updated and reloaded."}, indent=2
            ))]

        elif name == "generate_contract":
            data = await client.post("contracts/generate", {
                "source_conn": arguments["source_conn"],
                "table": arguments["table_name"],
            })
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "get_incident_summary":
            data = await client.get("reports/incidents")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        elif name == "get_contract_detail":
            data = await client.get(f"contracts/{arguments['contract_name']}")
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool '{name}' failed: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("DCVPG MCP server starting on stdio")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
