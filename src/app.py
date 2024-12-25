"""Main file."""

from pathlib import Path
from time import time

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


def reset_filters():
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

    df, df_gear = cache_all_activities_and_gears()

    df = df.drop(
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
    df = df.reset_index()

    df = df.rename(columns={"start_date_local": "start_date"})

    st.header("Activities")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    sel_type = col1.selectbox(
        "Sport", options=sorted(df["type"].unique()), index=None, key="sel_type"
    )
    if sel_type:
        df = df.query("type in @sel_type")
    sel_year = col2.selectbox(
        "Year",
        options=range(df["x_year"].min(), df["x_year"].max()),
        index=None,
        key="sel_year",
    )
    if sel_year:
        df = df.query("x_year == @sel_year")
    sel_duration = col3.slider(
        "Minutes", min_value=0, max_value=int(df["x_min"].max()), key="sel_duration"
    )
    if sel_duration:
        df = df.query("x_min > @sel_duration")
    sel_km = col4.slider(
        "Kilometer", min_value=0, max_value=int(df["x_km"].max()), key="sel_km"
    )
    if sel_km:
        df = df.query("x_km > @sel_km")
    sel_elev = col5.slider(
        "Elevation",
        min_value=0,
        max_value=int(df["total_elevation_gain"].max()),
        key="sel_elev",
    )
    if sel_elev:
        df = df.query("total_elevation_gain > @sel_elev")

    col6.button("Reset", on_click=reset_filters)

    st.columns(1)

    cols = df.columns.to_list()
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
    df = df[col_first]

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
        df,
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
    excel_download_buttons(df=df.reset_index(), exclude_index=True)

    st.header("Gear")
    st.dataframe(df_gear)

    st.header("Your known locations")
    kl = get_known_locations()
    df = pd.DataFrame(kl, columns=("Lat", "Lng", "Name"))
    df = df[["Name", "Lat", "Lng"]].sort_values("Name")
    st.dataframe(df, hide_index=True)
    # some more debug output only to me
    if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
        st.header("Session State")
        st.write(st.session_state)

    st.button("Logout", on_click=logout)

logger.info("End")

print("test")
