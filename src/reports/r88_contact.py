"""Contact."""

import streamlit as st

from helper_logging import get_logger_from_filename

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")


st.markdown("""
* [Feedback](https://entorb.net/contact.php?origin=strava) and ideas for new reports are highly appreciated.
* For bulk modify of activities and Excel import, please use the old [Äpp](https://entorb.net/strava/).
""")  # noqa: E501


logger.info("End")
