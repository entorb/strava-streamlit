"""Activity List and Excel Export."""

import datetime as dt
import json
from math import isnan

import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    get_act_desc_cache_file_path,
    refresh_activities_cache,
)
from helper_api import StravaRateLimitError, fetch_activity_description
from helper_logging import get_logger_from_filename
from helper_ui_components import excel_download_buttons, select_sport, select_years

_LOGGER = get_logger_from_filename(__file__)


def next_rate_limit_reset(now: dt.datetime) -> dt.datetime:
    """
    Return the next time Strava's 15-min rate-limit window resets.

    Strava's short-term limit resets at :00/:15/:30/:45; a few seconds of buffer
    are added to account for clock skew.
    """
    base = now.replace(second=0, microsecond=0)
    minutes_to_next = 15 - (now.minute % 15)
    return base + dt.timedelta(minutes=minutes_to_next, seconds=5)


def _load_descriptions() -> dict[int, str]:
    p = get_act_desc_cache_file_path()
    three_months_ago = dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=90)
    # sweep all cached description files older than 3 months
    for f in p.parent.glob("*.json"):
        if dt.datetime.fromtimestamp(f.stat().st_mtime, tz=dt.UTC) < three_months_ago:
            f.unlink()
    if not p.exists():
        return {}
    return {int(k): v for k, v in json.loads(p.read_text()).items()}


def _save_descriptions(descriptions: dict[int, str]) -> None:
    p = get_act_desc_cache_file_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(descriptions, ensure_ascii=False))


@st.fragment(run_every="10s")
def description_retry_status(ids: list[int]) -> None:
    """Show fetch progress and a Retry button that re-enables after the cooldown."""
    descriptions: dict[int, str] = _load_descriptions()
    total = len(ids)
    fetched = sum(1 for i in ids if i in descriptions)
    cooldown_until = st.session_state.get("desc_cooldown_until")
    now = dt.datetime.now(tz=dt.UTC)
    if cooldown_until is not None and now < cooldown_until:
        mins, secs = divmod(int((cooldown_until - now).total_seconds()), 60)
        st.warning(
            f"Strava API rate limit reached: {fetched} of {total} descriptions "
            f"fetched. Retry available in {mins:02d}:{secs:02d}."
        )
        st.button("Retry fetch", disabled=True)
    else:
        st.info(f"{fetched} of {total} descriptions fetched, some are still missing.")
        if st.button("Retry fetch"):
            st.rerun()


def fetch_and_attach_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch missing activity descriptions and add them as the x_description column.

    Descriptions persist in a JSON file (per user) and are pruned after 3 months.
    On hitting the rate limit, fetching pauses until the next Strava reset; the
    retry status/button is rendered by description_retry_status().
    """
    user_id = st.session_state["USER_ID"]
    descriptions: dict[int, str] = _load_descriptions()
    ids = [int(i) for i in df.index]
    total = len(ids)

    now = dt.datetime.now(tz=dt.UTC)
    cooldown_until = st.session_state.get("desc_cooldown_until")
    in_cooldown = cooldown_until is not None and now < cooldown_until

    missing = [i for i in ids if i not in descriptions]
    if missing and not in_cooldown:
        rate_limited = False
        progress = st.progress(0.0, text="Fetching activity descriptions ...")
        for n, activity_id in enumerate(missing):
            try:
                descriptions[activity_id] = fetch_activity_description(
                    activity_id=activity_id, user_id=user_id
                )
            except StravaRateLimitError:
                rate_limited = True
                st.session_state["desc_cooldown_until"] = next_rate_limit_reset(
                    dt.datetime.now(tz=dt.UTC)
                )
                break
            progress.progress((n + 1) / len(missing))
        progress.empty()
        _save_descriptions(descriptions)
        if not rate_limited:
            st.session_state.pop("desc_cooldown_until", None)

    df = df.copy()
    df["x_description"] = [descriptions.get(i, "") for i in ids]

    fetched = sum(1 for i in ids if i in descriptions)
    if fetched < total:
        description_retry_status(ids)
    else:
        st.success(f"All {total} activity descriptions fetched.")
    return df


def main() -> None:  # noqa: C901, D103, PLR0912, PLR0915
    st.markdown("Edit at [Strava](https://www.strava.com/athlete/training)")

    cols = st.columns((1, 5))
    select_years(cols[0])

    df, df_gear = cache_all_activities_and_gears()

    min_year = df["x_year"].min()
    max_year = df["x_year"].max()
    if min_year == max_year:
        max_year += 1

    def reset_filters() -> None:
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
        sel_km = col4.slider(
            "Kilometer", min_value=0, max_value=max_value, key="sel_km"
        )
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

    fetch_desc = st.checkbox(
        "Fetch activity descriptions too"
        f" ({len(df)} activities, 1 Strava API call each, may be slow,"
        " cached for 3 months to reduce API calls.)",
        value=False,
    )
    if fetch_desc:
        df = fetch_and_attach_descriptions(df)

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
    excel_download_buttons(
        df=df, file_name="Strava_Activity_List.xlsx", exclude_index=True
    )

    if st.button("Re-Fetch from Strava", help="Re-fetch activities from Strava"):
        refresh_activities_cache()
        st.rerun()

    st.header("Gear")
    st.dataframe(df_gear)


if __name__ == "__main__":
    main()
