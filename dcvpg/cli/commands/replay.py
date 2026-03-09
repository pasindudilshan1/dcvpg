import click
import os


@click.command()
@click.option("--batch-id", required=True, help="Quarantine batch ID to replay")
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
)
def replay(batch_id, config_path):
    """Re-validate a quarantined batch after a contract fix has been applied."""
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.quarantine_engine import QuarantineEngine
        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.validator import Validator

        config = load_config(config_path)
        quarantine = QuarantineEngine(config.database.model_dump())

        click.echo(f"Loading quarantined batch: {batch_id}")

        # Fetch the batch DataFrame from quarantine storage
        df, contract_name = quarantine.fetch_batch(batch_id)

        if df is None:
            click.echo(f"Error: Batch '{batch_id}' not found in quarantine store.")
            raise SystemExit(1)

        click.echo(f"  Contract : {contract_name}")
        click.echo(f"  Rows     : {len(df)}")

        registry = ContractRegistry(config.contracts.directory)
        contract = registry.get_contract(contract_name)
        custom_dir = config.extensions.custom_rules_dir if config.extensions else None
        engine = Validator(contract, custom_dir)
        report = engine.validate_batch(df, pipeline_name=contract_name, duration_ms=0)

        if report.status == "PASSED":
            quarantine.resolve_batch(batch_id)
            click.echo(f"✅ PASSED — batch '{batch_id}' resolved and released from quarantine.")
        else:
            click.echo(f"❌ FAILED — {report.violations_count} violation(s) remain:")
            for v in report.violation_details[:5]:
                click.echo(f"   • {v.field}: {v.violation_type}")
            click.echo(f"   Batch remains in quarantine.")
            raise SystemExit(1)

    except (ImportError, AttributeError) as e:
        click.echo(f"Error: {e}")
        raise SystemExit(1)
