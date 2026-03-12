import click
import os
import uuid
import time


@click.command()
@click.option("--all", "validate_all", is_flag=True, help="Validate all registered contracts")
@click.option("--contract", help="Validate a specific contract by name")
@click.option(
    "--config",
    "config_path",
    default="./dcvpg.config.yaml",
    show_default=True,
    help="Path to dcvpg.config.yaml",
)
def validate(validate_all, contract, config_path):
    """Run validation manually against configured data sources."""
    if not validate_all and not contract:
        click.echo("Please specify --all or --contract <name>")
        raise SystemExit(1)

    if not os.path.exists(config_path):
        click.echo(f"Error: Config file not found: {config_path}")
        raise SystemExit(1)

    try:
        from dcvpg.config.config_loader import load_config
        from dcvpg.engine.registry import ContractRegistry
        from dcvpg.engine.validator import Validator
        from dcvpg.engine.quarantine_engine import QuarantineEngine
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.mysql_connector import MySQLConnector
        from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
        from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
        from dcvpg.engine.connectors.s3_connector import S3Connector
        from dcvpg.engine.connectors.gcs_connector import GCSConnector
        from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
        from dcvpg.engine.connectors.file_connector import FileConnector

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

        from dcvpg.engine.report_store import ReportStore

        config = load_config(config_path)
        registry = ContractRegistry(config.contracts.directory)
        contracts = registry.list_contracts() if validate_all else [registry.get_contract(contract)]

        store = ReportStore(os.path.dirname(os.path.abspath(config_path)))

        def _get_connector(type_str):
            connector_cls = _CONNECTOR_MAP.get(type_str)
            if connector_cls is None:
                supported = ", ".join(_CONNECTOR_MAP.keys())
                raise NotImplementedError(
                    f"Connector for '{type_str}' not available in CLI. Supported: {supported}"
                )
            return connector_cls()

        pass_count = 0
        fail_count = 0

        for c in contracts:
            click.echo(f"Validating {c.name} v{c.version}...")
            conn_config = next((x for x in config.connections if x.name == c.source_connection), None)
            if not conn_config:
                click.echo(f"  ⚠️  Connection '{c.source_connection}' not found in config — skipping")
                fail_count += 1
                continue

            try:
                connector = _get_connector(conn_config.type)
                connector.connect(conn_config.model_dump())
                source = getattr(c, "source_table", None) or c.name
                start = time.time()
                df = connector.fetch_batch(source=source, batch_id=str(uuid.uuid4()))
                duration_ms = int((time.time() - start) * 1000)
                custom_dir = config.extensions.custom_rules_dir if config.extensions else None
                engine = Validator(c, custom_dir)
                report = engine.validate_batch(df, pipeline_name=c.name, duration_ms=duration_ms)

                # --- Anomaly detection (statistical baselines, no LLM) ---
                anomalies = []
                try:
                    from dcvpg.ai_agents.anomaly_detector.detector_agent import AnomalyDetectorAgent
                    baselines_path = os.path.join(os.path.dirname(os.path.abspath(config_path)), ".dcvpg", "baselines")
                    anomaly_agent = AnomalyDetectorAgent(store_path=baselines_path)
                    anomalies = anomaly_agent.detect(c, df)
                    if anomalies:
                        click.echo(f"  ⚠️  {len(anomalies)} anomaly(ies): " + ", ".join(a["anomaly_type"] for a in anomalies))
                except Exception as anomaly_err:
                    click.echo(f"  ℹ️  Anomaly detection skipped: {anomaly_err}")

                # Persist run to the file-based store so the API/dashboard can read it
                store.save_run({
                    "pipeline_name": c.name,
                    "contract_name": c.name,
                    "contract_version": c.version,
                    "status": report.status,
                    "rows_processed": report.rows_processed,
                    "violations_count": report.violations_count,
                    "duration_ms": duration_ms,
                    "violation_details": [v.model_dump(exclude_none=True) for v in report.violation_details],
                    "anomalies": anomalies,
                })

                if report.status == "PASSED":
                    click.echo(f"  ✅ PASSED — {report.rows_processed} rows in {duration_ms}ms")
                    pass_count += 1
                else:
                    click.echo(
                        f"  ❌ FAILED — {report.violations_count} violations on {report.rows_processed} rows"
                    )
                    for v in report.violation_details[:5]:
                        click.echo(f"     • {v.field}: {v.violation_type} (rows: {v.rows_affected})")
                    fail_count += 1
                    batch_id = str(uuid.uuid4())
                    quarantine = QuarantineEngine(config.database.model_dump())
                    quarantine.isolate_batch(report, batch_id)
                    # Persist each violation group as a quarantine event
                    for v in report.violation_details:
                        store.save_quarantine({
                            "batch_id": batch_id,
                            "pipeline_name": c.name,
                            "contract_name": c.name,
                            "contract_version": c.version,
                            "violation_type": v.violation_type or "UNKNOWN",
                            "affected_field": v.field or "unknown",
                            "rows_affected": v.rows_affected or 0,
                        })

                    # --- Root Cause Analysis (LLM via Claude, skipped if no ANTHROPIC_API_KEY) ---
                    try:
                        from dcvpg.ai_agents.rca_agent.rca import RootCauseAgent
                        rca = RootCauseAgent()
                        rca_report = rca.analyze_incident(report)
                        click.echo(f"\n  🧠 Root Cause Analysis:\n{rca_report}\n")
                    except Exception as rca_err:
                        click.echo(f"  ℹ️  RCA skipped (set ANTHROPIC_API_KEY to enable): {rca_err}")

                    # Fire alerts to all configured channels (Slack, PagerDuty, etc.)
                    if config.alerting:
                        try:
                            from dcvpg.alerting.alert_manager import AlertManager
                            alert_manager = AlertManager(config.alerting.model_dump())
                            if not alert_manager.alerters:
                                click.echo(f"  ℹ️  No alerters enabled (check alerting config)")
                            else:
                                alert_manager.dispatch_alert(
                                    title=f"Contract violation: {c.name}",
                                    report=report,
                                    severity="CRITICAL",
                                )
                                channels = ", ".join(a.__class__.__name__ for a in alert_manager.alerters)
                                click.echo(f"  🔔 Alerts dispatched via: {channels}")
                        except Exception as alert_err:
                            click.echo(f"  ⚠️  Alert dispatch failed: {alert_err}")

            except Exception as e:
                click.echo(f"  💥 Error validating {c.name}: {e}")
                fail_count += 1

        click.echo(f"\nResults: {pass_count} PASSED | {fail_count} FAILED")
        if fail_count > 0:
            raise SystemExit(1)

    except ImportError as e:
        click.echo(f"Import error: {e}. Is dcvpg properly installed?")
        raise SystemExit(1)
