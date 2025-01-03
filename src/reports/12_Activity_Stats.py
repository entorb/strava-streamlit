"""Activity Stats."""

import altair as alt
import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename, track_function_usage
from helper_pandas import reorder_cols
from helper_ui_components import excel_download_buttons, list_sports, select_sport

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


@track_function_usage
def generate_empty_df(
    sport: str, freq: str, year_min: int, year_max: int
) -> pd.DataFrame:
    """Generate and empty DataFrame with year, freq and type=Run ans index."""
    assert freq in ("Quarter", "Month", "Week")

    field = freq.lower()
    # single value df
    df = pd.DataFrame(
        data={
            "year": [year_min],
            field: 1,
            "type": sport,
            "Count": 0,
        }
    ).set_index(["year", field, "type"])

    if freq == "Quarter":
        rng = range(1, 4 + 1)
    elif freq == "Month":
        rng = range(1, 12 + 1)
    elif freq == "Week":
        rng = range(1, 52 + 1)

    # extend year and field
    df = df.reindex(
        pd.MultiIndex.from_product(
            [range(year_min, year_max + 1), rng, [sport]],
            names=["year", field, "type"],
        ),
        fill_value=0,
    )
    return df


def add_data_and_empty_df(df2: pd.DataFrame, df3: pd.DataFrame) -> pd.DataFrame:
    """
    Add empty DataFrame to real data.

    Both have a 3-fold index: year, freq, type
    """
    df2 = df2.add(df3, fill_value=0)
    # trim ends, maybe via
    first_idx = df2[df2["Count"] > 0].index[0]
    last_idx = df2[df2["Count"] > 0].index[-1]
    df2 = df2.loc[first_idx:last_idx]

    df2 = df2.fillna(0).reset_index()
    return df2


@track_function_usage
def activity_stats_grouping(df: pd.DataFrame, freq: str, sport: str) -> pd.DataFrame:
    # copied from strava V1: activityStats2.py
    """
    Perform GROUP BY aggregation for time_freq (month, week, quarter, year) and type.

    For sport == ALL only count is performed
    else all aggregations are performed
    """
    assert freq in ("Year", "Quarter", "Month", "Week"), freq

    if sport != "ALL":
        df = df[df["type"] == sport]
        aggregations = AGGREGATIONS
    else:
        aggregations = {"Count": "count"}
        sport = "Run"

    # reduce to relevant columns
    df = df[
        [
            "type",
            "id",  # this we use for count
            "x_year",
            "x_quarter",
            "x_month",
            "x_week",
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
            "x_year": "year",
            "x_quarter": "quarter",
            "x_month": "month",
            "x_week": "week",
            "x_min": "Hour-sum",
            "x_km": "Kilometer-sum",
            "total_elevation_gain": "Elevation-sum",
            "x_elev_%": "Elevation%-avg",
            "x_km/h": "Speed_km/h-avg",
            "average_heartrate": "Heartrate-avg",
        },
    )
    year_min, year_max = df["year"].min(), df["year"].max()

    # add some more columns
    df["Hour-sum"] = df["Hour-sum"] / 60
    df["Hour-avg"] = df["Hour-sum"]
    df["Kilometer-avg"] = df["Kilometer-sum"]
    df["Elevation-avg"] = df["Elevation-sum"]
    df["Speed_km/h-max"] = df["Speed_km/h-avg"]
    df["Heartrate-max"] = df["Heartrate-avg"]

    if freq == "Week":
        df2 = df.groupby(["year", "week", "type"]).agg(aggregations)
        # add missing values
        df3 = generate_empty_df(
            sport=sport, freq=freq, year_min=year_min, year_max=year_max
        )
        df2 = add_data_and_empty_df(df2, df3)
        # same str column for each freq
        df2[freq] = df2["year"].astype(str) + "-" + df2["week"].astype(str).str.zfill(2)
        df2 = df2.drop(columns=["year", "week"])

    elif freq == "Month":
        df2 = df.groupby(["year", "month", "type"]).agg(aggregations)
        # add missing values
        df3 = generate_empty_df(
            sport=sport, freq=freq, year_min=year_min, year_max=year_max
        )
        df2 = add_data_and_empty_df(df2, df3)
        df2[freq] = (
            df2["year"].astype(str) + "-" + df2["month"].astype(str).str.zfill(2)
        )
        df2 = df2.drop(columns=["year", "month"])

    elif freq == "Quarter":
        df2 = df.groupby(["year", "quarter", "type"]).agg(aggregations)
        # add missing values
        df3 = generate_empty_df(
            sport=sport, freq=freq, year_min=year_min, year_max=year_max
        )
        df2 = add_data_and_empty_df(df2, df3)
        df2[freq] = df2["year"].astype(str) + "-Q" + df2["quarter"].astype(str)
        df2 = df2.drop(columns=["year", "quarter"])

    elif freq == "Year":
        df2 = df.groupby(["year", "type"]).agg(aggregations)
        df3 = pd.DataFrame(
            {"year": range(year_min, year_max + 1), "type": sport, "Count": 0}
        ).set_index(["year", "type"])
        df2 = add_data_and_empty_df(df2, df3)
        df2["year"] = df2["year"].astype(str)
        df2 = df2.reset_index().rename(columns={"year": freq})

    # rounding
    for measure in AGGREGATIONS:
        if measure in df2.columns:
            if measure in (
                "Count",
                "Elevation-sum",
                "Elevation-avg",
                "Heartrate-avg",
                "Heartrate-max",
            ):
                df2[measure] = df2[measure].round(0).astype(int)
            else:
                df2[measure] = df2[measure].round(1)
    return df2


