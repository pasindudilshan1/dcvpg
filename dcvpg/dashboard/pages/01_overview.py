import streamlit as st
import sys
import os
# Hack to allow import from parent folder in Streamlit pages
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import fetch_api

st.title("📊 Overview")

pipelines = fetch_api("pipelines")
reports = fetch_api("reports/incidents")

if pipelines and reports:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Monitored Pipelines", len(pipelines))
        
    with col2:
        failures = len([p for p in pipelines if p.get("status") == "FAILED"])
        st.metric("Active Violations", failures, delta=f"{failures}", delta_color="inverse")
        
    with col3:
        st.metric("Total Incidents (30d)", reports.get("incident_count", 0))
        
    with col4:
        st.metric("MTTR", f"{reports.get('mean_time_to_resolve_minutes', 0)} mins")
        
    st.markdown("### Pipeline Status")
    for pipeline in pipelines:
        st.write(f"**{pipeline['pipeline_name']}** - Status: {pipeline['status']} ({pipeline['violations_count']} violations)")
