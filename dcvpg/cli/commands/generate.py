import click
import os


@click.command()
@click.option("--source", required=True, help="Connection name in dcvpg.config.yaml")
@click.option("--table", required=True, help="Table or source name to profile")
@click.option("--sample-rows", default=1000, show_default=True, help="Number of rows to profile")
@click.option("--config", "config_path", default="./dcvpg.config.yaml", show_default=True)
@click.option("--output-dir", default="./contracts/generated", show_default=True)
def generate(source, table, sample_rows, config_path, output_dir):
    """Generate a contract YAML from a live data source using AI."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.mysql_connector import MySQLConnector
        from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
        from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
        from dcvpg.engine.connectors.s3_connector import S3Connector
        from dcvpg.engine.connectors.gcs_connector import GCSConnector
        from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
        from dcvpg.engine.connectors.file_connector import FileConnector
        from dcvpg.ai_agents.contract_generator.generator_agent import ContractGeneratorAgent

        _CONNECTOR_MAP = {
            "postgres":  PostgresConnector,
            "mysql":     MySQLConnector,
            "snowflake": SnowflakeConnector,
            "bigquery":  BigQueryConnector,
            "s3":        S3Connector,
            "gcs":       GCSConnector,
            "rest":      RestApiConnector,
            "file":      FileConnector,
        }

        config = load_config(config_path)
        conn_config = next((c for c in config.connections if c.name == source), None)
        if not conn_config:
            click.echo(f"Error: Connection '{source}' not found in {config_path}")
            raise SystemExit(1)

        connector_cls = _CONNECTOR_MAP.get(conn_config.type)
        if connector_cls is None:
            supported = ", ".join(_CONNECTOR_MAP.keys())
            click.echo(
                f"Error: Connector type '{conn_config.type}' is not supported.\n"
                f"Supported types: {supported}"
            )
            raise SystemExit(1)

        click.echo(f"Connecting to {source} ({conn_config.type})...")
        connector = connector_cls()
        connector.connect(conn_config.model_dump())

        click.echo(f"Sampling {sample_rows} rows from {table}...")
        df = connector.fetch_sample(source=table, sample_rows=sample_rows)
        click.echo(f"Profiling {len(df.columns)} fields...")

        ai_config = config.ai or {}
        api_key_env = ai_config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.environ.get(api_key_env)
        model = ai_config.get("model", "claude-sonnet-4-6")

        agent = ContractGeneratorAgent(api_key=api_key, model=model)
        click.echo("Generating contract with AI...")
        yaml_content = agent.generate(source, table, df)

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{table}.yaml")
        with open(output_path, "w") as f:
            f.write(yaml_content)

        click.echo(f"\n✅ Contract saved: {output_path}")
        click.echo(f"   Fields profiled: {len(df.columns)}")
        click.echo("\nReview and register:")
        click.echo(f"$ dcvpg register {output_path}")

    except ImportError as e:
        click.echo(f"Import error: {e}. Install AI extras: pip install dcvpg[ai]")
        raise SystemExit(1)
