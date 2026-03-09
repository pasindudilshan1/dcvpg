import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector


class MySQLConnector(BaseConnector):
    """
    Connects to a MySQL / MariaDB database.
    Requires sqlalchemy + pymysql: pip install sqlalchemy pymysql
    """

    def connect(self, config: Dict[str, Any]) -> None:
        self.host = config.get("host")
        self.port = config.get("port", 3306)
        self.database = config.get("database")
        self.user = config.get("user")
        self.password = config.get("password", "")

        if not all([self.host, self.database, self.user]):
            raise ValueError("MySQLConnector requires host, database, and user in config.")

        self._conn_string = (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
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
