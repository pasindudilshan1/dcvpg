import click
import os


@click.command()
@click.argument("contract_path")
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
    help="Path to dcvpg.config.yaml",
)
def register(contract_path, config_path):
    """Register a contract YAML into the runtime registry."""
    if not os.path.exists(contract_path):
        click.echo(f"Error: Contract file not found: {contract_path}")
        raise SystemExit(1)

    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.contract_loader import load_contract_from_yaml

        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        contract = load_contract_from_yaml(contract_path)
        registry.register_contract(contract)
        click.echo(f"✅ Registered: {contract.name} v{contract.version}")
        click.echo(f"   Directory : {config.contracts.directory}")
        click.echo(f"   Owner     : {contract.owner_team} / {contract.source_owner}")
        click.echo(f"   Fields    : {len(contract.schema_fields)}")
    except Exception as e:
        click.echo(f"Error registering contract: {e}")
        raise SystemExit(1)
