import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("🚨 Violations")

pipelines = fetch_api("pipelines")

if not pipelines:
    st.info("No pipeline data available.")
else:
    failing = [p for p in pipelines if p.get("status") == "FAILED"]
    passing = [p for p in pipelines if p.get("status") != "FAILED"]

    col1, col2 = st.columns(2)
    col1.metric("❌ Failing Pipelines", len(failing))
    col2.metric("✅ Passing Pipelines", len(passing))

    if failing:
        st.markdown("### Active Violations")
        rows = []
        for p in failing:
            for v in p.get("violation_details", []):
                rows.append({
                    "Pipeline": p.get("pipeline_name"),
                    "Contract": p.get("contract_name"),
                    "Field": v.get("field"),
                    "Type": v.get("violation_type"),
                    "Rows Affected": v.get("rows_affected"),
                    "Expected": v.get("expected_value"),
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), width='stretch')
        else:
            for p in failing:
                st.warning(
                    f"**{p.get('pipeline_name')}** — {p.get('violations_count', 0)} violation(s) "
                    f"on {p.get('rows_processed', 0)} rows"
                )
    else:
        st.success("All pipelines are healthy 🎉")
