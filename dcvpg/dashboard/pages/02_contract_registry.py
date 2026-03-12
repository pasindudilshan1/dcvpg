import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("📋 Contract Registry")

contracts = fetch_api("contracts")

if not contracts:
    st.info("No contracts registered yet. Run `dcvpg register <contract.yaml>` to add one.")
else:
    st.metric("Total Contracts", len(contracts))

    search = st.text_input("🔍 Search contracts", placeholder="Filter by name, owner, or tag…")

    filtered = contracts
    if search:
        filtered = [
            c for c in contracts
            if search.lower() in c.get("name", "").lower()
            or search.lower() in c.get("owner_team", "").lower()
        ]

    for c in filtered:
        with st.expander(f"📄 {c.get('name')} v{c.get('version')} — {c.get('owner_team')}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Source connection:** {c.get('source_connection')}")
                st.write(f"**Source table:** {c.get('source_table', '—')}")
                st.write(f"**Description:** {c.get('description', '—')}")
            with col2:
                st.write(f"**Owner team:** {c.get('owner_team')}")
                st.write(f"**Source owner:** {c.get('source_owner')}")
                st.write(f"**Fields:** {len(c.get('schema', []))}")

            if c.get("schema"):
                st.markdown("**Schema fields:**")
                import pandas as pd
                df = pd.DataFrame(c["schema"])
                # Serialize any list/dict columns to strings so PyArrow can convert the
                # DataFrame without type-inference conflicts (e.g. mixed-type allowed_values)
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
                        df[col] = df[col].apply(lambda x: ", ".join(str(v) for v in x) if isinstance(x, list) else (str(x) if isinstance(x, dict) else x))
                st.dataframe(df, width='stretch')
