"""ActivityList."""  # noqa: INP001

import datetime as dt

import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import init_logger
from helper_ui_components import excel_download_buttons, select_sport

st.title("Activity List")

logger = init_logger(__file__)
logger.info("Start")


def reset_filters() -> None:  # noqa: D103
    st.session_state.sel_type = None
    st.session_state.sel_year = [2000, dt.datetime.now(tz=dt.UTC).year]
    st.session_state.sel_duration = 0
    st.session_state.sel_km = 0
    st.session_state.sel_elev = 0


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

col1, col2, col3, col4, col5, col6 = st.columns(6)

sel_type = select_sport(df, col1)

if sel_type:
    df = df.query("type in @sel_type")

min_value = df["x_year"].min()
max_value = df["x_year"].max()
sel_year = col2.slider(
    "Year",
    min_value=min_value,
    max_value=max_value if max_value != min_value else min_value + 1,
    value=(df["x_year"].min(), df["x_year"].max()),
    key="sel_year",
)
if sel_year:
    df = df.query("x_year >= @sel_year[0] and x_year <= @sel_year[1]")

if df.empty:
    st.stop()

max_value = int(df["x_min"].max())
if max_value > 0:
    sel_duration = col3.slider(
        "Minutes", min_value=0, max_value=max_value, key="sel_duration"
    )
    if sel_duration:
        df = df.query("x_min > @sel_duration")
if df.empty:
    st.stop()

max_value = int(df["x_km"].max())
if max_value > 0:
    sel_km = col4.slider("Kilometer", min_value=0, max_value=max_value, key="sel_km")
    if sel_km:
        df = df.query("x_km > @sel_km")
if df.empty:
    st.stop()

max_value = int(df["total_elevation_gain"].max())
if max_value > 0:
    sel_elev = col5.slider(
        "Elevation",
        min_value=0,
        max_value=max_value,
        key="sel_elev",
    )
    if sel_elev:
        df = df.query("total_elevation_gain > @sel_elev")
if df.empty:
    st.stop()

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


logger.info("End")
