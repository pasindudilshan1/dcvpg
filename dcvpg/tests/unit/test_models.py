import pytest
from dcvpg.engine.models import ContractSpec, FieldSpec

def test_contract_spec_valid():
    spec = ContractSpec(
        name="test_contract",
        version="1.0",
        owner_team="team_a",
        source_owner="team_b",
        source_connection="source_a",
        schema=[FieldSpec(field="id", type="string", nullable=False, unique=True)]
    )
    assert spec.name == "test_contract"
    assert spec.schema_fields[0].field == "id"

def test_contract_spec_invalid_missing_fields():
    with pytest.raises(ValueError):
        ContractSpec(
            name="test_contract",
            version="1.0"
            # Missing required fields like owner_team, etc.
        )
