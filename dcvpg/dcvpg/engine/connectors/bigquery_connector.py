import pandas as pd
from typing import Dict, Any
from .base_connector import BaseConnector


class BigQueryConnector(BaseConnector):
    """
    Connects to Google BigQuery.
    Requires google-cloud-bigquery + pandas-gbq: pip install google-cloud-bigquery pandas-gbq
    """

    def connect(self, config: Dict[str, Any]) -> None:
        self.project = config.get("project")
        self.dataset = config.get("dataset")
        self.credentials_env = config.get("credentials_env", "GOOGLE_APPLICATION_CREDENTIALS")

        if not self.project:
            raise ValueError("BigQueryConnector requires 'project' in config.")

    def fetch_sample(self, source: str, sample_rows: int = 1000) -> pd.DataFrame:
        try:
            import pandas_gbq

            table = f"{self.project}.{self.dataset}.{source}" if self.dataset else source
            query = f"SELECT * FROM `{table}` LIMIT {sample_rows}"
            return pandas_gbq.read_gbq(query, project_id=self.project)
        except ImportError:
            raise ImportError("pandas-gbq is required. Install it with: pip install pandas-gbq")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch sample from {source}: {e}")

    def fetch_batch(self, source: str, batch_id: str) -> pd.DataFrame:
        try:
            import pandas_gbq

            table = f"{self.project}.{self.dataset}.{source}" if self.dataset else source
            return pandas_gbq.read_gbq(f"SELECT * FROM `{table}`", project_id=self.project)
        except ImportError:
            raise ImportError("pandas-gbq is required. Install it with: pip install pandas-gbq")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch batch from {source}: {e}")
