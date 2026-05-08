"""Internal Stats."""

import streamlit as st

from helper_logging import (
    get_logger_from_filename,
)

_LOGGER = get_logger_from_filename(__file__)

# double check, that this file is only access-able by me
if st.session_state["USER_ID"] != st.secrets["my_user_id"]:
    st.stop()


if "activity:write" not in st.session_state["API_SCOPE"]:
    st.warning("API scope 'activity:write' missing")

st.header("TODO: Create activity")

st.header("TODO: Update to Commute")
