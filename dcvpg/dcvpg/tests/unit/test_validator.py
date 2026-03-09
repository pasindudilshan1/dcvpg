"""Unit tests for the core Validator engine."""
import pytest
import pandas as pd
from dcvpg.engine.models import ContractSpec, FieldSpec, ValidationReport


def make_contract(**kwargs) -> ContractSpec:
    defaults = dict(
        name="test",
        version="1.0",
        owner_team="eng",
        source_owner="team",
        source_connection="pg",
        schema_fields=[],
    )
    defaults.update(kwargs)
    return ContractSpec.model_validate({"contract": defaults} if False else defaults)


def make_field(**kwargs) -> FieldSpec:
    defaults = {"field": "col", "type": "string"}
    defaults.update(kwargs)
    return FieldSpec(**defaults)


@pytest.fixture
def basic_contract():
    return ContractSpec(
        name="orders",
        version="1.0",
        owner_team="eng",
        source_owner="team",
        source_connection="pg",
        **{"schema": [
            FieldSpec(field="id", type="integer", nullable=False, unique=True),
            FieldSpec(field="status", type="string", nullable=False,
                      allowed_values=["active", "inactive"]),
            FieldSpec(field="amount", type="float", nullable=True, min=0.0, max=1000.0),
        ]}
    )


@pytest.fixture
def valid_df():
    return pd.DataFrame({
        "id": [1, 2, 3],
        "status": ["active", "inactive", "active"],
        "amount": [10.5, 200.0, 0.0],
    })


def test_valid_batch_passes(basic_contract, valid_df):
    from dcvpg.engine.validator import Validator
    v = Validator(basic_contract)
    report = v.validate_batch(valid_df, pipeline_name="test_pipeline")
    assert report.status == "PASSED"
    assert report.violations_count == 0
    assert report.rows_processed == 3


def test_null_violation(basic_contract):
    from dcvpg.engine.validator import Validator
    df = pd.DataFrame({
        "id": [1, 2, None],  # id is nullable=False
        "status": ["active", "inactive", "active"],
        "amount": [10.0, 20.0, 30.0],
    })
    v = Validator(basic_contract)
    report = v.validate_batch(df, pipeline_name="test_pipeline")
    assert report.status == "FAILED"
    assert any(r.violation_type in ("NULLABILITY_VIOLATION", "TYPE_MISMATCH") for r in report.violation_details)


def test_allowed_values_violation(basic_contract):
    from dcvpg.engine.validator import Validator
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "status": ["active", "INVALID_VALUE", "inactive"],
        "amount": [10.0, 20.0, 30.0],
    })
    v = Validator(basic_contract)
    report = v.validate_batch(df, pipeline_name="test_pipeline")
    assert report.status == "FAILED"
    assert any(r.violation_type == "ALLOWED_VALUES_VIOLATION" for r in report.violation_details)


def test_range_violation(basic_contract):
    from dcvpg.engine.validator import Validator
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "status": ["active", "inactive", "active"],
        "amount": [10.0, 9999.0, -5.0],  # 9999 > max=1000, -5 < min=0
    })
    v = Validator(basic_contract)
    report = v.validate_batch(df, pipeline_name="test_pipeline")
    assert report.status == "FAILED"


def test_missing_field_violation():
    from dcvpg.engine.validator import Validator
    contract = ContractSpec(
        name="test",
        version="1.0",
        owner_team="eng",
        source_owner="team",
        source_connection="pg",
        **{"schema": [FieldSpec(field="required_col", type="string", nullable=False)]}
    )
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    v = Validator(contract)
    report = v.validate_batch(df, pipeline_name="test")
    assert report.status == "FAILED"
    assert any(r.violation_type == "FIELD_MISSING" for r in report.violation_details)


def test_row_count_min_violation():
    from dcvpg.engine.validator import Validator
    contract = ContractSpec(
        name="test",
        version="1.0",
        owner_team="eng",
        source_owner="team",
        source_connection="pg",
        row_count_min=100,
        **{"schema": [FieldSpec(field="id", type="integer")]}
    )
    df = pd.DataFrame({"id": range(10)})  # only 10 rows, min is 100
    v = Validator(contract)
    report = v.validate_batch(df, pipeline_name="test")
    assert report.status == "FAILED"
    assert any(r.violation_type == "ROW_COUNT_TOO_LOW" for r in report.violation_details)


def test_row_count_max_violation():
    from dcvpg.engine.validator import Validator
    contract = ContractSpec(
        name="test",
        version="1.0",
        owner_team="eng",
        source_owner="team",
        source_connection="pg",
        row_count_max=5,
        **{"schema": [FieldSpec(field="id", type="integer")]}
    )
    df = pd.DataFrame({"id": range(20)})  # 20 rows, max is 5
    v = Validator(contract)
    report = v.validate_batch(df, pipeline_name="test")
    assert report.status == "FAILED"
    assert any(r.violation_type == "ROW_COUNT_TOO_HIGH" for r in report.violation_details)


def test_report_structure(basic_contract, valid_df):
    from dcvpg.engine.validator import Validator
    v = Validator(basic_contract)
    report = v.validate_batch(valid_df, pipeline_name="my_pipeline", duration_ms=42)
    assert isinstance(report, ValidationReport)
    assert report.pipeline_name == "my_pipeline"
    assert report.contract_name == "orders"
    assert report.duration_ms == 42
