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


def calc_days_in_year(year: int) -> int:
    """Calc number of days in year, for current year only till today."""
    start = dt.date(year, 1, 1)
    end = dt.date(year, 12, 31) if year != DATE_TODAY.year else DATE_TODAY
    return 1 + (end - start).days


DATE_TODAY = dt.datetime.now(tz=dt.UTC).date()

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
past_days_in_year = calc_days_in_year(int(sel_year))
today_day_no = 1 + (DATE_TODAY - dt.date(DATE_TODAY.year, 1, 1)).days
total_days_in_this_year = (
    1 + (dt.date(DATE_TODAY.year, 12, 31) - dt.date(DATE_TODAY.year, 1, 1)).days
)
year_ratio = today_day_no / total_days_in_this_year

# optionally filter on sports
sel_types = col2.multiselect(label="Sports", options=list_sports(df), key="sel_types")
if sel_types:
    df = df.query("type in @sel_types")

cnt_activities = len(df)
hour_sum = df["Hour-sum"].sum()
km_sum = df["Kilometer-sum"].sum()
elev_km_sum = df["Elevation-sum"].sum() / 1000
active_days = df[["date"]].drop_duplicates().count().iloc[0]

cols = st.columns(5)
# headers
cols[0].subheader("Activities")
cols[1].subheader("Active Days")
cols[2].subheader("Time")
cols[3].subheader("Distance")
cols[4].subheader("Elevation")

# current data
cols[0].metric(label="Activities", value=cnt_activities, label_visibility="hidden")
cols[1].metric(label="Active Days", value=active_days, label_visibility="hidden")
cols[2].metric(label="Hours", value=f"{round(hour_sum)} h", label_visibility="hidden")
cols[3].metric(label="Distance", value=f"{round(km_sum)} km", label_visibility="hidden")
cols[4].metric(
    label="Elevation", value=f"{round(elev_km_sum, 1)} km", label_visibility="hidden"
)

# comparisons
cols[1].metric(
    label="Active Days %", value=f"{round(100 * active_days / past_days_in_year, 1)} %"
)
cols[2].metric(
    label="Minutes per Day",
    value=f"{round(60 * hour_sum / past_days_in_year)} min",
)
cols[2].metric(
    label="Hours per Week",
    value=f"{round(hour_sum / past_days_in_year * 7, 1)} h",
)

x = km_sum / 42.195
v = f"{x:.2f} x"
cols[3].metric(label="Marathon", value=v)

x = km_sum / 40_075
v = f"{x:.2f} x" if x > 1 else f"{x * 100:.2f} %"
cols[3].metric(label="Earth Equator", value=v)

x = km_sum / 384_400
v = f"{x:.2f} x" if x > 1 else f"{x * 100:.2f} %"
cols[3].metric(label="To Moon", value=v)

x = elev_km_sum / 8.848
v = f"{x:.2f} x" if x > 1 else f"{x * 100:.2f} %"
cols[4].metric(label="Mount Everest", value=v)

x = elev_km_sum / 12_756
v = f"{x:.2f} x" if x > 1 else f"{x * 100:.2f} %"
cols[4].metric(label="Earth Diameter", value=v)

# prognosis
if DATE_TODAY.year == int(sel_year):
    st.subheader("Prognosis")
    cols = st.columns(5)
    cols[0].metric(
        label="Activities",
        value=f"{round(cnt_activities / year_ratio)}",
        label_visibility="hidden",
    )
    cols[1].metric(
        label="Active Days",
        value=f"{round(active_days / year_ratio)}",
        label_visibility="hidden",
    )
    cols[2].metric(
        label="Hours",
        value=f"{round(hour_sum / year_ratio)} h",
        label_visibility="hidden",
    )
    cols[3].metric(
        label="Distance",
        value=f"{round(km_sum / year_ratio)} km",
        label_visibility="hidden",
    )
    cols[4].metric(
        label="Elevation",
        value=f"{round(elev_km_sum / year_ratio)} km",
        label_visibility="hidden",
    )


logger.info("End")
