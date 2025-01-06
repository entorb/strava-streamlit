"""Current Year."""

import datetime as dt

import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    reduce_and_rename_activity_df_for_stats,
)
from helper_logging import get_logger_from_filename
from helper_ui_components import list_sports

st.title(__doc__[:-1])  # type: ignore

logger = get_logger_from_filename(__file__)
logger.info("Start")


df = cache_all_activities_and_gears()[0]
df = reduce_and_rename_activity_df_for_stats(df)

col1, col2, _ = st.columns((1, 2, 3))

# list of years with min 3 activities
df2 = (
    df[["year", "Count"]]
    .groupby("year")
    .agg(Count=("Count", "count"))
    .sort_index(ascending=False)
)
df2 = df2[df2["Count"] >= 3]  # noqa: PLR2004
sel_year = col1.selectbox(label="Year", options=df2.index)
df = df[df["year"] == sel_year]

# optionally filter on sports
sel_types = col2.multiselect(label="Sports", options=list_sports(df))
if sel_types:
    df = df.query("type in @sel_types")

cnt_activities = len(df)
hour_sum = df["Hour-sum"].sum()
km_sum = df["Kilometer-sum"].sum()
elev_km_sum = df["Elevation-sum"].sum() / 1000
active_days = df[["date"]].drop_duplicates().count().iloc[0]

cols = st.columns(5)
cols[0].subheader("Activities")
cols[1].subheader("Active Days")
cols[2].subheader("Time")
cols[3].subheader("Distance")
cols[4].subheader("Elevation")
cols[0].metric(label="Activities", value=cnt_activities, label_visibility="hidden")
cols[1].metric(label="Active Days", value=active_days, label_visibility="hidden")
cols[2].metric(label="Hours", value=f"{round(hour_sum)} h", label_visibility="hidden")
cols[3].metric(label="Distance", value=f"{round(km_sum)} km", label_visibility="hidden")
cols[4].metric(
    label="Elevation", value=f"{round(elev_km_sum,1)} km", label_visibility="hidden"
)


def calc_days_in_year(year: int) -> int:
    """Calc number of days in year, for current year only till today."""
    date_today = dt.datetime.now(tz=dt.UTC).date()
    start = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31) if year != date_today.year else date_today
    return 1 + (end - start).days


days_in_year = calc_days_in_year(sel_year)
cols[1].metric(
    label="Active Days %", value=f"{round(100 * active_days / days_in_year, 1)} %"
)

cols[2].metric(
    label="Minutes per Day",
    value=f"{round(60 * hour_sum / days_in_year,1)} min",
)


cols[3].metric(
    label="Earth Equator",
    value=f"{round(100 * km_sum / 40_075 ,1)} %",
)
cols[3].metric(
    label="To Moon",
    value=f"{round(100 * km_sum / 384_400 ,3)} %",
)

cols[4].metric(
    label="Mount Everest",
    value=f"{round(elev_km_sum / 8.848 ,2)} x",
)
cols[4].metric(
    label="Earth Diameter",
    value=f"{round(100 * elev_km_sum / 12_756 ,3)} %",
)


logger.info("End")
