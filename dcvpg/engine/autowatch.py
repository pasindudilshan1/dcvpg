"""
Shared background validation loop used by both `dcvpg serve api` and
`dcvpg serve dashboard`.  Starts a daemon thread that runs
`dcvpg validate --all` immediately, then repeats every interval_seconds.
"""
import logging
import subprocess
import sys
import threading
import time

logger = logging.getLogger(__name__)


def _loop(config_path: str, interval: int) -> None:
    logger.info(f"Autowatch started — validating every {interval}s (config: {config_path})")
    while True:
        try:
            logger.info("Autowatch: running validation...")
            subprocess.run(
                [sys.executable, "-m", "dcvpg", "validate", "--all", "--config", config_path],
                capture_output=True,
            )
        except Exception as e:
            logger.error(f"Autowatch validation error: {e}")
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
