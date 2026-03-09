import pandas as pd
from typing import Dict, Any
from sqlalchemy import create_engine
from .base_connector import BaseConnector

class PostgresConnector(BaseConnector):
    """
    Connects to a PostgreSQL database via SQLAlchemy.
    """

    def connect(self, config: Dict[str, Any]) -> None:
        self.host = config.get("host")
        self.port = config.get("port", 5432)
        # accept both 'database' and 'name' for backwards compatibility
        self.database = config.get("database") or config.get("name")
        self.user = config.get("user")
        self.password = config.get("password")

        if not all([self.host, self.database, self.user]):
            raise ValueError("PostgresConnector requires host, database/name, and user in config.")

        conn_string = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        self.engine = create_engine(conn_string)

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        query = f"SELECT * FROM {source} LIMIT {sample_rows}"
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch sample from {source}: {str(e)}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        query = f"SELECT * FROM {source}"
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch batch from {source}: {str(e)}")
