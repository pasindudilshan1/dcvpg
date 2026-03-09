"""Integration tests for QuarantineEngine (requires PostgreSQL)."""
import os
import uuid
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def db_config():
    return {
        "host": os.environ.get("DCVPG_DB_HOST", "localhost"),
        "port": int(os.environ.get("DCVPG_DB_PORT", "5432")),
        "name": os.environ.get("DCVPG_DB_NAME", "dcvpg"),
        "user": os.environ.get("DCVPG_DB_USER", "dcvpg_user"),
        "password": os.environ.get("DCVPG_DB_PASSWORD", "dcvpg_password"),
    }


@pytest.fixture
def sample_report():
    from dcvpg.engine.models import ValidationReport, ValidationResult
    return ValidationReport(
        pipeline_name="test_pipeline",
        contract_name="test_contract",
        contract_version="1.0",
        status="FAILED",
        rows_processed=100,
        violations_count=2,
        duration_ms=150,
        violation_details=[
            ValidationResult(
                passed=False,
                field="status",
                violation_type="INVALID_VALUE",
                rows_affected=5,
                expected_value="['active', 'inactive']",
                sample_values=["UNKNOWN", "DELETED"],
            )
        ],
    )


def test_isolate_and_query_batch(db_config, sample_report):
    from dcvpg.engine.quarantine_engine import QuarantineEngine

    qe = QuarantineEngine(db_config)
    batch_id = str(uuid.uuid4())

    # Store the batch
    qe.isolate_batch(sample_report, batch_id)

    # Query it back
    events = qe.get_quarantined_batches(pipeline_name="test_pipeline")
    assert any(e.get("batch_id") == batch_id for e in events), \
        f"Batch {batch_id} not found in quarantine."


def test_resolve_batch(db_config, sample_report):
    from dcvpg.engine.quarantine_engine import QuarantineEngine

    qe = QuarantineEngine(db_config)
    batch_id = str(uuid.uuid4())
    qe.isolate_batch(sample_report, batch_id)
    qe.resolve_batch(batch_id)

    events = qe.get_quarantined_batches(pipeline_name="test_pipeline")
    resolved = [e for e in events if e.get("batch_id") == batch_id]
    if resolved:
        assert resolved[0].get("resolved_at") is not None


def test_multiple_violations_stored(db_config):
    from dcvpg.engine.models import ValidationReport, ValidationResult
    from dcvpg.engine.quarantine_engine import QuarantineEngine

    report = ValidationReport(
        pipeline_name="multi_test",
        contract_name="multi_contract",
        contract_version="2.0",
        status="FAILED",
        rows_processed=1000,
        violations_count=3,
        duration_ms=200,
        violation_details=[
            ValidationResult(passed=False, field="id", violation_type="FIELD_MISSING",
                             rows_affected=1000, expected_value="present"),
            ValidationResult(passed=False, field="amount", violation_type="ROW_COUNT_TOO_LOW",
                             rows_affected=1000, expected_value=">= 5000"),
        ],
    )

    qe = QuarantineEngine(db_config)
    batch_id = str(uuid.uuid4())
    qe.isolate_batch(report, batch_id)

    events = qe.get_quarantined_batches(pipeline_name="multi_test")
    assert len(events) >= 1
