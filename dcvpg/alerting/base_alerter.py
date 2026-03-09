from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAlerter(ABC):
    """
    Abstract base class for routing alerts to external systems natively or completely bespoke.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the alerter with the config provided in dcvpg.config.yaml
        """
        self.config = config

    @abstractmethod
    def send_alert(self, severity: str, message: str, metadata: Dict[str, Any]) -> bool:
        """
        Send the alert out to the appropriate destination.
        Returns a boolean indicating success.

        Args:
            severity (str): E.g., WARNING, CRITICAL
            message (str): Human-readable formatted alert message
            metadata (Dict[str, Any]): Full context, including pipeline_name, contract_name, rows_affected, etc.
        """
        pass
