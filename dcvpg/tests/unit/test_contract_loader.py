"""Unit tests for ContractRegistry / contract_loader."""
import os
import textwrap
import pytest


CONTRACT_YAML = textwrap.dedent("""\
    contract:
      name: test_contract
      version: "1.0"
      owner_team: data-eng
      source_owner: backend-team
      source_connection: postgres_main
      source_table: orders
      description: Unit test contract
      schema:
        - field: id
          type: integer
          nullable: false
          unique: true
        - field: status
          type: string
          nullable: false
          allowed_values: ["active", "inactive", "pending"]
        - field: amount
          type: float
          nullable: true
          min: 0.0
          max: 100000.0
""")


@pytest.fixture
def contract_dir(tmp_path):
    subdir = tmp_path / "contracts"
    subdir.mkdir()
    contract_file = subdir / "test_contract.yaml"
    contract_file.write_text(CONTRACT_YAML)
    return str(subdir)


def test_load_contract(contract_dir):
    from dcvpg.engine.contract_loader import load_contract
    c = load_contract(os.path.join(contract_dir, "test_contract.yaml"))
    assert c.name == "test_contract"
    assert c.version == "1.0"
    assert c.owner_team == "data-eng"
    assert c.source_table == "orders"
    assert len(c.schema_fields) == 3


def test_load_contract_schema_fields(contract_dir):
    from dcvpg.engine.contract_loader import load_contract
    c = load_contract(os.path.join(contract_dir, "test_contract.yaml"))
    id_field = next(f for f in c.schema_fields if f.field == "id")
    assert id_field.type == "integer"
    assert id_field.nullable is False
    assert id_field.unique is True

    status_field = next(f for f in c.schema_fields if f.field == "status")
    assert "active" in status_field.allowed_values

    amount_field = next(f for f in c.schema_fields if f.field == "amount")
    assert amount_field.min == 0.0
    assert amount_field.max == 100000.0


def test_registry_list(contract_dir):
    from dcvpg.engine.registry import ContractRegistry
    registry = ContractRegistry(contract_dir)
    contracts = registry.list_contracts()
    assert len(contracts) == 1
    assert contracts[0].name == "test_contract"


def test_registry_get(contract_dir):
    from dcvpg.engine.registry import ContractRegistry
    registry = ContractRegistry(contract_dir)
    c = registry.get_contract("test_contract")
    assert c is not None
    assert c.name == "test_contract"


def test_registry_get_missing(contract_dir):
    from dcvpg.engine.registry import ContractRegistry
    registry = ContractRegistry(contract_dir)
    with pytest.raises(Exception):
        registry.get_contract("nonexistent_contract")


def test_load_contract_missing_file():
    from dcvpg.engine.contract_loader import load_contract
    with pytest.raises((FileNotFoundError, Exception)):
        load_contract("/tmp/does_not_exist_xyz.yaml")
