"""Helper: Login to Strava via OAuth2."""

# ruff: noqa: E501

from time import time

import streamlit as st

from helper_api import api_post_deauthorize, api_post_oauth, api_post_token_refresh
from helper_logging import (
    get_logger_from_filename,
    get_user_login_count,
    track_function_usage,
)

logger = get_logger_from_filename(__file__)


@track_function_usage
def display_strava_auth_link() -> None:
    """Display link for Strava auth."""
    st.title("Login")

    # this text is copied from README.md
    st.markdown("""This is a modern rewrite of my [old Strava Äpp](https://entorb.net/strava/). Currently, only read-only statistics features are implemented. For bulk modify of activities and Excel import, please use the old Äpp.
""")

    # TODO: how to replace url to old strava app V1 here?
    st.write(
        """
<a target='_self' href='https://www.strava.com/oauth/authorize?client_id=28009&response_type=code&redirect_uri=https://entorb.net/strava-streamlit/?exchange_token&approval_prompt=force&scope=activity:read_all'>
<button class="strava-connect-button">
<img src="/strava/strava-resources/btn_strava_connectwith_light.svg" alt="Connect with Strava">
</button>
</a>
""",
        unsafe_allow_html=True,
    )

    # this text is copied from README.md
    st.markdown(
        """
## Privacy

* **Code:** The [source-code](https://github.com/entorb/strava-streamlit/) is open source.
* **Data:** The app does not use a database. Your Strava data is only temporarily cached.
* **Access:** A temporary access token to your Strava profile is used and revoked at logout.
* **Cookies:** Only a single technical cookie is used for session identification and deleted at end of session. No user tracking.
"""
    )


@track_function_usage
def handle_redirect() -> None:
    """
    Handle redirect from Strava after auth.

    Calls oauth API.
    Stores in st.session_state: TOKEN, TOKEN_EXPIRE, USER_ID, USERNAME
    """
    code = st.query_params["code"]
    d = api_post_oauth(code)
    # st.write(d)
    user_id = d["athlete"]["id"]
    st.session_state["TOKEN"] = d["access_token"]
    st.session_state["TOKEN_EXPIRE"] = d["expires_at"]
    st.session_state["TOKEN_REFRESH"] = d["refresh_token"]
    st.session_state["USER_ID"] = user_id
    st.session_state["USERNAME"] = d["athlete"].get("username", "no username")
    d_login_cnt = get_user_login_count()
    d_login_cnt[user_id] = 1 + d_login_cnt.get(user_id, 0)

    # remove url parameters
    st.query_params.clear()


@track_function_usage
def handle_token_refresh(d: dict) -> None:
    """Store refresh token response to session_state."""
    st.session_state["TOKEN"] = d["access_token"]
    st.session_state["TOKEN_EXPIRE"] = d["expires_at"]
    st.session_state["TOKEN_REFRESH"] = d["refresh_token"]


@track_function_usage
def token_refresh_if_needed() -> None:
    """Trigger token refresh if needed."""
    if time() > st.session_state["TOKEN_EXPIRE"] - 120:
        st.header("Token Refresh")
        d = api_post_token_refresh()
        handle_token_refresh(d)
        # st.write(d)


@track_function_usage
def perform_login() -> None:
    """Perform the login."""
    if "code" not in st.query_params:
        display_strava_auth_link()
    else:
        handle_redirect()


@track_function_usage
def logout() -> None:
    """Logout and unset all local access data."""
    api_post_deauthorize()
    for key in st.session_state:
        del st.session_state[key]

    st.write("Logged Out")
