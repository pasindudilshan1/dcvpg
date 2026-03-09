import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector


class SnowflakeConnector(BaseConnector):
    """
    Connects to Snowflake.
    Requires snowflake-sqlalchemy: pip install snowflake-sqlalchemy
    """

    def connect(self, config: Dict[str, Any]) -> None:
        self.account = config.get("account")
        self.warehouse = config.get("warehouse")
        self.database = config.get("database")
        self.schema = config.get("schema", "PUBLIC")
        self.user = config.get("user")
        self.password = config.get("password", "")

        if not all([self.account, self.database, self.user]):
            raise ValueError("SnowflakeConnector requires account, database, and user.")

        self._conn_string = (
            f"snowflake://{self.user}:{self.password}"
            f"@{self.account}/{self.database}/{self.schema}"
            f"?warehouse={self.warehouse}"
        )

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        try:
            return pd.read_sql(f"SELECT * FROM {source} LIMIT {sample_rows}", self._conn_string)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch sample from {source}: {e}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        try:
            return pd.read_sql(f"SELECT * FROM {source}", self._conn_string)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch batch from {source}: {e}")
