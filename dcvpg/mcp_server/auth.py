import os
import secrets
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_VALID_KEYS: set = set()


def load_api_keys() -> None:
    """Load valid API keys from the MCP_API_KEYS environment variable (comma-separated)."""
    raw = os.environ.get("MCP_API_KEYS", "")
    if raw:
        _VALID_KEYS.update(k.strip() for k in raw.split(",") if k.strip())


def validate_api_key(key: Optional[str]) -> bool:
    """Returns True if the key is valid. Always loads from env on first call."""
    if not _VALID_KEYS:
        load_api_keys()
    # If no keys configured, allow all (dev mode)
    if not _VALID_KEYS:
        logger.warning("MCP_API_KEYS not set — running in unauthenticated dev mode.")
        return True
    return key in _VALID_KEYS


def generate_dev_key() -> str:
    """Generate a random API key suitable for development use."""
    return secrets.token_urlsafe(32)
