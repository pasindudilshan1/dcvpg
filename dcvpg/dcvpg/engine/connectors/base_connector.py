from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseConnector(ABC):
    """
    Abstract base class for all connectors in DCVPG.
    Users extend this to write custom connectors.
    """

    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> None:
        """
        Initializes the connection using parameters provided in dcvpg.config.yaml.
        """
        pass

    @abstractmethod
    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        """
        Fetches a small sample of data from the source, useful for AI profiling and generation.
        """
        pass

    @abstractmethod
    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        """
        Fetches an entire batch of data based on a batch ID, watermark, or partition.
        """
        pass
