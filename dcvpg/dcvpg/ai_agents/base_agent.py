import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all DCVPG AI agents.
    Sets up the Anthropic client lazily and provides a shared call_llm() helper.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-6"):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required for AI features. "
                    "Install with: pip install dcvpg[ai]"
                )
            if not self.api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not set. "
                    "Set the environment variable or pass api_key= to the agent."
                )
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def call_llm(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        """Send a prompt to Claude and return the text response."""
        messages = [{"role": "user", "content": prompt}]
        kwargs: dict = {"model": self.model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text
