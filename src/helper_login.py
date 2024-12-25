"""Helper: Login to Strava via OAuth2."""

import requests
import streamlit as st

from helper_logging import init_logger

logger = init_logger(__file__)


def display_strava_auth_link() -> None:
    """Display link for Strava auth."""
    st.write(
        "<a target='_self' href='http://www.strava.com/oauth/authorize?client_id=28009&response_type=code&redirect_uri=https://entorb.net/strava-streamlit/?exchange_token&approval_prompt=force&scope=activity:read_all'>Login</a>",
        unsafe_allow_html=True,
    )


def handle_redirect() -> None:
    """
    Handle redirect from Strava after auth.

    Sets st.session_state["TOKEN"].
    """
    code = st.query_params["code"]
    url = "https://www.strava.com/oauth/token"
    d = {
        # 'Accept':"application/json",
        # 'Accept-Encoding':'UTF-8',
        "client_id": st.secrets["client_id"],
        "client_secret": st.secrets["secret"],
        "code": code,
    }
    resp = requests.post(url, json=d, timeout=3)
    access_token = resp.json()["access_token"]
    st.session_state["TOKEN"] = access_token

    # remove url parameters
    st.query_params.clear()


def perform_login() -> None:
    """Perform the login."""
    if "code" not in st.query_params:
        display_strava_auth_link()
    else:
        handle_redirect()


def logout() -> None:
    """Logout and unset all local access data."""
    # TODO: Logout at Strava
    for key in ("TOKEN", "USER_ID", "USERNAME", "ENV"):
        if key in st.session_state:
            del st.session_state[key]
    st.write("Logged Out")