df = cache_all_activities_and_gears()[0]

col1, col2, col3, col4 = st.columns((1, 1, 3, 1))

sel_freq = col1.selectbox(
    label="Frequency", options=("Year", "Quarter", "Month", "Week")
)

year_min, year_max = df["x_year"].min(), df["x_year"].max()

sel_year = col3.slider(
    "Year",
    min_value=year_min,
    max_value=year_max if year_max != year_min else year_min + 1,
    value=(df["x_year"].min(), df["x_year"].max()),
    key="sel_year",
)
if sel_year:
    df = df.query("x_year >= @sel_year[0] and x_year <= @sel_year[1]")


st.header(f"All Activity {sel_freq} Count")
df2 = activity_stats_grouping(df, freq=sel_freq, sport="ALL")

# date_axis_type = "N" if sel_freq in ("Year", "Quarter") else "T"
date_axis_type = ":N"

c = (
    alt.Chart(
        df2,
        title=alt.TitleParams(f"Strava Stats: All Activity {sel_freq} Count"),
    )
    .mark_bar()
    .encode(
        x=alt.X(sel_freq + date_axis_type, title=None),
        y=alt.Y("Count:Q", title=None),
        color="type:N",
    )
)
st.altair_chart(c, use_container_width=True)


df2b = (
    df2.pivot_table(index=sel_freq, columns="type", values="Count", aggfunc="first")
    .sort_index(ascending=False)
    .reset_index()
)
df2b = reorder_cols(df2b, [sel_freq, "Run", "Ride", "Swim", "Hike"])
st.dataframe(df2b, hide_index=True)

st.header("Per Sport")
col1, col2, col3, col4 = st.columns((1, 1, 1, 3))

sel_type = select_sport(df, col1, mandatory=True)
assert sel_type is not None

sel_agg = col2.selectbox(
    label="Aggregation",
    options=AGGREGATIONS.keys(),
)

df2 = activity_stats_grouping(df, freq=sel_freq, sport=sel_type).drop(columns="type")

c = (
    alt.Chart(
        df2,
        title=alt.TitleParams(f"Strava Stats: {sel_type} {sel_freq} {sel_agg}"),
    )
    .mark_bar()
    .encode(
        x=alt.X(sel_freq + date_axis_type, title=None),
        y=alt.Y(sel_agg + ":Q", title=None),
        tooltip=[
            alt.Tooltip(sel_freq + date_axis_type, title="Date"),
            alt.Tooltip(sel_agg + ":Q"),
            alt.Tooltip("Count:Q"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)

column_order = [sel_freq]
column_order.extend(AGGREGATIONS.keys())

title = f"{sel_type} per {sel_freq}"
st.header(title)
st.dataframe(
    df2.sort_values(sel_freq, ascending=False),
    hide_index=True,
    column_order=column_order,
)
excel_download_buttons(
    df2[column_order], file_name=f"Strava {title}.xlsx", exclude_index=True
)

st.header("Active Days")
sel_types = st.multiselect(label="Sport", options=list_sports(df))
if sel_types:
    df = df.query("type in @sel_types")

year_min, year_max = df["x_year"].min(), df["x_year"].max()

df3 = (
    df[["x_year", "x_date"]]
    .drop_duplicates()
    .groupby("x_year")
    .agg({"x_date": "count"})
    .rename(columns={"x_date": "Count"})
    .reindex(range(year_min, year_max + 1), fill_value=0)
    .reset_index()
)
# st.write(df3)
c = (
    alt.Chart(df3)
    .mark_bar()
    .encode(
        x=alt.X("x_year:N", title=None),
        y=alt.Y("Count:Q", title=None),
        tooltip=[
            alt.Tooltip("x_year:N", title="Year"),
            alt.Tooltip("Count:Q", title="Count"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)
# st.write(df2)

logger.info("End")
