"""
Lightweight file-based persistence for pipeline runs and quarantine events.

Records are stored as newline-delimited JSON (JSONL) under:
    {base_dir}/.dcvpg_data/pipeline_runs.jsonl
    {base_dir}/.dcvpg_data/quarantine_events.jsonl

`base_dir` is the directory that contains dcvpg.config.yaml.  The API
server locates it via the DCVPG_CONFIG_PATH env var; the CLI passes it
explicitly after loading its config.
"""

import os
import json
import datetime
from typing import Any, Dict, List, Optional


class ReportStore:
    def __init__(self, base_dir: str):
        self._dir = os.path.join(base_dir, ".dcvpg_data")
        os.makedirs(self._dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _path(self, filename: str) -> str:
        return os.path.join(self._dir, filename)

    def _append(self, filename: str, record: Dict[str, Any]) -> None:
        with open(self._path(filename), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

    def _read_all(self, filename: str) -> List[Dict[str, Any]]:
        path = self._path(filename)
        if not os.path.exists(path):
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def _rewrite(self, filename: str, records: List[Dict[str, Any]]) -> None:
        with open(self._path(filename), "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, default=str) + "\n")

    # ------------------------------------------------------------------
    # Pipeline runs
    # ------------------------------------------------------------------

    def save_run(self, record: Dict[str, Any]) -> None:
        """Append a pipeline run record (from a ValidationReport)."""
        record.setdefault("run_at", datetime.datetime.utcnow().isoformat())
        self._append("pipeline_runs.jsonl", record)

    def get_runs(self) -> List[Dict[str, Any]]:
        return self._read_all("pipeline_runs.jsonl")

    # ------------------------------------------------------------------
    # Quarantine events
    # ------------------------------------------------------------------

    def save_quarantine(self, event: Dict[str, Any]) -> None:
        """Append a quarantine event record."""
        event.setdefault("quarantined_at", datetime.datetime.utcnow().isoformat())
        event.setdefault("resolved", False)
        self._append("quarantine_events.jsonl", event)

    def get_quarantine_events(
        self,
        pipeline: Optional[str] = None,
        include_resolved: bool = False,
    ) -> List[Dict[str, Any]]:
        events = self._read_all("quarantine_events.jsonl")
        if not include_resolved:
            events = [e for e in events if not e.get("resolved")]
        if pipeline:
            events = [e for e in events if e.get("pipeline_name") == pipeline]
        return events

    def resolve_batch(self, batch_id: str) -> bool:
        """Mark all events for a batch_id as resolved (rewrites the file)."""
        events = self._read_all("quarantine_events.jsonl")
        found = False
        for e in events:
            if e.get("batch_id") == batch_id:
                e["resolved"] = True
                e["resolved_at"] = datetime.datetime.utcnow().isoformat()
                found = True
        if found:
            self._rewrite("quarantine_events.jsonl", events)
        return found
