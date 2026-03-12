"""
Shared background validation loop used by both `dcvpg serve api` and
`dcvpg serve dashboard`.  Starts a daemon thread that runs validation
in-process immediately, then repeats every interval_seconds.
"""
import logging
import os
import threading
import time
import uuid

logger = logging.getLogger(__name__)


_CONNECTOR_MAP_CACHE = None


def _get_connector_map():
    global _CONNECTOR_MAP_CACHE
    if _CONNECTOR_MAP_CACHE is None:
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        from dcvpg.engine.connectors.mysql_connector import MySQLConnector
        from dcvpg.engine.connectors.snowflake_connector import SnowflakeConnector
        from dcvpg.engine.connectors.bigquery_connector import BigQueryConnector
        from dcvpg.engine.connectors.s3_connector import S3Connector
        from dcvpg.engine.connectors.gcs_connector import GCSConnector
        from dcvpg.engine.connectors.rest_api_connector import RestApiConnector
        from dcvpg.engine.connectors.file_connector import FileConnector
        _CONNECTOR_MAP_CACHE = {
            "postgres":  PostgresConnector,
            "mysql":     MySQLConnector,
            "snowflake": SnowflakeConnector,
            "bigquery":  BigQueryConnector,
            "s3":        S3Connector,
            "gcs":       GCSConnector,
            "rest":      RestApiConnector,
            "file":      FileConnector,
        }
    return _CONNECTOR_MAP_CACHE


def _run_validation(config_path: str) -> None:
    """Run a full validate-all cycle in-process (no subprocess)."""
    from dcvpg.config.config_loader import load_config
    from dcvpg.engine.registry import ContractRegistry
    from dcvpg.engine.validator import Validator
    from dcvpg.engine.quarantine_engine import QuarantineEngine
    from dcvpg.engine.report_store import ReportStore

    config = load_config(config_path)
    registry = ContractRegistry(config.contracts.directory)
    contracts = registry.list_contracts()
    store = ReportStore(os.path.dirname(os.path.abspath(config_path)))
    connector_map = _get_connector_map()

    for c in contracts:
        conn_config = next((x for x in config.connections if x.name == c.source_connection), None)
        if not conn_config:
            logger.warning(f"Autowatch: connection '{c.source_connection}' not found for {c.name} — skipping")
            continue

        connector_cls = connector_map.get(conn_config.type)
        if not connector_cls:
            logger.warning(f"Autowatch: unsupported connector type '{conn_config.type}' for {c.name} — skipping")
            continue

        try:
            connector = connector_cls()
            connector.connect(conn_config.model_dump())
            source = getattr(c, "source_table", None) or c.name
            start = time.time()
            df = connector.fetch_batch(source=source, batch_id=str(uuid.uuid4()))
            duration_ms = int((time.time() - start) * 1000)
            custom_dir = config.extensions.custom_rules_dir if config.extensions else None
            engine = Validator(c, custom_dir)
            report = engine.validate_batch(df, pipeline_name=c.name, duration_ms=duration_ms)

            store.save_run({
                "pipeline_name": c.name,
                "contract_name": c.name,
                "contract_version": c.version,
                "status": report.status,
                "rows_processed": report.rows_processed,
                "violations_count": report.violations_count,
                "duration_ms": duration_ms,
                "violation_details": [v.model_dump(exclude_none=True) for v in report.violation_details],
            })

            if report.status != "PASSED":
                batch_id = str(uuid.uuid4())
                quarantine = QuarantineEngine(config.database.model_dump())
                quarantine.isolate_batch(report, batch_id)
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
                if config.alerting:
                    try:
                        from dcvpg.alerting.alert_manager import AlertManager
                        am = AlertManager(config.alerting.model_dump())
                        if am.alerters:
                            am.dispatch_alert(
                                title=f"Contract violation: {c.name}",
                                report=report,
                                severity="CRITICAL",
                            )
                            channels = ", ".join(a.__class__.__name__ for a in am.alerters)
                            logger.info(f"Autowatch: alerts dispatched via {channels} for {c.name}")
                        else:
                            logger.warning(f"Autowatch: no alerters enabled for {c.name} — check alerting config")
                    except Exception as alert_err:
                        logger.error(f"Autowatch: alert dispatch failed for {c.name}: {alert_err}")

            logger.info(f"Autowatch: {c.name} → {report.status} ({report.rows_processed} rows, {report.violations_count} violations)")

        except Exception as e:
            logger.error(f"Autowatch: error validating {c.name}: {e}", exc_info=True)


def _loop(config_path: str, interval: int) -> None:
    logger.info(f"Autowatch started — validating every {interval}s (config: {config_path})")
    while True:
        try:
            logger.info("Autowatch: running validation cycle...")
            _run_validation(config_path)
        except Exception as e:
            logger.error(f"Autowatch: cycle error: {e}", exc_info=True)
        time.sleep(interval)


def start_if_enabled(config_path: str) -> bool:
    """
    Reads autowatch config from config_path.  If enabled, starts the
    background thread immediately (first run happens right away).
    Returns True if the thread was started, False otherwise.
    """
    import os
    if not os.path.exists(config_path):
        return False
    try:
        from dcvpg.config.config_loader import load_config
        cfg = load_config(config_path)
        if not cfg.autowatch.enabled:
            return False
        interval = cfg.autowatch.interval_seconds
        t = threading.Thread(target=_loop, args=(config_path, interval), daemon=True)
        t.start()
        logger.info(f"Autowatch thread started (interval={interval}s)")
        return True
    except Exception as e:
        logger.warning(f"Could not start autowatch: {e}")
        return False
