import logging
from typing import Dict, Any

from dcvpg.ai_agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """You are an expert data engineer fixing a broken data contract YAML.

CURRENT CONTRACT YAML:
{current_yaml}

SCHEMA DIFF (contract definition vs live source schema):
{schema_diff}

VIOLATION DETAILS:
{violation_details}

Generate a corrected contract YAML that resolves all violations. Return ONLY the YAML starting with 'contract:'.
"""


class FixProposer(BaseAgent):
    """Uses an LLM to propose a corrected contract YAML from violation context."""

    def propose_fix(
        self,
        current_yaml: str,
        schema_diff: Dict[str, Any],
        violation_details: str,
    ) -> str:
        """
        Returns corrected YAML string, or the original if the LLM call fails.
        """
        prompt = _PROMPT_TEMPLATE.format(
            current_yaml=current_yaml,
            schema_diff=schema_diff,
            violation_details=violation_details,
        )
        try:
            return self.call_llm(
                prompt, system="You are a data contract YAML expert. Return only valid YAML."
            )
        except Exception as e:
            logger.error(f"FixProposer LLM call failed: {e}. Returning original YAML unchanged.")
            return current_yaml
