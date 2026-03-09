import json
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
        webhook_env_name = self.config.get("webhook_env")
        webhook_url = os.environ.get(webhook_env_name) if webhook_env_name else None
        
        if not webhook_url:
            logger.error("Slack webhook URL not found in config/env")
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
        
        # Add violation details
        if "violation_details" in metadata:
            for v in metadata["violation_details"][:3]: # Max 3 to not spam
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"• *Field:* `{v.get('field')}`\n  *Violation:* {v.get('violation_type')}\n  *Expected:* {v.get('expected_value')}\n  *Rows Affected:* {v.get('rows_affected')}"}
                })
        
        if self.config.get("mention_owners") and severity == "CRITICAL":
            # In a real scenario we'd map team names to Slack IDs
            owner = metadata.get("owner_team", "@data-eng-team")
            source = metadata.get("source_owner", "@source-team")
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Owners:* {owner} | *Source:* {source}"}
            })

        payload = {"blocks": blocks}
        
        # httpx post to Slack
        # response = httpx.post(webhook_url, json=payload)
        logger.info(f"SLACK DUMMY DISPATCH: {json.dumps(payload)}")
        return True
