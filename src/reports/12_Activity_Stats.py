"""Activity Stats."""

import datetime as dt

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
def reduce_and_rename_activity_df(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce activity DataFrame to relevant columns."""
    # reduce
    df = df[
        [
            "type",
            "x_date",
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

    # rename
    df = df.rename(
        columns={
            "x_year": "year",
            "x_quarter": "quarter",
            "x_month": "month",
            "x_week": "week",
            "x_date": "date",
            "x_min": "Hour-sum",
            "x_km": "Kilometer-sum",
            "total_elevation_gain": "Elevation-sum",
            "x_elev_%": "Elevation%-avg",
            "x_km/h": "Speed_km/h-avg",
            "average_heartrate": "Heartrate-avg",
        },
    )

    # add count
    df["Count"] = 0

    # add some more columns
    df["Hour-sum"] = df["Hour-sum"] / 60
    df["Hour-avg"] = df["Hour-sum"]
    df["Kilometer-avg"] = df["Kilometer-sum"]
    df["Elevation-avg"] = df["Elevation-sum"]
    df["Speed_km/h-max"] = df["Speed_km/h-avg"]
    df["Heartrate-max"] = df["Heartrate-avg"]
    return df


@track_function_usage
def generate_empty_df(
    sport: str, freq: str, year_min: int, year_max: int, aggregation_name: str
) -> pd.DataFrame:
    """Generate and empty DataFrame with year, freq and type as index."""
    assert freq in ("Quarter", "Month", "Week")

    field = freq.lower()

    # single value df
    df = pd.DataFrame(
        data={
            "year": [year_min],
            field: 1,
            "type": sport,
            aggregation_name: 0,
        }
    ).set_index(["year", field, "type"])

    # sub-level range
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


@track_function_usage
def add_data_and_empty_df(
    df2: pd.DataFrame, df3: pd.DataFrame, aggregation_name: str
) -> pd.DataFrame:
    """
    Add empty DataFrame to real data.

    Both have a 3-fold index: year, freq, type
    """
    df2 = df2.add(df3, fill_value=0)
    # trim ends, maybe via
    first_idx = df2[df2[aggregation_name] > 0].index[0]
    last_idx = df2[df2[aggregation_name] > 0].index[-1]
    df2 = df2.loc[first_idx:last_idx]

    df2 = df2.fillna(0).reset_index()
    return df2


@track_function_usage
def activity_stats_grouping(
    df: pd.DataFrame, freq: str, sport: str, aggregation: str
) -> pd.DataFrame:
    # copied from strava V1: activityStats2.py
    """
    Perform GROUP BY aggregation for time_freq (month, week, quarter, year) and type.

    For sport == ALL only count is performed
    else all aggregations are performed
    """
    assert freq in ("Year", "Quarter", "Month", "Week"), freq

    if sport != "ALL":
        # if not ALL sports, filter on one sport
        df = df[df["type"] == sport]
    else:  # ALL
        sport = "Run"

    if aggregation != "ALL":
        agg = {aggregation: AGGREGATIONS[aggregation]}
        aggregation_name = aggregation
    else:  # ALL
        agg = AGGREGATIONS
        aggregation_name = "Count"

    year_min, year_max = df["year"].min(), df["year"].max()

    if freq == "Week":
        df2 = df.groupby(["year", "week", "type"]).agg(agg)
        # add missing values
        df3 = generate_empty_df(
            sport=sport,
            freq=freq,
            year_min=year_min,
            year_max=year_max,
            aggregation_name=aggregation_name,
        )
        df2 = add_data_and_empty_df(df2, df3, aggregation_name=aggregation_name)
        # same str column for each freq
        df2[freq] = df2["year"].astype(str) + "-" + df2["week"].astype(str).str.zfill(2)
        df2["date"] = pd.to_datetime(
            df2.apply(
                lambda row: dt.date.fromisocalendar(row["year"], row["week"], 1), axis=1
            )
        )
        df2 = df2.drop(columns=["year", "week"])

    elif freq == "Month":
        df2 = df.groupby(["year", "month", "type"]).agg(agg)
        # add missing values
        df3 = generate_empty_df(
            sport=sport,
            freq=freq,
            year_min=year_min,
            year_max=year_max,
            aggregation_name=aggregation_name,
        )
        df2 = add_data_and_empty_df(df2, df3, aggregation_name=aggregation_name)
        df2[freq] = (
            df2["year"].astype(str) + "-" + df2["month"].astype(str).str.zfill(2)
        )
        df2["date"] = pd.to_datetime(
            df2.apply(
                lambda row: dt.date(row["year"], row["month"], 1),
                axis=1,
            )
        )
        df2 = df2.drop(columns=["year", "month"])

    elif freq == "Quarter":
        df2 = df.groupby(["year", "quarter", "type"]).agg(agg)
        # add missing values
        df3 = generate_empty_df(
            sport=sport,
            freq=freq,
            year_min=year_min,
            year_max=year_max,
            aggregation_name=aggregation_name,
        )
        df2 = add_data_and_empty_df(df2, df3, aggregation_name=aggregation_name)
        df2[freq] = df2["year"].astype(str) + "-Q" + df2["quarter"].astype(str)
        df2["date"] = pd.to_datetime(
            df2.apply(
                lambda row: dt.date(row["year"], 3 * row["quarter"] - 2, 1),
                axis=1,
            )
        )
        df2 = df2.drop(columns=["year", "quarter"])

    elif freq == "Year":
        df2 = df.groupby(["year", "type"]).agg(agg)
        df3 = pd.DataFrame(
            {"year": range(year_min, year_max + 1), "type": sport, aggregation_name: 0}
        ).set_index(["year", "type"])
        df2 = add_data_and_empty_df(df2, df3, aggregation_name=aggregation_name)
        df2["date"] = df2.apply(
            lambda row: dt.date(row["year"], 1, 1),
            axis=1,
        )
        df2["year"] = df2["year"].astype(str)
        df2 = df2.rename(columns={"year": freq})  # capitalization

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
    df2 = df2.rename(columns={"type": "Sport"})
    df2 = reorder_cols(df=df2, col_first=[freq, "Sport"])
    return df2


df = cache_all_activities_and_gears()[0]
df = reduce_and_rename_activity_df(df)

col1, col2, col3, col4 = st.columns((1, 1, 3, 1))

sel_freq = col1.selectbox(
    label="Frequency", options=("Year", "Quarter", "Month", "Week")
)

year_min, year_max = df["year"].min(), df["year"].max()

sel_year = col3.slider(
    "Year",
    min_value=year_min,
    max_value=year_max if year_max != year_min else year_min + 1,
    value=(df["year"].min(), df["year"].max()),
    key="sel_year",
)
if sel_year:
    df = df.query("year >= @sel_year[0] and year <= @sel_year[1]")


st.header(f"All Activity {sel_freq} Count")
aggregation = "Count"
df2 = activity_stats_grouping(df, freq=sel_freq, sport="ALL", aggregation=aggregation)

# date_axis_type = "N" if sel_freq in ("Year", "Quarter") else "T"
date_axis_type = ":N"

# TODO: to streamlit-examples
# altair time units https://altair-viz.github.io/user_guide/transform/timeunit.html
if sel_freq == "Year":
    time_unit = "year(date):T"
elif sel_freq == "Quarter":
    time_unit = "yearquarter(date):T"
elif sel_freq == "Month":
    time_unit = "yearmonth(date):T"
elif sel_freq == "Week":
    time_unit = "date:T"

c = (
    alt.Chart(
        df2,
        title=alt.TitleParams(f"Strava Stats: All Activity {sel_freq} Count"),
    )
    .mark_bar()
    .encode(
        x=alt.X(time_unit, title=None),
        y=alt.Y(f"{aggregation}:Q", title=None),
        color="Sport:N",
        tooltip=[
            # alt.Tooltip(time_unit, title="Date"),
            alt.Tooltip(sel_freq),
            alt.Tooltip("Sport:N"),
            alt.Tooltip(f"{aggregation}:Q"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)


df2b = (
    df2.pivot_table(index=sel_freq, columns="Sport", values="Count", aggfunc="first")
    .sort_index(ascending=False)
    .reset_index()
)
df2b = reorder_cols(df2b, [sel_freq, "Run", "Ride", "Swim", "Hike"])
st.dataframe(df2b, hide_index=True)


st.header("Compare to Previous Period")
col1, _ = st.columns((1, 5))
sel_agg = col1.selectbox(
    label="Aggregation",
    options=AGGREGATIONS.keys(),
)

df2c = (
    activity_stats_grouping(df, freq=sel_freq, sport="ALL", aggregation=sel_agg)
    .drop(columns=["date"])
    .sort_values([sel_freq, "Sport"], ascending=(False, True))
)


def get_cell(df: pd.DataFrame, sport: str, period: str, agg: str) -> float | int:
    """Extract a cell."""
    df2 = df[(df[sel_freq] == period) & (df["Sport"] == sport)]
    lst = df2[agg].head(1).to_list()
    if len(lst) == 0:
        return 0
    return lst[0]


periods = df2c[sel_freq].unique()[:4]

cols = st.columns(4)
sports = ["Run", "Ride", "Swim", "Hike"]
for i in range(4):
    col = cols[i]
    sport = sports[i]
    col.subheader(sport)
    cur = get_cell(df=df2c, sport=sport, period=periods[0], agg=sel_agg)
    if len(periods) > 1:
        prev1 = get_cell(df=df2c, sport=sport, period=periods[1], agg=sel_agg)
    else:
        prev1 = 0
    if len(periods) > 2:  # noqa: PLR2004
        prev2 = get_cell(df=df2c, sport=sport, period=periods[2], agg=sel_agg)
    if len(periods) > 3:  # noqa: PLR2004
        prev3 = get_cell(df=df2c, sport=sport, period=periods[3], agg=sel_agg)
    else:
        prev3 = 0
    col.metric(label=periods[0], value=cur)
    if len(periods) > 1:
        col.metric(label=periods[1], value=prev1, delta=round(prev1 - prev2, 1))
    if len(periods) > 2:  # noqa: PLR2004
        col.metric(label=periods[2], value=prev2)
        # col.metric(label=periods[2], value=prev2, delta=round(prev2 - prev3, 1))


# st.dataframe(df, hide_index=True)


st.header("Per Sport")
col1, _ = st.columns((1, 5))

sel_type = select_sport(df, col1, mandatory=True)
assert sel_type is not None


# df2 has 1 sport and all aggregations
df2 = activity_stats_grouping(
    df, freq=sel_freq, sport=sel_type, aggregation="ALL"
).drop(columns="Sport")

c = (
    alt.Chart(
        df2,
        title=alt.TitleParams(f"Strava Stats: {sel_type} {sel_freq} {sel_agg}"),
    )
    .mark_bar()
    .encode(
        x=alt.X(time_unit, title=None),
        y=alt.Y(f"{sel_agg}:Q", title=None),
        tooltip=[
            alt.Tooltip(sel_freq),
            alt.Tooltip(f"{sel_agg}:Q"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)

column_order = [sel_freq]  # date frequency
column_order.extend(AGGREGATIONS.keys())

title = f"{sel_type} Stats per {sel_freq}"
st.header(title)
st.dataframe(
    df2.sort_values(sel_freq, ascending=False),
    hide_index=True,
    column_order=column_order,
)
excel_download_buttons(
    df2[column_order],
    file_name=f"Strava {title}.xlsx",
    exclude_index=True,
)


st.header("Active Days")
sel_types = st.multiselect(label="Sport", options=list_sports(df))
if sel_types:
    df = df.query("type in @sel_types")

year_min, year_max = df["year"].min(), df["year"].max()

df3 = (
    df[["year", "date"]]
    .drop_duplicates()
    .groupby("year")
    .count()
    .rename(columns={"date": "Count"})
    .reindex(range(year_min, year_max + 1), fill_value=0)
    .reset_index()
)

df3["date"] = df3.apply(lambda row: dt.date(row["year"], 1, 1), axis=1)

c = (
    alt.Chart(df3)
    .mark_bar()
    .encode(
        x=alt.X("year(date):T", title=None),
        y=alt.Y("Count:Q", title=None),
        tooltip=[
            alt.Tooltip("year", title="Year"),
            alt.Tooltip("Count:Q", title="Active Days"),
        ],
    )
)
st.altair_chart(c, use_container_width=True)

# Add download button
# No because the required lib vl-convert-python is quite huge
# users can screenshot instead.
# if st.button("Download chart as PNG"):
#     buffer = io.BytesIO()
#     c.save(buffer, format="png")
#     btn = st.download_button(
#         label="Download chart as PNG",
#         data=buffer,
#         file_name="chart.png",
#         mime="image/png",
#     )


logger.info("End")
