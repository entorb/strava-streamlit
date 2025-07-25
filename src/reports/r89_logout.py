"""Logout."""

import streamlit as st

from helper_logging import get_logger_from_filename
from helper_login import (
    logout,
)

st.title(__doc__[:-1])  # type: ignore
logger = get_logger_from_filename(__file__)


st.button("Logout", on_click=logout)
