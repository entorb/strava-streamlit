"""Helper: Login to Strava via OAuth2."""

from time import time

import streamlit as st

from helper_api import api_post_deauthorize, api_post_oauth, api_post_token_refresh
from helper_logging import init_logger

logger = init_logger(__file__)


def display_strava_auth_link() -> None:
    """Display link for Strava auth."""
    st.title("Login")
    st.write(
        "<a target='_self' href='http://www.strava.com/oauth/authorize?client_id=28009&response_type=code&redirect_uri=https://entorb.net/strava-streamlit/?exchange_token&approval_prompt=force&scope=activity:read_all'>Login</a>",
        unsafe_allow_html=True,
    )


def handle_redirect() -> None:
    """
    Handle redirect from Strava after auth.

    Calls oauth API.
    Stores in st.session_state: TOKEN, TOKEN_EXPIRE, USER_ID, USERNAME
    """
    code = st.query_params["code"]
    d = api_post_oauth(code)
    # st.write(d)
    st.session_state["TOKEN"] = d["access_token"]
    st.session_state["TOKEN_EXPIRE"] = d["expires_at"]
    st.session_state["TOKEN_REFRESH"] = d["refresh_token"]
    st.session_state["USER_ID"] = d["athlete"]["id"]
    st.session_state["USERNAME"] = d["athlete"].get("username", "no username")

    # remove url parameters
    st.query_params.clear()


def handle_token_refresh(d: dict) -> None:
    """Store refresh token response to session_state."""
    st.session_state["TOKEN"] = d["access_token"]
    st.session_state["TOKEN_EXPIRE"] = d["expires_at"]
    st.session_state["TOKEN_REFRESH"] = d["refresh_token"]


def token_refresh_if_needed() -> None:
    """Trigger token refresh if needed."""
    if time() > st.session_state["TOKEN_EXPIRE"] - 120:
        st.header("Token Refresh")
        d = api_post_token_refresh()
        handle_token_refresh(d)
        # st.write(d)


def perform_login() -> None:
    """Perform the login."""
    if "code" not in st.query_params:
        display_strava_auth_link()
    else:
        handle_redirect()


def logout() -> None:
    """Logout and unset all local access data."""
    api_post_deauthorize()
    for key in ("TOKEN", "USER_ID", "USERNAME", "ENV"):
        if key in st.session_state:
            del st.session_state[key]

    st.write("Logged Out")
