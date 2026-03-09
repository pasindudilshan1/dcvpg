import json
import logging
import datetime
from typing import Dict, Any, List, Optional
from .models import ValidationReport, QuarantineEvent

# We would import our Postgres connection pool here, but we will mock it for now
logger = logging.getLogger(__name__)

class QuarantineEngine:
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._store: List[Dict[str, Any]] = []
        # self.conn = connect_to_postgres(self.db_config)
    
    def isolate_batch(self, report: ValidationReport, batch_id: str):
        """
        Takes a failed ValidationReport and writes the metadata to the quarantine_events table.
        It does NOT move the data itself (data movement is handled by the data lake / S3 connector
        or simply aborted in memory), but it creates the central record of the quarantined batch.
        """
        if report.status == "PASSED":
            return
            
        events_to_insert = []
        for details in report.violation_details:
            event = QuarantineEvent(
                pipeline_name=report.pipeline_name,
                contract_name=report.contract_name,
                contract_version=report.contract_version,
                batch_id=str(batch_id),
                violation_type=details.violation_type or "UNKNOWN",
                affected_field=details.field or "UNKNOWN",
                expected_value=details.expected_value,
                actual_sample=json.dumps(details.sample_values) if details.sample_values else None,
                rows_affected=details.rows_affected or 0,
                total_rows=report.rows_processed
            )
            events_to_insert.append(event)
            
        self._write_to_db(events_to_insert)
        
        logger.error(
            f"QUARANTINE: {report.pipeline_name} ({report.contract_name} v{report.contract_version}) "
            f"isolated. Validated {report.rows_processed} rows, {report.violations_count} violations."
        )
        
    def _write_to_db(self, events: List[QuarantineEvent]):
        for ev in events:
            logger.info(f"Writing quarantine event to DB: {ev.violation_type} on {ev.affected_field}")
            self._store.append({
                "pipeline_name": ev.pipeline_name,
                "contract_name": ev.contract_name,
                "contract_version": ev.contract_version,
                "batch_id": ev.batch_id,
                "violation_type": ev.violation_type,
                "affected_field": ev.affected_field,
                "expected_value": ev.expected_value,
                "actual_sample": ev.actual_sample,
                "rows_affected": ev.rows_affected,
                "total_rows": ev.total_rows,
                "resolved_at": None,
            })

    def get_quarantined_batches(self, pipeline_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return stored quarantine events, optionally filtered by pipeline name."""
        events = self._store
        if pipeline_name:
            events = [e for e in events if e.get("pipeline_name") == pipeline_name]
        return events

    def resolve_batch(self, batch_id: str):
        """Mark all quarantine events for a batch as resolved."""
        resolved_time = datetime.datetime.utcnow().isoformat()
        for event in self._store:
            if event.get("batch_id") == batch_id:
                event["resolved_at"] = resolved_time
        logger.info(f"Resolved quarantine batch {batch_id} at {resolved_time}")
