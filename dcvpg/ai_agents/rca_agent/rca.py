import logging
from dcvpg.engine.models import ValidationReport
from dcvpg.ai_agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RootCauseAgent(BaseAgent):
    """
    Subscribes to quarantine events and uses an LLM to suggest the probable
    root cause of contract violations to engineers.
    Falls back to a structured template if the LLM is unavailable.
    """

    def __init__(self, api_key: str = None):
        super().__init__(api_key=api_key)

    def analyze_incident(self, report: ValidationReport, schema_diff: dict = None) -> str:
        from dcvpg.ai_agents.rca_agent.report_builder import ReportBuilder
        builder = ReportBuilder(api_key=self.api_key)
        return builder.build_rca_report(report, schema_diff=schema_diff)
