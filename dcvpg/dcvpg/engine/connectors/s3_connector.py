import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector


class S3Connector(BaseConnector):
    """
    Reads CSV, JSON, or Parquet files from Amazon S3.
    Requires boto3 and s3fs: pip install boto3 s3fs
    """

    def connect(self, config: Dict[str, Any]) -> None:
        import os

        self.bucket = config.get("bucket") or os.environ.get(
            config.get("bucket_env", ""), ""
        )
        self.region = config.get("region", "us-east-1")
        self.file_type = config.get("file_type", "csv").lower()

        access_key_env = config.get("access_key_env", "AWS_ACCESS_KEY_ID")
        secret_key_env = config.get("secret_key_env", "AWS_SECRET_ACCESS_KEY")

        import boto3

        self._s3 = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=os.environ.get(access_key_env),
            aws_secret_access_key=os.environ.get(secret_key_env),
        )

        if not self.bucket:
            raise ValueError("S3Connector requires 'bucket' in config.")

    def _read(self, key: str, nrows: int = None) -> pd.DataFrame:
        s3_path = f"s3://{self.bucket}/{key}"
        if self.file_type == "csv":
            return pd.read_csv(s3_path, nrows=nrows)
        elif self.file_type == "json":
            df = pd.read_json(s3_path, lines=True)
            return df.head(nrows) if nrows else df
        elif self.file_type == "parquet":
            df = pd.read_parquet(s3_path)
            return df.head(nrows) if nrows else df
        else:
            raise ValueError(f"Unsupported file_type: {self.file_type}")

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        try:
            return self._read(source, nrows=sample_rows)
        except Exception as e:
            raise RuntimeError(f"S3 sample fetch failed for s3://{self.bucket}/{source}: {e}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        try:
            return self._read(source)
        except Exception as e:
            raise RuntimeError(f"S3 batch fetch failed for s3://{self.bucket}/{source}: {e}")
