"""Main file."""
# ruff: noqa: E402

import tracemalloc
from time import time

import streamlit as st

# needs to be first streamlit command, so placed before the imports
st.set_page_config(page_title="Strava Äpp V2", page_icon=None, layout="wide")

from helper import get_env
from helper_logging import get_logger_from_filename, get_user_login_count, init_logging
from helper_login import (
    perform_login,
    token_refresh_if_needed,
)
from helper_ui_components import create_navigation_menu

MEASURE_MEMORY = True
init_logging()
LOGGER = get_logger_from_filename(__file__)


def init_sentry() -> None:
    """Initialize Sentry exception tracking/alerting."""
    import sentry_sdk  # noqa: PLC0415

    sentry_sdk.init(
        dsn=st.secrets["sentry_dsn"],
        environment=get_env(),
        send_default_pii=True,
        traces_sample_rate=0.0,
    )


def init_matomo() -> None:
    """Initialize Matomo access stats, via JavaScript snippet."""
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


def init_dev_session_state() -> None:
    """Set session variables needed for local dev without login."""
    st.session_state["TOKEN"] = st.secrets["my_token"]
    st.session_state["TOKEN_EXPIRE"] = int(time() + 24 * 3600)
    st.session_state["TOKEN_REFRESH"] = st.secrets["my_refresh_token"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    d_login_cnt = get_user_login_count()
    d_login_cnt[st.session_state["USER_ID"]] = 1 + d_login_cnt.get(
        st.session_state["USER_ID"], 0
    )
    st.session_state["USERNAME"] = st.secrets["my_username"]


def main() -> None:  # noqa: D103
    if get_env() == "PROD":
        init_sentry()
        init_matomo()

    if get_env() == "DEV":
        init_dev_session_state()

    if "TOKEN" not in st.session_state:
        perform_login()

    if "TOKEN" in st.session_state:
        # check if we need to refresh the token
        token_refresh_if_needed()

        st.logo(
            "src/strava-resources/api_logo_pwrdBy_strava_stack_light.svg", size="large"
        )
        if MEASURE_MEMORY:
            tracemalloc.start()
        time_start = time()
        page = create_navigation_menu()
        pagename = page.url_path or "main"
        st.title(page.title)

        page.run()

        time_end = time()
        log_line = f"stats: {pagename},{round(time_end - time_start, 1)}s"

        if MEASURE_MEMORY:
            max_bytes = tracemalloc.get_traced_memory()[0]
            tracemalloc.stop()
            log_line += f",{round(max_bytes / 1_048_576, 1)}MB"
        LOGGER.info(log_line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # automatically triggered by logger.exception
        # sentry_sdk.capture_exception(e)
        LOGGER.exception("Exception:")
        st.exception(e)
        st.stop()
