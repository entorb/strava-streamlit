"""Logout."""  # noqa: INP001

import streamlit as st

from helper_logging import init_logger
from helper_login import (
    logout,
)

st.title(__doc__[:-1])  # type: ignore

logger = init_logger(__file__)
logger.info("Start")

st.button("Logout", on_click=logout)

logger.info("End")
