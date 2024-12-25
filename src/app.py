"""Main file."""

from pathlib import Path
from time import time

import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    get_known_locations,
)
from helper_logging import init_logger
from helper_login import (
    logout,
    perform_login,
    token_refresh_if_needed,
)


def set_env() -> None:
    """Set ENV to entorb.net / local."""
    if "ENV" not in st.session_state:
        if Path("/home/entorb/strava-streamlit").is_dir():
            st.session_state["ENV"] = "PROD"
        else:
            st.session_state["ENV"] = "DEV"
            # when running locally, ensure we have data dirs
            Path("./cache").mkdir(exist_ok=True)
            Path("./data").mkdir(exist_ok=True)


title = "Strava Äpp V2"
st.set_page_config(page_title=title, page_icon=None, layout="wide")
st.title(title)

logger = init_logger(__file__)
logger.info("Start")

set_env()


# for local development I skip the login
if st.session_state["ENV"] == "DEV":
    st.session_state["TOKEN"] = st.secrets["my_token"]
    st.session_state["TOKEN_EXPIRE"] = int(time() + 24 * 3600)
    st.session_state["TOKEN_REFRESH"] = st.secrets["my_refresh_token"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    st.session_state["USERNAME"] = st.secrets["my_username"]

if "TOKEN" not in st.session_state:
    perform_login()


if "TOKEN" in st.session_state:
    # check if we need to refresh the token
    token_refresh_if_needed()

    username = st.session_state["USERNAME"]
    st.write(f"Welcome User '{username}'")

    df, df_gear = cache_all_activities_and_gears()
    st.header("Activities")
    st.write(df)

    st.header("Gear")
    st.write(df_gear)

    st.header("Your known locations")
    kl = get_known_locations()
    df = pd.DataFrame(kl, columns=("Lat", "Lng", "Name"))
    df = df[["Name", "Lat", "Lng"]].sort_values("Name")
    st.dataframe(df, hide_index=True)

    # some more debug output only to me
    if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
        st.header("Session State")
        st.write(st.session_state)

    st.button("Logout", on_click=logout)

logger.info("End")

print("test")
