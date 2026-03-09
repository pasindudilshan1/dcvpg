import json
import logging
import os
from typing import Dict, Any
from .base_alerter import BaseAlerter

logger = logging.getLogger(__name__)


class TeamsAlerter(BaseAlerter):
    """
    Sends structured Adaptive Card alerts to Microsoft Teams via an incoming webhook.
    """

    def send_alert(self, severity: str, title: str, metadata: Dict[str, Any]) -> bool:
        webhook_env_name = self.config.get("webhook_env")
        webhook_url = os.environ.get(webhook_env_name) if webhook_env_name else None

        if not webhook_url:
            logger.error("Teams webhook URL not found in config/env")
            return False

        color = "attention" if severity == "CRITICAL" else "warning"

        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "size": "Large",
                                "weight": "Bolder",
                                "text": f"🚨 [{severity}] {title}",
                                "color": color,
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {"title": "Pipeline", "value": metadata.get("pipeline_name", "—")},
                                    {"title": "Contract", "value": f"{metadata.get('contract_name')} v{metadata.get('contract_version')}"},
                                    {"title": "Status", "value": metadata.get("status", "FAILED")},
                                    {"title": "Rows Processed", "value": str(metadata.get("rows_processed", 0))},
                                    {"title": "Violations", "value": str(metadata.get("violations_count", 0))},
                                ],
                            },
                        ],
                    },
                }
            ],
        }

        # httpx.post(webhook_url, json=card)
        logger.info(f"TEAMS DUMMY DISPATCH: {json.dumps(card)}")
        return True
