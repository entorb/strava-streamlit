"""Internal Stats."""

import pandas as pd
import streamlit as st

from helper_logging import get_call_stats, get_logger_from_filename

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")

# double check, that this file is only access-able by me
if st.session_state["USER_ID"] != st.secrets["my_user_id"]:
    st.stop()

st.header("Session State")
st.write(st.session_state)


st.header("Fct Call Stats")
call_stats = get_call_stats()
df = pd.DataFrame(call_stats).T
df["total_time"] = df["total_time"].round(3)
st.dataframe(df, hide_index=False)

logger.info("End")
