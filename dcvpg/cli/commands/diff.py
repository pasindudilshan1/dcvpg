import click
import os


@click.command()
@click.option("--contract", required=True, help="Contract name to diff")
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
)
def diff(contract, config_path):
    """Show schema drift between a contract definition and its live source."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.file_connector import FileConnector
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff, infer_schema_from_dataframe
        import uuid

        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        c = registry.get_contract(contract)

        conn_config = next((x for x in config.connections if x.name == c.source_connection), None)
        if not conn_config:
            click.echo(f"Error: Connection '{c.source_connection}' not found in config.")
            raise SystemExit(1)

        if conn_config.type == "postgres":
            connector = PostgresConnector()
        elif conn_config.type == "file":
            connector = FileConnector()
        else:
            click.echo(f"Error: Connector '{conn_config.type}' not supported by CLI diff.")
            raise SystemExit(1)

        connector.connect(conn_config.model_dump())
        source = getattr(c, "source_table", None) or c.name
        df = connector.fetch_sample(source=source, sample_rows=100)

        live_schema = infer_schema_from_dataframe(df)
        result = compute_schema_diff(
            [{"field": f.field, "type": f.type} for f in c.schema_fields],
            live_schema,
        )

        if not result["has_drift"]:
            click.echo(f"✅ No schema drift detected for '{contract}'.")
            return

        click.echo(f"⚠️  Schema drift detected for '{contract}':\n")
        if result["added_fields"]:
            click.echo(f"  Added in source (not in contract):")
            for f in result["added_fields"]:
                click.echo(f"    + {f}")
        if result["removed_fields"]:
            click.echo(f"  Removed from source (still in contract):")
            for f in result["removed_fields"]:
                click.echo(f"    - {f}")
        if result["type_changed"]:
            click.echo(f"  Type changes:")
            for f, change in result["type_changed"].items():
                click.echo(f"    ~ {f}: {change['contract_type']} → {change['live_type']}")

    except Exception as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
