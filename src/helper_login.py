"""Helper: Login to Strava via OAuth2."""

# ruff: noqa: E501

import subprocess
from time import time

import streamlit as st

from helper import get_env
from helper_api import api_post_deauthorize, api_post_oauth, api_post_token_refresh
from helper_logging import (
    get_logger_from_filename,
    get_user_login_count,
    track_function_usage,
)

_LOGGER = get_logger_from_filename(__file__)
PATH_WEBSTATS_SCRIPT = "/var/www/virtual/entorb/web-stats.py"


@track_function_usage
def display_strava_auth_link() -> None:
    """Display link for Strava auth."""
    st.title("Login")

    # this text is copied from README.md
    st.markdown("""This is a modern rewrite of my [old Strava Äpp](https://entorb.net/strava-old/). For bulk modify of activities, please use the old Äpp.
""")

    # attention: static files are under html/strava/strava-resources
    st.write(
        """
<table>
  <tbody>
    <tr>
      <td style="text-align:center;">
        <a target="_self" href="https://www.strava.com/oauth/authorize?client_id=28009&response_type=code&redirect_uri=https://entorb.net/strava-streamlit/?exchange_token&approval_prompt=force&scope=activity:read_all">
          <button class="strava-connect-button">
            <img src="/strava/strava-resources/btn_strava_connect_with_white.svg" alt="Connect with Strava (Read)">
          </button>
        </a>
        <div>Readonly: default</div>
      </td>
      <td style="text-align:center;">
        <a target="_self" href="https://www.strava.com/oauth/authorize?client_id=28009&response_type=code&redirect_uri=https://entorb.net/strava-streamlit/?exchange_token&approval_prompt=force&scope=activity:read_all,activity:write">
          <button class="strava-connect-button">
            <img src="/strava/strava-resources/btn_strava_connect_with_orange.svg" alt="Connect with Strava (Write)">
          </button>
        </a>
        <div>Write access: for modifying data</div>
      </td>
    </tr>
  </tbody>
</table>""",
        unsafe_allow_html=True,
    )

    # this text is copied from README.md
    st.markdown(
        """
## Latest features
* 2026-07-02 fetching of activity description field for Excel download (optional checkbox)
* 2026-05-25 Excel import of activities to Strava
* 2026-05-10 Write commute flag for activities to Strava

## Privacy

* **Code:** The [source-code](https://github.com/entorb/strava-streamlit/) is open source.
* **Data:** The app does not use a database. Your Strava data is only temporarily cached.
* **Access:** A temporary access token to your Strava profile is used and revoked at logout.
* **Cookies:** Only a single technical cookie is used for session identification and deleted at end of session. No user tracking.
"""
    )

    # cspell:disable
    st.markdown(
        """
## Feedback
* 2026-04-26 Robert: Großartige App, lässt mein Daten-Herz höher schlagen!
* 2025-12-20 Porkchop: This is absolutely amazing, thank you for publishing this!
* 2025-09-09 John: thanks for creating an awesome export tool.
* 2025-03-26 Chris: Thank you for this tool.

plus much more at [old App](https://entorb.net/strava-old/)
"""
    )


# cspell:enable


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

    st.session_state["API_SCOPE"] = st.query_params["scope"]

    # increase the login counter via web-stats script
    subprocess.run([PATH_WEBSTATS_SCRIPT, "strava-streamlit"], check=False, shell=False)  # noqa: S603

    # remove url parameters
    st.query_params.clear()


def init_dev_session_state() -> None:
    """Set session variables needed for local dev without login."""
    st.session_state["TOKEN"] = st.secrets["my_token"]
    st.session_state["TOKEN_EXPIRE"] = int(time() + 24 * 3600)
    st.session_state["TOKEN_REFRESH"] = st.secrets["my_refresh_token"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    st.session_state["API_SCOPE"] = "read,activity:write,activity:read_all"
    d_login_cnt = get_user_login_count()
    d_login_cnt[st.session_state["USER_ID"]] = 1 + d_login_cnt.get(
        st.session_state["USER_ID"], 0
    )
    st.session_state["USERNAME"] = st.secrets["my_username"]


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
    if get_env() == "PROD":
        api_post_deauthorize()
    for key in st.session_state:
        del st.session_state[key]
    # no st.logout() needed, as st.login is not used

    st.write("Logged Out")
