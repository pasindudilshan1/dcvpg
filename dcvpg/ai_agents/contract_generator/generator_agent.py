import logging
import os
from typing import Optional

import pandas as pd

from dcvpg.ai_agents.base_agent import BaseAgent
from .profiler import profile_dataframe

logger = logging.getLogger(__name__)


class ContractGeneratorAgent(BaseAgent):
    """Generates a data contract YAML from a live data source sample using AI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-6"):
        super().__init__(api_key=api_key, model=model)

    def generate(
        self, source_name: str, table_name: str, df_sample: Optional[pd.DataFrame] = None
    ) -> str:
        """
        Profiles the dataframe, invokes LLM to infer types, rules and bounds,
        and returns the generated Contract YAML string.
        """
        if df_sample is None or (hasattr(df_sample, "empty") and df_sample.empty):
            logger.warning("No DataFrame sample provided. Returning minimal contract.")
            return self._minimal_contract(source_name, table_name)

        profile = profile_dataframe(df_sample)
        profile_text = "\n".join(
            f"  - field: {p['field']}, inferred_type: {p['inferred_type']}, "
            f"null_rate: {p['null_rate']}, unique_rate: {p['unique_rate']}"
            + (f", min: {p['min']}, max: {p['max']}" if "min" in p else "")
            + (f", sample_values: {p['sample_values']}" if p.get("sample_values") else "")
            for p in profile
        )

        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "generate_contract.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path) as f:
                template = f.read()
            prompt = template.format(
                source_name=source_name, table_name=table_name, field_profiles=profile_text
            )
        else:
            prompt = self._default_prompt(source_name, table_name, profile_text)

        try:
            return self.call_llm(
                prompt,
                system="You are a data contract YAML generator. Return ONLY valid YAML starting with 'contract:'.",
            )
        except Exception as e:
            logger.warning(f"LLM call failed: {e}. Falling back to profile-based generation.")
            return self._generate_from_profile(source_name, table_name, profile)

    def _default_prompt(self, source_name: str, table_name: str, profile_text: str) -> str:
        return (
            f"Generate a DCVPG data contract YAML for table '{table_name}' from source '{source_name}'.\n"
            f"Field profiles:\n{profile_text}\n\n"
            f"Rules:\n"
            f"- Use inferred_type for the 'type' field (integer/float/string/timestamp/boolean)\n"
            f"- Set nullable: false only when null_rate is 0.0\n"
            f"- Set unique: true only when unique_rate is 1.0 and name looks like an ID\n"
            f"- Add allowed_values if sample_values has <= 10 entries\n"
            f"- Add min/max for numeric fields\n"
            f"- Output ONLY the YAML, no explanation, starting with 'contract:'"
        )

    def _generate_from_profile(self, source_name: str, table_name: str, profile: list) -> str:
        """Fallback: generate contract YAML directly from profile without LLM."""
        lines = [
            "contract:",
            f"  name: {table_name}_generated",
            '  version: "1.0"',
            "  owner_team: data-engineering",
            "  source_owner: unknown",
            f"  source_connection: {source_name}",
            f"  source_table: {table_name}",
            '  description: "AI-Generated contract from metadata profiling"',
            "  schema:",
        ]
        for p in profile:
            lines.append(f"    - field: {p['field']}")
            lines.append(f"      type: {p['inferred_type']}")
            if p["null_rate"] == 0.0:
                lines.append("      nullable: false")
            if p.get("unique_rate") == 1.0 and p["inferred_type"] in ("integer", "string"):
                lines.append("      unique: true")
            if "min" in p and p["inferred_type"] in ("integer", "float"):
                lines.append(f"      min: {p['min']}")
                lines.append(f"      max: {p['max']}")
            if p.get("sample_values") and p["unique_count"] <= 10:
                vals = [
                    f'"{v}"' if isinstance(v, str) else str(v)
                    for v in p["sample_values"]
                ]
                lines.append(f"      allowed_values: [{', '.join(vals)}]")
        return "\n".join(lines)

    def _minimal_contract(self, source_name: str, table_name: str) -> str:
        return (
            f"contract:\n"
            f"  name: {table_name}_generated\n"
            f'  version: "1.0"\n'
            f"  owner_team: data-engineering\n"
            f"  source_owner: unknown\n"
            f"  source_connection: {source_name}\n"
            f"  source_table: {table_name}\n"
            f'  description: "AI-Generated contract (no sample data provided)"\n'
            f"  schema:\n"
            f"    - field: id\n"
            f"      type: integer\n"
            f"      nullable: false\n"
            f"      unique: true\n"
        )
