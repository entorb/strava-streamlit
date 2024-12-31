"""Internal Stats."""

import streamlit as st

from helper_logging import get_logger_from_filename

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")
st.header("Session State")
st.write(st.session_state)

logger.info("End")
