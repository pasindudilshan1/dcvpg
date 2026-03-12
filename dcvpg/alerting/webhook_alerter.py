import logging
import os
from typing import Dict, Any
from .base_alerter import BaseAlerter

logger = logging.getLogger(__name__)


class WebhookAlerter(BaseAlerter):
    """
    Sends alert payloads as JSON POST requests to a generic HTTP webhook endpoint.
    Supports optional Bearer token authentication.
    """

    def send_alert(self, severity: str, title: str, metadata: Dict[str, Any]) -> bool:
        url_env = self.config.get("url_env")
        webhook_url = os.environ.get(url_env) if url_env else self.config.get("url")

        if not webhook_url:
            logger.error("Webhook URL not configured")
            return False

        token_env = self.config.get("token_env")
        token = os.environ.get(token_env) if token_env else self.config.get("token")

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {
            "severity": severity,
            "title": title,
            "source": "dcvpg",
            **metadata,
        }

        try:
            import httpx
            response = httpx.post(webhook_url, json=payload, headers=headers, timeout=10)
            if response.status_code < 300:
                logger.info(f"Webhook alert sent to {webhook_url}")
                return True
            else:
                logger.error(f"Webhook returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Webhook alert failed: {e}")
            return False
