import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("🔒 Quarantine Manager")

quarantine_data = fetch_api("quarantine")

if not quarantine_data:
    st.info("No quarantined batches.")
else:
    batches = quarantine_data if isinstance(quarantine_data, list) else quarantine_data.get("batches", [])

    if not batches:
        st.success("✅ Quarantine is empty — no held batches.")
    else:
        st.metric("Quarantined Batches", len(batches))

        rows = [
            {
                "Batch ID": b.get("batch_id", ""),
                "Pipeline": b.get("pipeline_name", ""),
                "Contract": b.get("contract_name", ""),
                "Rows Affected": b.get("rows_affected", 0),
                "Violation Type": b.get("violation_type", ""),
                "Quarantined At": b.get("quarantined_at", ""),
            }
            for b in batches
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, width='stretch')

        st.markdown("### Actions")
        selected_batch = st.selectbox(
            "Select batch to replay",
            options=[b.get("batch_id") for b in batches],
        )
        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Replay Batch"):
                result = fetch_api(
                    f"quarantine/{selected_batch}/resolve",
                    method="PATCH",
                    data={"replay": True},
                )
                if result:
                    st.success(f"Replay triggered for {selected_batch}")
                else:
                    st.error("Replay failed — check API logs.")

        with col2:
            if st.button("🗑️ Discard Batch"):
                result = fetch_api(
                    f"quarantine/{selected_batch}/resolve",
                    method="PATCH",
                    data={"discard": True},
                )
                if result:
                    st.warning(f"Batch {selected_batch} discarded.")
