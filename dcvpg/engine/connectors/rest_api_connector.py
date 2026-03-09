import pandas as pd
import httpx
from typing import Dict, Any, Optional
from .base_connector import BaseConnector


class RestApiConnector(BaseConnector):
    """
    Generic REST API connector.
    Fetches JSON data from any HTTP endpoint and normalises it into a DataFrame.
    """

    AUTH_TYPES = ("bearer", "api_key", "basic", "none")

    def connect(self, config: Dict[str, Any]) -> None:
        self.base_url = config.get("base_url", "").rstrip("/")
        self.auth_type = config.get("auth_type", "none").lower()
        self.timeout = config.get("timeout_seconds", 30)

        # Resolve auth credentials
        import os

        self.headers: Dict[str, str] = {"Accept": "application/json"}

        if self.auth_type == "bearer":
            token_env = config.get("token_env", "")
            token = os.environ.get(token_env, "") if token_env else config.get("token", "")
            if token:
                self.headers["Authorization"] = f"Bearer {token}"

        elif self.auth_type == "api_key":
            key_env = config.get("api_key_env", "")
            key = os.environ.get(key_env, "") if key_env else config.get("api_key", "")
            header_name = config.get("api_key_header", "X-API-Key")
            if key:
                self.headers[header_name] = key

        elif self.auth_type == "basic":
            import base64

            user = config.get("username", "")
            pwd = config.get("password", "")
            encoded = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            self.headers["Authorization"] = f"Basic {encoded}"

        if not self.base_url:
            raise ValueError("RestApiConnector requires 'base_url' in config.")

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=self.headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        """Normalise JSON response (list or dict with 'data' key) into DataFrame."""
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            # Try common envelope keys
            for key in ("data", "results", "items", "records"):
                if key in data and isinstance(data[key], list):
                    return pd.DataFrame(data[key])
            # Fallback: single record
            return pd.DataFrame([data])
        raise ValueError(f"Cannot convert API response of type {type(data)} to DataFrame")

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        data = self._get(source, params={"limit": sample_rows, "per_page": sample_rows})
        return self._to_dataframe(data).head(sample_rows)

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        data = self._get(source)
        return self._to_dataframe(data)
