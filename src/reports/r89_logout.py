"""Logout."""

import streamlit as st

from helper_logging import get_logger_from_filename
from helper_login import (
    logout,
)

LOGGER = get_logger_from_filename(__file__)


st.button("Logout", on_click=logout)
