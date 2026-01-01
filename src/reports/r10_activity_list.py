"""Activity List and Excel Export."""

from math import isnan

import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename
from helper_ui_components import excel_download_buttons, select_sport

st.title(__doc__[:-1])  # type: ignore
logger = get_logger_from_filename(__file__)


st.markdown(
    "Edit at [Strava](https://www.strava.com/athlete/training) or bulk-edit using my [Äpp V1](https://entorb.net/strava-old/)"  # noqa: E501
)

df, df_gear = cache_all_activities_and_gears()

min_year = df["x_year"].min()
max_year = df["x_year"].max()
if min_year == max_year:
    max_year += 1


def reset_filters() -> None:  # noqa: D103
    st.session_state.sel_type = None
    st.session_state.sel_year = [min_year, max_year]
    st.session_state.sel_duration = 0
    st.session_state.sel_km = 0
    st.session_state.sel_elev = 0


col1, col2, col3, col4, col5, col6, col7 = st.columns((1, 1, 1, 1, 1, 0.5, 0.5))

sel_type = select_sport(df, col1)

if sel_type:
    df = df.query("type in @sel_type")

sel_year = col2.slider(
    "Year",
    min_value=min_year,
    max_value=max_year,
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

max_value = df["total_elevation_gain"].max()

if not isnan(max_value):
    max_value = int(max_value)
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
sel_km = col6.selectbox(label="km/mi", options=["km", "mi"])

col7.button("Reset", on_click=reset_filters)

st.columns(1)


# to rename "x_" prefix
col_names = {}
for col in df.columns.to_list():
    if col.startswith("x_"):
        col_names[col] = col[2:]
    elif col.startswith("average_"):
        col_names[col] = col[8:] + "_av"
    else:
        col_names[col] = col  # unchanged
col_names["average_heartrate"] = "HR_av"
col_names["average_watts"] = "W_av"
col_names["device_watts"] = "W_device"
col_names["display_hide_heartrate_option"] = "HR_hide"
col_names["heartrate_opt_out"] = "HR_opt_out"
col_names["location_country"] = "country"
col_names["max_heartrate"] = "HR_max"
col_names["max_watts"] = "W_max"
col_names["total_elevation_gain"] = "elev_gain"
col_names["weighted_average_watts"] = "W_weight_avg"
col_names["x_gear_name"] = "gear"
col_names["x_min"] = "minutes"
col_names["x_nearest_city_start"] = "nearest_city"


# some we do not display in web table, but keep for Excel export
col_hide = [
    "distance",
    "elapsed_time",
    "gear_id",
    "id",
    "max_speed",
    "moving_time",
    "speed_av",
    "start_date_local",
    "timezone",
    "utc_offset",
    "week",
    "year",
    "month",
    "quarter",
    "start_h",
]
if sel_km == "km":
    col_hide.extend(("min/mi", "mi", "mph", "max_mph"))
else:
    col_hide.extend(("min/km", "km", "km/h", "max_km/h"))
col_order = [new for new in col_names.values() if new not in col_hide]

st.dataframe(
    df.rename(columns=col_names, errors="raise"),
    width="stretch",
    hide_index=True,
    column_order=col_order,
    column_config={
        # "start_date_local": st.column_config.DateColumn(format=FORMAT_DATETIME),
        # no pinning, as taking too much space on mobile
        # "name": st.column_config.Column(pinned=False),
        "url": st.column_config.LinkColumn("ID", display_text=r"/(\d+)$"),
        "dl": st.column_config.LinkColumn("DL", display_text="DL"),
    },
)
excel_download_buttons(df=df, file_name="Strava_Activity_List.xlsx", exclude_index=True)

st.header("Gear")
st.dataframe(df_gear)
