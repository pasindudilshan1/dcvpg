import logging
import os
from typing import Dict, Any
from .base_alerter import BaseAlerter

logger = logging.getLogger(__name__)

class PagerDutyAlerter(BaseAlerter):
    """
    Sends structured incidents to PagerDuty over Events API v2.
    """
    def send_alert(self, severity: str, title: str, metadata: Dict[str, Any]) -> bool:
        api_key_env_name = self.config.get("api_key_env")
        api_key = os.environ.get(api_key_env_name) if api_key_env_name else None
        service_id = self.config.get("service_id")

        if not api_key:
            logger.error("PagerDuty API Key not found in config/env")
            return False

        incident = {
            "routing_key": api_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"DCVPG {severity}: {title} on {metadata.get('contract_name')}",
                "severity": "critical" if severity == "CRITICAL" else "warning",
                "source": metadata.get("pipeline_name"),
                "custom_details": metadata,
            },
        }

        try:
            import httpx
            response = httpx.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=incident,
                timeout=10,
            )
            if response.status_code in (200, 202):
                logger.info(f"PagerDuty incident triggered on service {service_id}")
                return True
            else:
                logger.error(f"PagerDuty returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"PagerDuty alert failed: {e}")
            return False
