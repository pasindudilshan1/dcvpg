import click
import os
import sys
import subprocess


@click.group()
def serve():
    """Start DCVPG services (REST API or Dashboard)."""
    pass


@serve.command()
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload (development only).")
@click.option("--api-key", envvar="DCVPG_API_KEY", help="Override DCVPG_API_KEY env var.")
def api(host, port, reload, api_key):
    """Start the DCVPG REST API (FastAPI / uvicorn)."""
    if api_key:
        os.environ["DCVPG_API_KEY"] = api_key

    click.echo("Starting DCVPG REST API...")
    click.echo(f"  URL      : http://{host}:{port}")
    click.echo(f"  Docs     : http://{host}:{port}/docs")
    click.echo(f"  API key  : {'(set)' if os.environ.get('DCVPG_API_KEY') else 'my-secret-key (default)'}")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "dcvpg.api.main:app",
        "--host", host,
        "--port", str(port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\nAPI server stopped.")
    except FileNotFoundError:
        click.echo("Error: uvicorn not found. Run: pip install dcvpg")
        raise SystemExit(1)


@serve.command()
@click.option("--host", default="localhost", show_default=True)
@click.option("--port", default=8501, show_default=True, type=int)
@click.option("--api-url", envvar="DCVPG_API_URL", default="http://localhost:8000/api/v1", show_default=True)
@click.option("--api-key", envvar="DCVPG_API_KEY", help="Override DCVPG_API_KEY env var.")
@click.option("--config", "config_path", envvar="DCVPG_CONFIG_PATH", default="./dcvpg.config.yaml", show_default=True)
def dashboard(host, port, api_url, api_key, config_path):
    """Start the DCVPG Streamlit Dashboard."""
    if api_key:
        os.environ["DCVPG_API_KEY"] = api_key
    os.environ["DCVPG_API_URL"] = api_url
    os.environ["DCVPG_CONFIG_PATH"] = os.path.abspath(config_path)

    # Start background validation loop if autowatch is enabled
    from dcvpg.engine.autowatch import start_if_enabled
    started = start_if_enabled(os.path.abspath(config_path))
    if started:
        click.echo("  Autowatch : enabled — validation running in background")
    else:
        click.echo("  Autowatch : disabled — run `dcvpg validate --all` manually")

    try:
        import dcvpg.dashboard.app as _app_module
        app_path = os.path.abspath(_app_module.__file__)
    except ImportError:
        click.echo("Error: Dashboard module not found. Run: pip install dcvpg")
        raise SystemExit(1)

    click.echo("Starting DCVPG Dashboard...")
    click.echo(f"  URL      : http://{host}:{port}")
    click.echo(f"  API URL  : {api_url}")

    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.address", host,
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        click.echo("\nDashboard stopped.")
    except FileNotFoundError:
        click.echo("Error: streamlit not found. Run: pip install dcvpg")
        raise SystemExit(1)
