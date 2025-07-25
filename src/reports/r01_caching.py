"""Caching of Activities."""

import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename

st.title(__doc__[:-1])  # type: ignore
logger = get_logger_from_filename(__file__)


col1, _ = st.columns((1, 5))
if "years" not in st.session_state:
    st.session_state["years"] = 0
years = st.session_state["years"]

lst = ["Current", "Last", "Last 5", "Last 10", "All"]
if years == 0:
    index = 0
elif years == 1:
    index = 1
elif years == 5:  # noqa: PLR2004
    index = 2
    index = 3
else:
    index = 4

sel_years = col1.selectbox(label="Years", options=lst, index=index)

if sel_years == "Current":
    st.session_state["years"] = 0
elif sel_years == "Last":
    st.session_state["years"] = 1
elif sel_years == "Last 5":
    st.session_state["years"] = 5
elif sel_years == "Last 10":
    st.session_state["years"] = 10
else:
    st.session_state["years"] = 100

df = cache_all_activities_and_gears()[0]

# export activity_columns
# lst = sorted(df.columns)
# Path("activity_columns.txt").write_text("\n".join(lst) + "\n")

df2 = (
    df[["x_year", "x_url"]]
    .groupby("x_year")
    .count()
    .sort_index(ascending=False)
    .reset_index()
    .rename(columns={"x_year": "year", "x_url": "count"})
)
col1.dataframe(
    df2,
    hide_index=True,
    use_container_width=True,
    column_config={"year": st.column_config.NumberColumn(format="%d")},
)
