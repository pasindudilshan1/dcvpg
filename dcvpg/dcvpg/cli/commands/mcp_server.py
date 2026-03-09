import click
import os


@click.group()
def mcp_server():
    """Manage the DCVPG MCP Server for AI assistant integration."""
    pass


@mcp_server.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8765, show_default=True, type=int)
@click.option("--api-key", envvar="DCVPG_API_KEY", help="DCVPG REST API key")
def start(host, port, api_key):
    """Start the MCP Server on stdio (for Claude Desktop) or TCP."""
    try:
        import asyncio
        from dcvpg.mcp_server.server import main as server_main

        if api_key:
            os.environ["DCVPG_API_KEY"] = api_key

        click.echo("Starting DCVPG MCP Server (stdio mode)...")
        click.echo(f"  API URL : {os.environ.get('DCVPG_API_URL', 'http://localhost:8000/api/v1')}")
        asyncio.run(server_main())
    except ImportError as e:
        click.echo(f"Error: MCP package not installed. Run: pip install dcvpg[mcp]\n{e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        click.echo("\nMCP Server stopped.")


@mcp_server.command()
def status():
    """Check MCP server configuration and connectivity."""
    api_url = os.environ.get("DCVPG_API_URL", "http://localhost:8000/api/v1")
    api_key = os.environ.get("DCVPG_API_KEY", "(not set)")
    mcp_keys = os.environ.get("MCP_API_KEYS", "(not set)")
    click.echo("DCVPG MCP Server Config:")
    click.echo(f"  DCVPG_API_URL  : {api_url}")
    click.echo(f"  DCVPG_API_KEY  : {'(set)' if api_key != '(not set)' else '(not set)'}")
    click.echo(f"  MCP_API_KEYS   : {'(set)' if mcp_keys != '(not set)' else '(not set)'}")
