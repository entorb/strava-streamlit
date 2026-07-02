"""Contact."""

import streamlit as st

from helper_logging import get_logger_from_filename

_LOGGER = get_logger_from_filename(__file__)


def main() -> None:  # noqa: D103
    st.markdown("""
    * [Feedback](https://entorb.net/contact.php?origin=strava) and ideas for new reports are highly appreciated.
    * [SourceCode](https://github.com/entorb/strava-streamlit) can be found at GitHub.
    """)  # noqa: E501


if __name__ == "__main__":
    main()
