import logging
import uuid
from typing import Optional, Any

from dcvpg.engine.models import ValidationReport
from dcvpg.ai_agents.base_agent import BaseAgent
from .github import GitHubClient

logger = logging.getLogger(__name__)


class AutoHealerAgent(BaseAgent):
    """
    Wakes up on CRITICAL violations. Fetches live schema, computes diff,
    calls LLM to propose a corrected contract YAML, and opens a GitHub PR.
    Human approval is always required before merge (auto_merge: false by default).
    """

    def __init__(self, github_token: str, repo_name: str, api_key: str = None, enabled: bool = True):
        super().__init__(api_key=api_key)
        self.enabled = enabled
        if self.enabled:
            self.gh = GitHubClient(token=github_token, repo=repo_name)

    def process_failure(
        self,
        report: ValidationReport,
        batch_id: str = None,
        contract_yaml: str = "",
        live_schema: list = None,
    ) -> Optional[str]:
        """
        Analyze the failure report and execute self-healing sequence if safe.
        Returns PR URL if successful, else None.
        """
        if not self.enabled:
            return None

        safe_violations = ["TYPE_MISMATCH", "FIELD_MISSING"]
        violating_details = [
            v for v in report.violation_details if v.violation_type in safe_violations
        ]

        if not violating_details:
            logger.info("AutoHealer skipping — violations too complex for auto-patching.")
            return None

        logger.info(f"AutoHealer activated for {report.contract_name}")

        batch_ref = (batch_id or str(uuid.uuid4()))[:8]
        branch_name = f"autoheal/{report.contract_name}-{batch_ref}"

        # Build schema diff context
        schema_diff: dict = {}
        if live_schema:
            from dcvpg.engine.reporting.schema_diff import compute_schema_diff
            contract_schema = [
                {"field": v.field, "type": v.expected_value}
                for v in report.violation_details
            ]
            schema_diff = compute_schema_diff(contract_schema, live_schema)

        violation_text = "\n".join(
            f"- Field: {v.field}, Violation: {v.violation_type}, Expected: {v.expected_value}"
            for v in violating_details
        )

        # Propose fix via LLM
        fixed_yaml = self._propose_fix(contract_yaml, schema_diff, violation_text)

        patch_file = f"contracts/{report.contract_name}.yaml"
        commit_msg = (
            f"fix({report.contract_name}): AutoHealer resolving "
            f"{violating_details[0].violation_type}"
        )

        self.gh.create_branch(branch_name)
        self.gh.create_commit(branch_name, patch_file, fixed_yaml, commit_msg)
        pr_url = self.gh.create_pull_request(
            title=f"🚨 AutoHeal Fix: {report.contract_name} — {violating_details[0].violation_type}",
            head=branch_name,
            body=(
                f"**DCVPG AutoHealer PR** — requires human review before merge.\n\n"
                f"**Violations resolved:**\n{violation_text}\n\n"
                f"**Schema diff:**\n```json\n{schema_diff}\n```"
            ),
        )
        return pr_url

    def _propose_fix(self, current_yaml: str, schema_diff: dict, violation_text: str) -> str:
        """Call LLM to propose a corrected contract YAML, or return original on failure."""
        import os
        prompt_path = os.path.join(
            os.path.dirname(__file__), "prompts", "generate_fix.txt"
        )
        if os.path.exists(prompt_path):
            with open(prompt_path) as f:
                template = f.read()
            prompt = template.format(
                current_yaml=current_yaml,
                schema_diff=schema_diff,
                violation_details=violation_text,
            )
        else:
            prompt = (
                f"You are a data contract YAML expert.\n"
                f"Current contract:\n{current_yaml}\n\n"
                f"Schema diff: {schema_diff}\n\n"
                f"Violations:\n{violation_text}\n\n"
                f"Return ONLY the corrected contract YAML starting with 'contract:'."
            )
        try:
            fixed_yaml = self.call_llm(prompt, system="You are a data contract YAML expert.")
            # Post-fix validation: ensure type consistency with allowed_values
            fixed_yaml = self._validate_type_consistency(fixed_yaml)
            return fixed_yaml
        except Exception as e:
            logger.warning(f"AutoHealer LLM call failed: {e}. Using original contract.")
            return current_yaml or "# AutoHealer could not generate fix\n"
    
    def _validate_type_consistency(self, yaml_content: str) -> str:
        """Validate and fix type/allowed_values consistency in the contract YAML."""
        import yaml
        try:
            data = yaml.safe_load(yaml_content)
            if not data or "contract" not in data:
                return yaml_content
            
            contract = data["contract"]
            if "schema" not in contract:
                return yaml_content
            
            schema = contract["schema"]
            for field in schema:
                if "allowed_values" not in field or "type" not in field:
                    continue
                
                allowed_vals = field["allowed_values"]
                if not allowed_vals:
                    continue
                
                # Infer expected type from allowed_values
                sample = allowed_vals[0]
                inferred_type = self._infer_type(sample)
                
                # If mismatch, fix the type
                if inferred_type and field["type"] != inferred_type:
                    logger.warning(
                        f"Type mismatch in field '{field.get('field', '?')}': "
                        f"type={field['type']} but allowed_values suggest {inferred_type}. Fixing..."
                    )
                    field["type"] = inferred_type
            
            # Re-serialize to YAML
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.warning(f"Type consistency validation failed: {e}. Returning original YAML.")
            return yaml_content
    
    @staticmethod
    def _infer_type(value: Any) -> Optional[str]:
        """Infer JSON schema type from a Python value."""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, dict):
            return "json"
        elif isinstance(value, list):
            return "array"
        return None
