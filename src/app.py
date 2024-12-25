"""Main file."""

from pathlib import Path
from time import time

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    get_known_locations,
)
from helper_logging import init_logger
from helper_login import (
    logout,
    perform_login,
    token_refresh_if_needed,
)
from helper_ui_components import excel_download_buttons

# https://momentjs.com/docs/#/displaying/format/
FORMAT_DATETIME = "YY-MM-DD HH:mm"


def set_env() -> None:
    """Set ENV to entorb.net / local."""
    if "ENV" not in st.session_state:
        if Path("/home/entorb/strava-streamlit").is_dir():
            st.session_state["ENV"] = "PROD"
        else:
            st.session_state["ENV"] = "DEV"
            # when running locally, ensure we have data dirs
            Path("./cache").mkdir(exist_ok=True)
            Path("./data").mkdir(exist_ok=True)


AGGREGATIONS = {
    "Count": "count",
    "Hour-sum": "sum",
    "Hour-avg": "mean",
    "Kilometer-sum": "sum",
    "Kilometer-avg": "mean",
    "Elevation-sum": "sum",
    "Elevation-avg": "mean",
    "Elevation%_avg": "mean",
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
    assert freq in ("Year", "Quarter", "Month", "Week")  # noqa: S101
    # reduce to relevant columns
    df = df[
        [
            "id",
            "type",
            "x_date",
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
            "x_date": "date",
            "x_min": "Hour-sum",
            "x_km": "Kilometer-sum",
            "total_elevation_gain": "Elevation-sum",
            "x_elev_%": "Elevation%_avg",
            "x_km/h": "Speed_km/h-avg",
            "average_heartrate": "Heartrate-avg",
        },
    )  # not inplace here!

    # replace 0 by nan
    df = df.replace(0, np.nan)
    df["date"] = pd.to_datetime(df["date"])
    df["Hour-sum"] = df["Hour-sum"] / 60
    df["Hour-avg"] = df["Hour-sum"]
    df["Kilometer-avg"] = df["Kilometer-sum"]
    df["Elevation-avg"] = df["Elevation-sum"]
    df["Heartrate-max"] = df["Heartrate-avg"]
    df["Speed_km/h-max"] = df["Speed_km/h-avg"]

    if freq == "Week":
        df = df.groupby(["type", pd.Grouper(key="date", freq="W")]).agg(AGGREGATIONS)

    if freq == "Month":
        df = df.groupby(["type", pd.Grouper(key="date", freq="MS")]).agg(AGGREGATIONS)

    if freq == "Quarter":
        df = df.groupby(["type", pd.Grouper(key="date", freq="QS")]).agg(AGGREGATIONS)

    if freq == "Year":
        df["date"] = df["date"].dt.year
        df = df.groupby(["type", pd.Grouper(key="date")]).agg(AGGREGATIONS)

    # rounding
    for measure in AGGREGATIONS:
        if measure in ("Count", "Elevation-sum"):
            df[measure] = df[measure].astype(np.int64)
        else:
            df[measure] = df[measure].round(1)

    df = df.reset_index()

    # discrete values for date
    if freq == "Week":
        df["date"] = df["date"].dt.strftime("%Y-W%W")
    elif freq == "Month":
        df["date"] = df["date"].dt.strftime("%Y-%m")
    elif freq == "Quarter":
        df["date"] = df["date"].dt.to_period("Q").dt.strftime("%Y-Q%q")
    elif freq == "Year":
        df["date"] = df["date"].astype(int)
    st.write(df)
    return df


title = "Strava Äpp V2"
st.set_page_config(page_title=title, page_icon=None, layout="wide")
st.title(title)

logger = init_logger(__file__)
logger.info("Start")

set_env()


# for local development I skip the login
if st.session_state["ENV"] == "DEV":
    st.session_state["TOKEN"] = st.secrets["my_token"]
    st.session_state["TOKEN_EXPIRE"] = int(time() + 24 * 3600)
    st.session_state["TOKEN_REFRESH"] = st.secrets["my_refresh_token"]
    st.session_state["USER_ID"] = st.secrets["my_user_id"]
    st.session_state["USERNAME"] = st.secrets["my_username"]

if "TOKEN" not in st.session_state:
    perform_login()


def reset_filters() -> None:  # noqa: D103
    st.session_state.sel_type = None
    st.session_state.sel_year = None
    st.session_state.sel_duration = 0
    st.session_state.sel_km = 0
    st.session_state.sel_elev = 0


if "TOKEN" in st.session_state:
    # check if we need to refresh the token
    token_refresh_if_needed()

    username = st.session_state["USERNAME"]
    st.write(f"Welcome User '{username}'")

    df2, df_gear = cache_all_activities_and_gears()

    df2 = df2.drop(
        columns=[
            "resource_state",
            "athlete",
            "map",
            "upload_id",
            "upload_id_str",
            "external_id",
            "start_date",
        ]
    )
    df2 = df2.reset_index()

    df2 = df2.rename(columns={"start_date_local": "start_date"})

    st.header("Activities")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    sel_type = col1.selectbox(
        "Sport", options=sorted(df2["type"].unique()), index=None, key="sel_type"
    )
    if sel_type:
        df2 = df2.query("type in @sel_type")

    sel_year = col2.slider(
        "Year",
        min_value=df2["x_year"].min(),
        max_value=df2["x_year"].max(),
        value=(df2["x_year"].min(), df2["x_year"].max()),
        key="sel_year",
    )
    if sel_year:
        df2 = df2.query("x_year >= @sel_year[0] and x_year <= @sel_year[1]")

    sel_duration = col3.slider(
        "Minutes", min_value=0, max_value=int(df2["x_min"].max()), key="sel_duration"
    )
    if sel_duration:
        df2 = df2.query("x_min > @sel_duration")

    sel_km = col4.slider(
        "Kilometer", min_value=0, max_value=int(df2["x_km"].max()), key="sel_km"
    )
    if sel_km:
        df2 = df2.query("x_km > @sel_km")

    sel_elev = col5.slider(
        "Elevation",
        min_value=0,
        max_value=int(df2["total_elevation_gain"].max()),
        key="sel_elev",
    )
    if sel_elev:
        df2 = df2.query("total_elevation_gain > @sel_elev")

    col6.button("Reset", on_click=reset_filters)

    st.columns(1)

    cols = df2.columns.to_list()
    col_first = [
        "x_date",
        "name",
        "type",
        "x_url",
        "start_date",
        "x_min",
        "x_km",
        "x_elev_%",
        "x_km/h",
        "x_max_km/h",
        "x_start_locality",
        "x_end_locality",
        "x_dist_start_end_km",
        "x_nearest_city_start",
        "location_country",
        "x_gear_name",
        "average_heartrate",
        "max_heartrate",
        "average_cadence",
        "average_watts",
        "kilojoules",
        "total_elevation_gain",
        "elev_high",
        "elev_low",
        "average_temp",
    ]
    for col in col_first:
        if col in cols:
            cols.remove(col)
        else:
            st.write(f"'{col}' not in columns")
    col_first.extend(cols)
    df2 = df2[col_first]

    # some we do not display in web table, but keep for Excel export
    col_hide = [
        "distance",
        "moving_time",
        "id",
        "timezone",
        "utc_offset",
        "gear_id",
        "average_speed",
        "max_speed",
        "x_week",
        "elapsed_time",
        "start_date",
    ]
    for col in col_hide:
        if col in col_first:
            col_first.remove(col)
        else:
            st.write(f"'{col}' not in columns")

    st.dataframe(
        df2,
        use_container_width=True,
        hide_index=True,
        column_order=col_first,
        column_config={
            # "start_date": st.column_config.DateColumn(format=FORMAT_DATETIME),
            "name": st.column_config.Column(pinned=True),
            "x_url": st.column_config.LinkColumn("ID", display_text=r"/(\d+)$"),
            "x_min": "minutes",
            "x_km": "km",
            "x_elev_%": "elev %",
            "x_km/h": "km/h",
            "x_max_km/h": "max_km/h",
            "x_dist_start_end_km": "km_start_end",
            "x_start_locality": "location_start",
            "x_end_locality": "location_end",
            "x_nearest_city_start": "nearest_city",
            "x_gear_name": "gear",
            "total_elevation_gain": "elev_gain",
            "x_date": "date",
        },
    )
    excel_download_buttons(df=df2.reset_index(), exclude_index=True)

    st.header("Gear")
    st.dataframe(df_gear)

    st.header("Activity Stats")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    sel_freq = col1.selectbox("Frequency", options=("Year", "Quarter", "Month", "Week"))
    sel_type = col2.selectbox("Sport", options=sorted(df2["type"].unique()))
    sel_agg = col3.selectbox(
        "Aggregation",
        options=AGGREGATIONS.keys(),
    )

    df2 = activity_stats_grouping(df2, freq=sel_freq)

    c = (
        alt.Chart(
            df2.query("type==@sel_type"),
            title=alt.TitleParams(
                f"Strava Stats: {sel_type} {sel_freq} {sel_agg}", anchor="middle"
            ),
        )
        .mark_bar()
        .encode(
            x=alt.X("date:N", title=None),
            y=alt.Y(sel_agg + ":Q", title=None),
        )
    )
    st.altair_chart(c, use_container_width=True)

    c = (
        alt.Chart(
            df2,
            title=alt.TitleParams(
                f"Strava Stats: All Activity {sel_freq} Count", anchor="middle"
            ),
        )
        .mark_bar()
        .encode(
            x=alt.X("date:N", title=None),
            y=alt.Y("Count:Q", title=None),
            color="type:N",
        )
    )
    st.altair_chart(c, use_container_width=True)

    #
    # #
    #
    st.header("Your known locations")
    kl = get_known_locations()
    df2 = pd.DataFrame(kl, columns=("Lat", "Lng", "Name"))
    df2 = df2[["Name", "Lat", "Lng"]].sort_values("Name")
    st.dataframe(df2, hide_index=True)
    # some more debug output only to me
    if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
        st.header("Session State")
        st.write(st.session_state)

    st.button("Logout", on_click=logout)

logger.info("End")

print("test")
