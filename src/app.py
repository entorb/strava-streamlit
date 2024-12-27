"""Main file."""

from pathlib import Path
from time import time

import streamlit as st

from helper_logging import get_logger_from_filename
from helper_login import (
    perform_login,
    token_refresh_if_needed,
)
from helper_ui_components import create_navigation_menu

st.set_page_config(page_title="Strava Äpp V2", page_icon=None, layout="wide")
logger = get_logger_from_filename(__file__)
logger.info("Start")

# https://momentjs.com/docs/#/displaying/format/
# FORMAT_DATETIME = "YY-MM-DD HH:mm"


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

    st.logo(
            "src/strava-resources/api_logo_pwrdBy_strava_stack_light.svg",
            size="large"
        )
    create_navigation_menu()

    # username = st.session_state["USERNAME"]
    # st.write(f"Welcome User '{username}'")


logger.info("End")
