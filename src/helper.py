"""General helper functions."""

from pathlib import Path

import streamlit as st


@st.cache_data()
def get_env() -> str:
    """Get ENV to PROD (=entorb.net) / DEV (=local)."""
    if Path("/home/entorb/strava-streamlit").is_dir():
        return "PROD"
    # when running locally, ensure we have data dirs
    Path("./cache").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
    return "DEV"
