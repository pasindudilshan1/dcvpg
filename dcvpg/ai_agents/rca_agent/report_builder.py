import logging
from typing import Any, Dict, Optional

from dcvpg.ai_agents.base_agent import BaseAgent
from dcvpg.engine.models import ValidationReport

logger = logging.getLogger(__name__)

_RCA_PROMPT = """You are a data engineering expert investigating a data quality violation.

PIPELINE: {pipeline_name}
CONTRACT: {contract_name} v{contract_version}
VIOLATIONS ({count} total):
{violation_text}

SCHEMA DIFF:
{schema_diff}

Provide a concise Root Cause Analysis:
ROOT CAUSE: <one sentence>
CONFIDENCE: <LOW|MEDIUM|HIGH>
DETAILS: <2-3 sentences>
REMEDIATION:
  1. <step>
  2. <step>
NOTIFY: <team>
"""


class ReportBuilder(BaseAgent):
    """Generates a Root Cause Analysis report from a ValidationReport using LLM."""

    def build_rca_report(
        self,
        report: ValidationReport,
        schema_diff: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Calls the LLM to produce an RCA report. Falls back to a template if LLM fails."""
        violation_text = "\n".join(
            f"- Field: {v.field}, Type: {v.violation_type}, Expected: {v.expected_value}, Rows: {v.rows_affected}"
            for v in report.violation_details
        )

        prompt = _RCA_PROMPT.format(
            pipeline_name=report.pipeline_name,
            contract_name=report.contract_name,
            contract_version=report.contract_version,
            count=report.violations_count,
            violation_text=violation_text or "No details available.",
            schema_diff=schema_diff or "Not available.",
        )

        try:
            return self.call_llm(
                prompt,
                system="You are a senior data engineer diagnosing pipeline failures. Be concise and actionable.",
            )
        except Exception as e:
            logger.warning(f"RCA LLM call failed: {e}. Returning fallback report.")
            return self._fallback_report(report)

    def _fallback_report(self, report: ValidationReport) -> str:
        lines = [
            "ROOT CAUSE: Unknown \u2014 LLM unavailable.",
            "CONFIDENCE: LOW",
            f"DETAILS: {report.violations_count} violation(s) detected in pipeline '{report.pipeline_name}' "
            f"contract '{report.contract_name}' v{report.contract_version}.",
            "REMEDIATION:",
            "  1. Review the violation details in the quarantine log.",
            "  2. Check recent upstream schema changes.",
            f"NOTIFY: {report.contract_name.split('_')[0]}-team",
        ]
        return "\n".join(lines)
