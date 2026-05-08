"""Contact."""

import streamlit as st

from helper_logging import get_logger_from_filename

_LOGGER = get_logger_from_filename(__file__)


st.markdown("""
* [Feedback](https://entorb.net/contact.php?origin=strava) and ideas for new reports are highly appreciated.
* For bulk modify of activities and Excel import, please use the old [Äpp](https://entorb.net/strava-old/).
""")  # noqa: E501
