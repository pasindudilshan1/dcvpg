import importlib
import logging
from typing import Dict, Any, List
from .base_alerter import BaseAlerter
from .slack_alerter import SlackAlerter
from .pagerduty_alerter import PagerDutyAlerter
from dcvpg.engine.models import ValidationReport

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Reads the alerting section from config and routes alerts to all active channels.
    """
    
    def __init__(self, alerting_config: Dict[str, Any]):
        self.config = alerting_config
        self.alerters: List[BaseAlerter] = []
        self._initialize_alerters()
        
    def _initialize_alerters(self):
        slack_config = self.config.get("slack", {})
        if slack_config.get("enabled"):
            self.alerters.append(SlackAlerter(slack_config))
            
        pd_config = self.config.get("pagerduty", {})
        if pd_config.get("enabled"):
            self.alerters.append(PagerDutyAlerter(pd_config))
            
        # TODO: Teams / Webhooks logic here
        
        custom_config = self.config.get("custom_alerter", {})
        if custom_config.get("enabled"):
            module_path = custom_config.get("module")
            if module_path:
                try:
                    parts = module_path.rsplit(".", 1)
                    if len(parts) == 2:
                        mod = importlib.import_module(parts[0])
                        alerter_class = getattr(mod, parts[1])
                        if not issubclass(alerter_class, BaseAlerter):
                            raise TypeError(f"'{parts[1]}' must inherit from BaseAlerter")
                        self.alerters.append(alerter_class(custom_config))
                except Exception as e:
                    logger.error(f"Failed to load custom alerter {module_path}: {e}")
                    
    def dispatch_alert(self, title: str, report: ValidationReport, severity: str = "CRITICAL"):
        """
        Send an alert to all configured channels based on severity.
        """
        config_threshold = self.config.get("default_severity_threshold", "WARNING").upper()
        
        # Simple severity hierarchy
        levels = {"INFO": 1, "WARNING": 2, "CRITICAL": 3}
        if levels.get(severity, 0) < levels.get(config_threshold, 2):
            logger.info(f"Skipping alert dispatch: Event severity '{severity}' is below threshold '{config_threshold}'")
            return
            
        metadata = report.model_dump()
        
        for alerter in self.alerters:
            try:
                # Some alerters might have bespoke severity overrides
                alerter_threshold = alerter.config.get("severity_threshold")
                if alerter_threshold and levels.get(severity, 0) < levels.get(alerter_threshold, 2):
                    continue

                result = alerter.send_alert(severity, title, metadata)
                if not result:
                    logger.warning(
                        f"{alerter.__class__.__name__}: send_alert returned False — "
                        f"check logs above for the specific reason (missing URL, HTTP error, etc.)"
                    )
            except Exception as e:
                logger.error(f"Alerter {alerter.__class__.__name__} failed to dispatch: {e}")
