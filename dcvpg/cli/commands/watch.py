import click
import os
import time
import subprocess
import sys


@click.command()
@click.option(
    "--interval",
    default=60,
    show_default=True,
    type=int,
    help="Seconds between validation runs.",
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

    Runs `dcvpg validate --all` every INTERVAL seconds.
    Alerts are fired automatically on failure via the alerting config.
    The dashboard and API will reflect each run immediately.

    Example:
        dcvpg watch --interval 300   # validate every 5 minutes
    """
    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    click.echo(f"👁  Watching — validating every {interval}s. Press Ctrl+C to stop.")
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

        click.echo(f"    Next run in {interval}s...\n")
        time.sleep(interval)
