import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector

class FileConnector(BaseConnector):
    """
    Connects to local or network-mounted files (CSV, JSON, Parquet).
    """

    def connect(self, config: Dict[str, Any]) -> None:
        self.file_path = config.get("path")  # optional; source arg used as path when absent
        self.file_type = config.get("file_type", "csv").lower()

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        """
        Samples a specific file or set of files.
        For simplicity in this framework demo, we read the top N rows of a defined file.
        """
        if self.file_path is None:
            path = source
        else:
            path = f"{self.file_path}/{source}" if not self.file_path.endswith(source) else self.file_path
        
        try:
             if self.file_type == "csv":
                 return pd.read_csv(path, nrows=sample_rows)
             elif self.file_type == "json":
                 # JSON doesn't support nrows natively, read all and head()
                 df = pd.read_json(path, lines=True)
                 return df.head(sample_rows)
             elif self.file_type == "parquet":
                 # requires pyarrow/fastparquet
                 return pd.read_parquet(path).head(sample_rows)
             else:
                 raise ValueError(f"Unsupported file type: {self.file_type}")
        except FileNotFoundError:
             raise FileNotFoundError(f"Source file not found: {path}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        """
        Reads the whole file as a batch.
        """
        if self.file_path is None:
            path = source
        else:
            path = f"{self.file_path}/{source}" if not self.file_path.endswith(source) else self.file_path
        
        try:
             if self.file_type == "csv":
                 return pd.read_csv(path)
             elif self.file_type == "json":
                 return pd.read_json(path, lines=True)
             elif self.file_type == "parquet":
                 return pd.read_parquet(path)
             else:
                 raise ValueError(f"Unsupported file type: {self.file_type}")
        except FileNotFoundError:
             raise FileNotFoundError(f"Source file not found: {path}")
