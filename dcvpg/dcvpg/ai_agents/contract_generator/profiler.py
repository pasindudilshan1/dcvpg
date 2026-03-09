import pandas as pd
from typing import Dict, Any, List


def profile_dataframe(df: pd.DataFrame, sample_rows: int = 1000) -> List[Dict[str, Any]]:
    """
    Profiles a DataFrame sample and returns field-level statistics
    used by the LLM to generate a data contract.
    """
    sample = df.head(sample_rows) if len(df) > sample_rows else df
    profiles = []

    for col in sample.columns:
        series = sample[col]
        profile: Dict[str, Any] = {
            "field": col,
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_rate": round(float(series.isna().mean()), 4),
            "unique_count": int(series.nunique()),
            "unique_rate": round(float(series.nunique() / max(len(series), 1)), 4),
        }

        if pd.api.types.is_integer_dtype(series):
            profile["inferred_type"] = "integer"
            non_null = series.dropna()
            if not non_null.empty:
                profile["min"] = int(non_null.min())
                profile["max"] = int(non_null.max())

        elif pd.api.types.is_float_dtype(series):
            profile["inferred_type"] = "float"
            non_null = series.dropna()
            if not non_null.empty:
                profile["min"] = float(non_null.min())
                profile["max"] = float(non_null.max())

        elif pd.api.types.is_datetime64_any_dtype(series):
            profile["inferred_type"] = "timestamp"

        elif pd.api.types.is_bool_dtype(series):
            profile["inferred_type"] = "boolean"

        else:
            profile["inferred_type"] = "string"
            non_null = series.dropna().astype(str)
            if not non_null.empty:
                profile["min_length"] = int(non_null.str.len().min())
                profile["max_length"] = int(non_null.str.len().max())

        # Suggest allowed_values for low-cardinality columns
        if 0 < profile["unique_count"] <= 20:
            profile["sample_values"] = series.dropna().unique().tolist()[:20]

        profiles.append(profile)

    return profiles
