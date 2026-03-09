import streamlit as st
import os
import requests

st.set_page_config(
    page_title="Pipeline Guardian Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Pipeline Guardian - DCVPG")
st.markdown("Monitor your Data Contracts, quarantine violations, and schema drift in real-time.")

# Shared helper to call the FastAPI backend
def fetch_api(endpoint: str, method: str = "GET", data: dict = None):
    api_url = os.environ.get("DCVPG_API_URL", "http://localhost:8000/api/v1").rstrip("/")
    api_key = os.environ.get("DCVPG_API_KEY", "my-secret-key")
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{api_url}/{endpoint.lstrip('/')}"
    try:
        method = method.upper()
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data or {})
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data or {})
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            st.error(f"Unsupported HTTP method: {method}")
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed [{method} {url}]: {e}")
        return None

# Simple homepage
st.markdown("""
### Welcome to DCVPG Dashboard
Use the sidebar to navigate through:
- **Overview:** High-level metrics
- **Contract Registry:** See all active definitions
- **Violations:** Deep dive into failures and quarantine
""")
