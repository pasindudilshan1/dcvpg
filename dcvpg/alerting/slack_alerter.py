import logging
import os
from typing import Dict, Any
from .base_alerter import BaseAlerter

logger = logging.getLogger(__name__)

class SlackAlerter(BaseAlerter):
    """
    Sends structured messages to Slack using an incoming Webhook URL.
    """
    def send_alert(self, severity: str, title: str, metadata: Dict[str, Any]) -> bool:
        # Resolve URL: try env var first, then direct webhook_url in config
        webhook_url = None
        webhook_env_name = self.config.get("webhook_env")
        if webhook_env_name:
            webhook_url = os.environ.get(webhook_env_name)
            if not webhook_url:
                logger.warning(
                    f"Slack: env var '{webhook_env_name}' is not set — "
                    f"falling back to webhook_url in config"
                )
        if not webhook_url:
            webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            logger.error(
                "Slack alert skipped: no webhook URL found. "
                "Set the env var referenced by webhook_env, or add webhook_url directly to config."
            )
            return False

        # Build block kit message
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 [{severity}] Contract Violation"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Pipeline:* {metadata.get('pipeline_name')}\n*Contract:* {metadata.get('contract_name')} v{metadata.get('contract_version')}\n*Status:* FAILED"}
            }
        ]

        if "violation_details" in metadata:
            for v in metadata["violation_details"][:3]:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"• *Field:* `{v.get('field')}`\n  *Violation:* {v.get('violation_type')}\n  *Expected:* {v.get('expected_value')}\n  *Rows Affected:* {v.get('rows_affected')}"}
                })

        if self.config.get("mention_owners") and severity == "CRITICAL":
            owner = metadata.get("owner_team", "data-eng-team")
            source = metadata.get("source_owner", "source-team")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Owners:* {owner} | *Source:* {source}"}
            })

        payload = {"blocks": blocks}

        try:
            import httpx
            response = httpx.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {title}")
                return True
            else:
                logger.error(f"Slack returned {response.status_code}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Slack alert failed: {e}")
            return False

