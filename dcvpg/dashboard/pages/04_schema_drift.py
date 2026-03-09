import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("🔍 Schema Drift")

drift_report = fetch_api("reports/drift")

if not drift_report:
    st.info("No schema drift data available.")
elif not drift_report.get("drifts"):
    st.success("✅ No schema drift detected across all contracts.")
else:
    drifts = drift_report["drifts"]
    st.metric("Contracts with drift", len(drifts))
    st.warning(f"{len(drifts)} contract(s) have schema drift vs their live sources.")

    for d in drifts:
        with st.expander(f"⚠️ {d.get('contract_name')} — {d.get('source')}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Added Fields", len(d.get("added_fields", [])))
            col2.metric("Removed Fields", len(d.get("removed_fields", [])))
            col3.metric("Type Changes", len(d.get("type_changed", {})))

            if d.get("added_fields"):
                st.markdown("**➕ New fields in source (not in contract):**")
                for f in d["added_fields"]:
                    st.code(f"+ {f}", language="diff")

            if d.get("removed_fields"):
                st.markdown("**➖ Fields removed from source (still in contract):**")
                for f in d["removed_fields"]:
                    st.code(f"- {f}", language="diff")

            if d.get("type_changed"):
                st.markdown("**🔄 Type changes:**")
                for field, change in d["type_changed"].items():
                    st.code(
                        f"~ {field}: {change.get('contract_type')} → {change.get('live_type')}",
                        language="diff",
                    )

            if st.button(f"🤖 Open Fix PR", key=f"pr_{d.get('contract_name')}"):
                result = fetch_api(
                    f"contracts/{d.get('contract_name')}/fix",
                    method="POST",
                    data={"auto_heal": True},
                )
                if result:
                    st.success(f"PR created: {result.get('pr_url', 'N/A')}")
