from typing import Dict, Any, List

from dcvpg.engine.models import ContractSpec
from dcvpg.engine.reporting.schema_diff import compute_schema_diff


def diff_contract_vs_live(
    contract: ContractSpec, live_schema: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compares a loaded ContractSpec against the live schema dicts fetched from a data source.
    Returns a structured diff with added, removed, and type-changed fields.
    """
    contract_schema = [
        {"field": f.field, "type": f.type, "nullable": f.nullable}
        for f in contract.schema_fields
    ]
    return compute_schema_diff(contract_schema, live_schema)
