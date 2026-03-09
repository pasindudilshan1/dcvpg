import streamlit as st
import sys
import os
import pandas as pd
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("👥 Data Ownership")

contracts = fetch_api("contracts")

if not contracts:
    st.info("No contracts registered yet.")
else:
    # Group by owner team
    by_team: dict = defaultdict(list)
    for c in contracts:
        team = c.get("owner_team", "unknown")
        by_team[team].append(c)

    st.metric("Teams", len(by_team))

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("### By Team")
        for team, team_contracts in sorted(by_team.items()):
            st.write(f"**{team}** — {len(team_contracts)} contract(s)")

    with col2:
        st.markdown("### Contract Owners")
        rows = [
            {
                "Contract": c.get("name"),
                "Version": c.get("version"),
                "Owner Team": c.get("owner_team"),
                "Source Owner": c.get("source_owner"),
                "Connection": c.get("source_connection"),
            }
            for c in contracts
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.markdown("---")
    st.markdown("### Team Detail")
    selected_team = st.selectbox("Select team", sorted(by_team.keys()))
    if selected_team:
        for c in by_team[selected_team]:
            with st.expander(f"📄 {c.get('name')} v{c.get('version')}"):
                st.write(f"**Source connection:** {c.get('source_connection')}")
                st.write(f"**Source owner:** {c.get('source_owner')}")
                st.write(f"**Description:** {c.get('description', '—')}")
                if c.get("pipeline_tags"):
                    st.write(f"**Tags:** {', '.join(c['pipeline_tags'])}")
