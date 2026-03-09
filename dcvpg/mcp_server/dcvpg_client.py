import os
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class DCVPGClient:
    """Async HTTP client wrapping the DCVPG REST API for use by the MCP Server."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.api_url = (api_url or os.environ.get("DCVPG_API_URL", "http://localhost:8000/api/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("DCVPG_API_KEY", "")
        self.timeout = timeout

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url, headers=self._headers, params=params or {})
            resp.raise_for_status()
            return resp.json()

    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=self._headers, json=data or {})
            resp.raise_for_status()
            return resp.json()

    async def patch(self, endpoint: str, data: Optional[Dict] = None) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.patch(url, headers=self._headers, json=data or {})
            resp.raise_for_status()
            return resp.json()

    async def delete(self, endpoint: str) -> Any:
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.delete(url, headers=self._headers)
            resp.raise_for_status()
            return resp.json()
