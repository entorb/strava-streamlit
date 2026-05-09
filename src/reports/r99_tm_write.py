"""Internal Stats."""

import datetime as dt
from zoneinfo import ZoneInfo

import streamlit as st

from helper_activities_caching import cache_all_activities_and_gears
from helper_api import api_post
from helper_logging import (
    get_logger_from_filename,
)

TZ_DE = ZoneInfo("Europe/Berlin")

_LOGGER = get_logger_from_filename(__file__)

# double check, that this file is only access-able by me
if st.session_state["USER_ID"] != st.secrets["my_user_id"]:
    st.stop()


if "activity:write" not in st.session_state["API_SCOPE"]:
    st.warning("API scope 'activity:write' missing")


def post_activity(  # noqa: PLR0913
    act_type: str,
    name: str,
    date: str,  # "YYYY-MM-DD HH:MM:SS"
    duration: int,  # seconds
    distance: float | None = None,  # meters
    desc: str | None = None,
    commute: int | None = None,
    gear_id: str | None = None,
    elev_gain: int | None = None,
) -> dict:
    """Create a new activity."""
    date = date.replace(" ", "T") + "Z"
    date = date.replace("T00:00:00Z", "T00:00:01Z")
    params = {
        "name": name.strip(),
        "type": act_type,
        "sport_type": act_type,  # do not know why there are 2 fields
        "start_date_local": date,
        "elapsed_time": duration,
        "description": desc.strip() if desc else None,
        "distance": distance or None,
        "commute": commute or None,
        "gear_id": gear_id or None,
        "elev_gain": elev_gain or None,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return api_post("activities", params)


def post_act() -> None:
    """Post a new activity from templates."""
    st.header("Post activity")
    my_sport = st.selectbox("Sport", ["Pendelei", "Maloche", "KravMaga", "KravFit"])

    today = dt.datetime.now(tz=TZ_DE).date()
    last_monday = today - dt.timedelta(days=today.weekday())
    last_thursday = today - dt.timedelta(days=(today.weekday() - 3) % 7)

    # defaults to make Pylance happy
    act_type = "Ride"
    name = "my_sport"
    proposed_datetime = dt.datetime.combine(today, dt.time(7, 30))
    duration = 3600
    distance = None
    commute = None
    gear_id = None
    elev_gain = None

    if my_sport == "KravMaga":
        act_type = "Crossfit"
        name = "Krav Maga @ Level Up Gym"
        proposed_datetime = dt.datetime.combine(last_monday, dt.time(18, 0))
        duration = 3600
    elif my_sport == "KravFit":
        act_type = "Crossfit"
        name = "Krav Fit @ Level Up Gym"
        proposed_datetime = dt.datetime.combine(last_thursday, dt.time(17, 45))
        duration = 3600 + 900
    elif my_sport in ["Pendelei", "Maloche"]:
        cols = st.columns(2)
        act_type = "Ride"
        name = my_sport
        commute = 1
        gear_id = "b6686831"
        proposed_datetime = dt.datetime.combine(today, dt.time(7, 30))

        proposed_distance = 33.0 if my_sport == "Maloche" else 20.0
        distance = cols[0].number_input(
            "KM", step=0.5, min_value=10.0, value=proposed_distance, format="%0.1f"
        )

        proposed_duration = 90 if my_sport == "Maloche" else 70
        duration = (
            cols[1].number_input(
                "Minutes", step=1, min_value=10, value=proposed_duration
            )
            * 60
        )
        if my_sport == "Maloche":
            elev_gain = 90

    sel_datetime = st.datetime_input("Date", value=proposed_datetime)

    if st.button("Submit"):
        resp = post_activity(
            act_type=act_type,
            name=name,
            date=sel_datetime.isoformat(),  # 2026-05-09T17:45:00Z
            duration=int(duration),
            distance=distance * 1000 if distance else distance,  # km -> m
            commute=commute,
            gear_id=gear_id,
            elev_gain=elev_gain,
        )

        st.html(
            f"<h2><a target='_blank' href='https://www.strava.com/activities/{resp['id']}'>View at Strava</a></h2>"  # noqa: E501
        )


def review_city_bike() -> None:
    """City-Bike candidates missing commute flag (or wrong bike)."""
    st.header("City-Bike candidates missing commute flag (or wrong bike)")
    df, _df_gear = cache_all_activities_and_gears()
    df = df.query("type == 'Ride' and gear_id == 'b6686831' and commute == False")

    col_order = ["x_url", "name"]
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_order=col_order,
        column_config={
            # "start_date_local": st.column_config.DateColumn(format=FORMAT_DATETIME),
            # no pinning, as taking too much space on mobile
            # "name": st.column_config.Column(pinned=False),
            "x_url": st.column_config.LinkColumn("ID", display_text=r"/(\d+)$"),
        },
    )


def main() -> None:  # noqa: D103
    post_act()

    review_city_bike()


if __name__ == "__main__":
    main()

# cspell:words: Krav Maga Pendelei Maloche
