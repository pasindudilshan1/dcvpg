import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_PATH = ".dcvpg/baselines"


class BaselineStore:
    """
    Persists rolling statistical baselines for anomaly detection.
    Stores JSON snapshots per contract/field in a local directory.
    """

    def __init__(self, store_path: str = _DEFAULT_PATH):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)

    def _key_path(self, contract_name: str, field: str) -> Path:
        safe_field = field.replace("/", "_").replace(".", "_")
        return self.store_path / f"{contract_name}__{safe_field}.json"

    def save(self, contract_name: str, field: str, stats: Dict[str, Any]) -> None:
        path = self._key_path(contract_name, field)
        with open(path, "w") as f:
            json.dump(stats, f, indent=2)

    def load(self, contract_name: str, field: str) -> Optional[Dict[str, Any]]:
        path = self._key_path(contract_name, field)
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def delete(self, contract_name: str, field: str) -> None:
        path = self._key_path(contract_name, field)
        if path.exists():
            path.unlink()

    def list_baselines(self, contract_name: Optional[str] = None) -> list:
        pattern = f"{contract_name}__*.json" if contract_name else "*.json"
        return [p.stem for p in self.store_path.glob(pattern)]
