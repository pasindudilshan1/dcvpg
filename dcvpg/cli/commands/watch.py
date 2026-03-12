import click
import os
import time
import subprocess
import sys


@click.command()
@click.option(
    "--interval",
    default=None,
    type=int,
    help="Seconds between validation runs. Overrides autowatch.interval_seconds in config.",
)
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
    help="Path to dcvpg.config.yaml",
)
def watch(interval, config_path):
    """
    Continuously validate all contracts on a schedule.

    Reads autowatch.interval_seconds from dcvpg.config.yaml by default.
    Pass --interval to override. Alerts fire automatically on failure.

    Example:
        dcvpg watch               # uses interval from config (default 60s)
        dcvpg watch --interval 30
    """
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    # Read interval from config if not overridden on CLI
    effective_interval = interval
    if effective_interval is None:
        try:
            from dcvpg.config.config_loader import load_config
            cfg = load_config(config_path)
            effective_interval = cfg.autowatch.interval_seconds
        except Exception:
            effective_interval = 60

    click.echo(f"👁  Watching — validating every {effective_interval}s. Press Ctrl+C to stop.")
    click.echo(f"    Config: {os.path.abspath(config_path)}\n")

    run_count = 0
    while True:
        run_count += 1
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"[{timestamp}] Run #{run_count}")

        result = subprocess.run(
            [sys.executable, "-m", "dcvpg", "validate", "--all", "--config", config_path],
            capture_output=False,
        )

        if result.returncode == 0:
            click.echo(f"  → All contracts passed.\n")
        else:
            click.echo(f"  → Violations found — alerts dispatched, batches quarantined.\n")

        click.echo(f"    Next run in {effective_interval}s...\n")
        time.sleep(effective_interval)
