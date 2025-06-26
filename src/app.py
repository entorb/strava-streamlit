"""Main file."""

# ruff: noqa: E402
import streamlit as st

# needs to be first streamlit command, so placed before the imports
st.set_page_config(page_title="Strava Äpp V2", page_icon=None, layout="wide")

from pathlib import Path
from time import time

from helper_logging import get_logger_from_filename, get_user_login_count
from helper_login import (
    perform_login,
    token_refresh_if_needed,
)
from helper_ui_components import create_navigation_menu

logger = get_logger_from_filename(__file__)
logger.info("Start")


def include_matomo_stats() -> None:
    """Include Matomo access stats update JavaScript snippet."""
    import streamlit.components.v1 as components  # noqa: PLC0415

    components.html(
        """
<script>
var _paq = window._paq = window._paq || [];
_paq.push(['trackPageView']);
_paq.push(['enableLinkTracking']);
(function() {
    var u="https://entorb.net/stats/matomo/";
    _paq.push(['setTrackerUrl', u+'matomo.php']);
    _paq.push(['setSiteId', '8']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
})();
</script>
    """,
        height=0,
    )


def include_sentry() -> None:
    # TODO: https://github.com/streamlit/streamlit/issues/3426
    """Load Sentry."""
    import sentry_sdk  # noqa: PLC0415

    sentry_sdk.init(
        dsn=st.secrets["sentry_dns"],
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        traces_sample_rate=0.0,
        environment="entorb.net",
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


set_env()

if st.session_state["ENV"] == "PROD":
    include_matomo_stats()

# include_sentry()
# st.error("Test Error")
# st.exception("Test Exception")

# for local development I skip the login
if st.session_state["ENV"] == "DEV":
    st.session_state["TOKEN"] = st.secrets["my_token"]
    st.session_state["TOKEN_EXPIRE"] = int(time() + 24 * 3600)
    st.session_state["TOKEN_REFRESH"] = st.secrets["my_refresh_token"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    d_login_cnt = get_user_login_count()
    d_login_cnt[st.session_state["USER_ID"]] = 1 + d_login_cnt.get(
        st.session_state["USER_ID"], 0
    )
    st.session_state["USERNAME"] = st.secrets["my_username"]

if "TOKEN" not in st.session_state:
    perform_login()


if "TOKEN" in st.session_state:
    # check if we need to refresh the token
    token_refresh_if_needed()

    st.logo("src/strava-resources/api_logo_pwrdBy_strava_stack_light.svg", size="large")
    create_navigation_menu()


logger.info("End")
