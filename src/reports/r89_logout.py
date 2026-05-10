"""Logout."""

import streamlit as st

from helper_logging import get_logger_from_filename
from helper_login import (
    logout,
)

_LOGGER = get_logger_from_filename(__file__)


def main() -> None:  # noqa: D103
    st.button("Logout", on_click=logout)


if __name__ == "__main__":
    main()
