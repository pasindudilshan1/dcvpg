import json
import os
from typing import Any, Dict, List, Tuple


def validate_config(config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a parsed dcvpg.config.yaml dict against required structure.
    Returns (is_valid, list_of_error_messages).
    """
    errors: List[str] = []

    # Required top-level keys
    required_keys = ["project", "contracts", "database"]
    for key in required_keys:
        if key not in config_dict:
            errors.append(f"Missing required top-level key: '{key}'")

    # Project section
    project = config_dict.get("project", {})
    for field in ["name", "team", "environment"]:
        if not project.get(field):
            errors.append(f"project.{field} is required.")

    # Contracts section
    contracts = config_dict.get("contracts", {})
    if not contracts.get("directory"):
        errors.append("contracts.directory is required.")

    # Database section
    database = config_dict.get("database", {})
    for field in ["host", "port", "name", "user"]:
        if not database.get(field):
            errors.append(f"database.{field} is required.")

    # Connections section (optional, but each entry must have name + type)
    for i, conn in enumerate(config_dict.get("connections", [])):
        if not conn.get("name"):
            errors.append(f"connections[{i}].name is required.")
        if not conn.get("type"):
            errors.append(f"connections[{i}].type is required.")
        valid_types = {"postgres", "mysql", "snowflake", "bigquery", "file", "s3", "gcs", "rest"}
        if conn.get("type") and conn["type"] not in valid_types:
            errors.append(
                f"connections[{i}].type '{conn['type']}' is not a known connector. "
                f"Supported: {sorted(valid_types)}"
            )

    # AI section (optional)
    ai = config_dict.get("ai", {})
    if ai and not ai.get("api_key_env") and not os.environ.get("ANTHROPIC_API_KEY"):
        errors.append(
            "ai.api_key_env is not set and ANTHROPIC_API_KEY env var is not present. "
            "AI features will not work."
        )

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_config_file(config_path: str) -> Tuple[bool, List[str]]:
    """Load and validate a dcvpg.config.yaml file at the given path."""
    import yaml

    if not os.path.exists(config_path):
        return False, [f"Config file not found: {config_path}"]

    try:
        with open(config_path) as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Failed to parse YAML: {e}"]

    if not isinstance(raw, dict):
        return False, ["Config file must be a YAML mapping (dict)."]

    return validate_config(raw)
