"""Performance test: validate a 1M-row batch within the SLA."""
import time
import pytest
import numpy as np
import pandas as pd

pytestmark = pytest.mark.perf

# SLA: 1M rows must validate in under 60 seconds
ROWS = 1_000_000
SLA_SECONDS = 60.0


def _make_large_df(rows: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "id": np.arange(1, rows + 1, dtype=np.int64),
        "status": rng.choice(["active", "inactive", "pending"], size=rows),
        "amount": rng.uniform(0.0, 10000.0, size=rows).round(2),
        "email": [f"user{i}@example.com" for i in range(rows)],
        "created_at": pd.date_range("2020-01-01", periods=rows, freq="s"),
    })


@pytest.fixture(scope="module")
def large_df():
    print(f"\nGenerating {ROWS:,} row DataFrame…")
    t0 = time.perf_counter()
    df = _make_large_df(ROWS)
    elapsed = time.perf_counter() - t0
    print(f"  DataFrame generated in {elapsed:.2f}s")
    return df


@pytest.fixture(scope="module")
def perf_contract():
    from dcvpg.engine.models import ContractSpec, FieldSpec
    return ContractSpec(
        name="perf_test",
        version="1.0",
        owner_team="perf-team",
        source_owner="perf-owner",
        source_connection="pg",
        row_count_min=500_000,
        row_count_max=2_000_000,
        **{
            "schema": [
                FieldSpec(field="id", type="integer", nullable=False),
                FieldSpec(field="status", type="string", nullable=False,
                          allowed_values=["active", "inactive", "pending"]),
                FieldSpec(field="amount", type="float", nullable=False, min=0.0, max=10000.0),
                FieldSpec(field="email", type="string", nullable=False),
                FieldSpec(field="created_at", type="timestamp", nullable=False),
            ]
        },
    )


def test_validate_1m_rows_within_sla(large_df, perf_contract):
    from dcvpg.engine.validator import Validator

    validator = Validator(perf_contract)
    t0 = time.perf_counter()
    report = validator.validate_batch(large_df, pipeline_name="perf_pipeline")
    elapsed = time.perf_counter() - t0

    print(f"\n  Validation of {ROWS:,} rows: {elapsed:.2f}s")
    print(f"  Status: {report.status}, Violations: {report.violations_count}")

    assert elapsed < SLA_SECONDS, (
        f"Validation took {elapsed:.2f}s — exceeds SLA of {SLA_SECONDS}s"
    )
    assert report.rows_processed == ROWS
