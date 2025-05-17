"""Internal Stats."""

import pandas as pd
import streamlit as st

from helper_logging import (
    get_call_stats,
    get_logger_from_filename,
    get_page_count,
    get_user_login_count,
)

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")


# double check, that this file is only access-able by me
if st.session_state["USER_ID"] != st.secrets["my_user_id"]:
    st.stop()


st.header("Session State")
st.write(st.session_state)


st.header("User Login Count")
d = get_user_login_count()
df = pd.DataFrame(data={"user": d.keys(), "count": d.values()})
df = df.sort_values(["count", "user"], ascending=[False, True])
st.dataframe(df, hide_index=True, column_config={"user": st.column_config.TextColumn()})


st.header("Page Count")
d = get_page_count()
df = pd.DataFrame(data={"page": d.keys(), "count": d.values()})
df = df.sort_values(["count", "page"], ascending=[False, True])
st.dataframe(df, hide_index=True)


st.header("Fct Call Stats")
call_stats = get_call_stats()
df = pd.DataFrame(call_stats).T.reset_index().sort_values("total_time", ascending=False)
df["total_time"] = df["total_time"].round(3)
st.dataframe(df, hide_index=True)


logger.info("End")
