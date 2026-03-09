import click
import os


@click.command()
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(config_path, as_json):
    """Show pass/fail status of all registered contracts."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry

        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        contracts = registry.list_contracts()

        if not contracts:
            click.echo("No contracts registered.")
            return

        if as_json:
            import json
            rows = [
                {
                    "name": c.name,
                    "version": c.version,
                    "owner_team": c.owner_team,
                    "source_connection": c.source_connection,
                    "fields": len(c.schema_fields),
                }
                for c in contracts
            ]
            click.echo(json.dumps(rows, indent=2))
            return

        click.echo(f"{'CONTRACT':<35} {'VERSION':<10} {'OWNER':<20} {'FIELDS'}")
        click.echo("-" * 80)
        for c in contracts:
            click.echo(f"{c.name:<35} {c.version:<10} {c.owner_team:<20} {len(c.schema_fields)}")

        click.echo(f"\nTotal: {len(contracts)} contract(s) registered.")

    except Exception as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
