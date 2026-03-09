import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector


class GCSConnector(BaseConnector):
    """
    Reads CSV, JSON, or Parquet files from Google Cloud Storage.
    Requires gcsfs: pip install gcsfs
    """

    def connect(self, config: Dict[str, Any]) -> None:
        import os

        self.bucket = config.get("bucket") or os.environ.get(
            config.get("bucket_env", ""), ""
        )
        self.project = config.get("project")
        self.file_type = config.get("file_type", "csv").lower()
        self.credentials_env = config.get("credentials_env", "GOOGLE_APPLICATION_CREDENTIALS")

        if not self.bucket:
            raise ValueError("GCSConnector requires 'bucket' in config.")

    def _gcs_path(self, key: str) -> str:
        return f"gcs://{self.bucket}/{key}"

    def _read(self, key: str, nrows: int = None) -> pd.DataFrame:
        path = self._gcs_path(key)
        if self.file_type == "csv":
            return pd.read_csv(path, nrows=nrows)
        elif self.file_type == "json":
            df = pd.read_json(path, lines=True)
            return df.head(nrows) if nrows else df
        elif self.file_type == "parquet":
            df = pd.read_parquet(path)
            return df.head(nrows) if nrows else df
        else:
            raise ValueError(f"Unsupported file_type: {self.file_type}")

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        try:
            return self._read(source, nrows=sample_rows)
        except Exception as e:
            raise RuntimeError(f"GCS sample fetch failed for gs://{self.bucket}/{source}: {e}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        try:
            return self._read(source)
        except Exception as e:
            raise RuntimeError(f"GCS batch fetch failed for gs://{self.bucket}/{source}: {e}")
