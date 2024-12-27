"""Activity Stats."""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename
from helper_ui_components import list_sports, select_sport

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")


AGGREGATIONS = {
    "Count": "count",
    "Hour-sum": "sum",
    "Hour-avg": "mean",
    "Kilometer-sum": "sum",
    "Kilometer-avg": "mean",
    "Elevation-sum": "sum",
    "Elevation-avg": "mean",
    "Elevation%-avg": "mean",
    "Speed_km/h-avg": "mean",
    "Speed_km/h-max": "max",
    "Heartrate-avg": "mean",
    "Heartrate-max": "max",
}


def activity_stats_grouping(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    # copied from strava V1: activityStats2.py
    """
    Perform GROUP BY aggregation for time_freq (month, week, quarter, year) and type.
    """
    assert freq in ("Year", "Quarter", "Month", "Week")

    if freq == "Week":
        df["date-group"] = (
            df["start_date_local"].dt.to_period("W").apply(lambda r: r.start_time)
        ).dt.strftime("%Y-%m-%d")
        # alternative, using yyyy-ww
        # df["date-group"] = (
        #     df["x_year"].astype(str) + "-CW" + df["x_week"].astype(str).str.zfill(2)
        # )
    elif freq == "Month":
        # df["date-group"] = (
        #     df["x_year"].astype(str) + "-" + df["x_month"].astype(str).str.zfill(2)
        # )
        df["date-group"] = df["start_date_local"].dt.strftime("%Y-%m")
    elif freq == "Quarter":
        df["date-group"] = df["x_year"].astype(str) + "-Q" + df["x_quarter"].astype(str)
    elif freq == "Year":
        df["date-group"] = df["x_year"]

    # reduce to relevant columns
    df = df[
        [
            "type",
            "id",
            "date-group",
            "x_min",
            "x_km",
            "total_elevation_gain",
            "x_elev_%",
            "x_km/h",
            "average_heartrate",
            "max_heartrate",
            "x_max_km/h",
        ]
    ]

    df = df.rename(
        columns={
            "id": "Count",
            # "x_date": "date",
            "x_min": "Hour-sum",
            "x_km": "Kilometer-sum",
            "total_elevation_gain": "Elevation-sum",
            "x_elev_%": "Elevation%-avg",
            "x_km/h": "Speed_km/h-avg",
            "average_heartrate": "Heartrate-avg",
        },
    )  # not inplace here!

    # replace 0 by nan
    df = df.replace(0, np.nan)
    # add some more columns
    df["Hour-sum"] = df["Hour-sum"] / 60
    df["Hour-avg"] = df["Hour-sum"]
    df["Kilometer-avg"] = df["Kilometer-sum"]
    df["Elevation-avg"] = df["Elevation-sum"]
    df["Speed_km/h-max"] = df["Speed_km/h-avg"]
    df["Heartrate-max"] = df["Heartrate-avg"]

    df = df.groupby(["type", pd.Grouper(key="date-group")]).agg(AGGREGATIONS)
    df = df.reset_index()

    # rounding
    for measure in AGGREGATIONS:
        if measure in ("Count", "Elevation-sum"):
            df[measure] = df[measure].astype(np.int64)
        else:
            df[measure] = df[measure].round(1)

    return df


df = cache_all_activities_and_gears()[0]

col1, col2, col3, col4 = st.columns((1, 1, 3, 1))

sel_freq = col1.selectbox("Frequency", options=("Year", "Quarter", "Month", "Week"))

min_value = df["x_year"].min()
max_value = df["x_year"].max()
sel_year = col3.slider(
    "Year",
    min_value=min_value,
    max_value=max_value if max_value != min_value else min_value + 1,
    value=(df["x_year"].min(), df["x_year"].max()),
    key="sel_year",
)
if sel_year:
    df = df.query("x_year >= @sel_year[0] and x_year <= @sel_year[1]")


st.header(f"All Activity {sel_freq} Count")
df2 = activity_stats_grouping(df, freq=sel_freq)

# date_axis_type = "N" if sel_freq in ("Year", "Quarter") else "T"
date_axis_type = "N"

c = (
    alt.Chart(
        df2,
        title=alt.TitleParams(f"Strava Stats: All Activity {sel_freq} Count"),
    )
    .mark_bar()
    .encode(
        x=alt.X("date-group:" + date_axis_type, title=None),
        y=alt.Y("Count:Q", title=None),
        color="type:N",
    )
)
st.altair_chart(c, use_container_width=True)


st.header("Per Sport")
col1, col2, col3, col4 = st.columns((1, 1, 1, 3))

sel_type = select_sport(df, col1, mandatory=True)

sel_agg = col2.selectbox(
    "Aggregation",
    options=AGGREGATIONS.keys(),
)


c = (
    alt.Chart(
        df2.query("type==@sel_type"),
        title=alt.TitleParams(f"Strava Stats: {sel_type} {sel_freq} {sel_agg}"),
    )
    .mark_bar()
    .encode(
        x=alt.X("date-group:" + date_axis_type, title=None),
        y=alt.Y(sel_agg + ":Q", title=None),
    )
)
st.altair_chart(c, use_container_width=True)

st.header("Active Days")
sel_types = st.multiselect(label="Sport", options=list_sports(df))
if sel_types:
    df = df.query("type in @sel_types")
df3 = (
    df[["x_year", "x_date"]]
    .drop_duplicates()
    .groupby("x_year")
    .agg(count=("x_date", "count"))
    .reset_index()
)

c = (
    alt.Chart(df3)
    .mark_bar()
    .encode(
        x=alt.X("x_year:N", title=None),
        y=alt.Y("count:Q", title=None),
        tooltip=[
            alt.Tooltip("x_year:N", title="Year"),
            alt.Tooltip("count:Q", title="Count"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)
# st.write(df2)

logger.info("End")
