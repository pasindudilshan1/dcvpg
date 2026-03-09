from typing import Dict, Any, List


def compute_schema_diff(
    contract_schema: List[Dict[str, Any]],
    live_schema: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compares the contract schema vs the live source schema.
    Both inputs are lists of dicts with at least a 'field' key and a 'type' key.

    Returns a structured diff:
      - added_fields:   fields present in live but not in contract
      - removed_fields: fields present in contract but not in live
      - type_changed:   fields present in both but whose type differs
      - has_drift:      True if any difference was found
    """
    contract_fields = {f["field"]: f for f in contract_schema}
    live_fields = {f["field"]: f for f in live_schema}

    contract_keys = set(contract_fields.keys())
    live_keys = set(live_fields.keys())

    added = sorted(live_keys - contract_keys)
    removed = sorted(contract_keys - live_keys)

    type_changed: Dict[str, Dict[str, Any]] = {}
    for field in contract_keys & live_keys:
        c_type = contract_fields[field].get("type")
        l_type = live_fields[field].get("type")
        if c_type and l_type and c_type != l_type:
            type_changed[field] = {"contract_type": c_type, "live_type": l_type}

    return {
        "has_drift": bool(added or removed or type_changed),
        "added_fields": added,
        "removed_fields": removed,
        "type_changed": type_changed,
    }


def infer_schema_from_dataframe(df) -> List[Dict[str, Any]]:
    """
    Infer a minimal schema list from a pandas DataFrame.
    Used by schema_differ to get the live schema from a sampled batch.
    """
    import pandas as pd

    TYPE_MAP = {
        "int64": "integer",
        "int32": "integer",
        "float64": "float",
        "float32": "float",
        "bool": "boolean",
        "object": "string",
        "datetime64[ns]": "timestamp",
        "datetime64[ns, UTC]": "timestamp",
    }
    schema = []
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        inferred = TYPE_MAP.get(dtype_str, "string")
        schema.append({"field": col, "type": inferred})
    return schema
