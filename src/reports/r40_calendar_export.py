"""Calendar Export."""

import datetime as dt

import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename, track_function_usage

_LOGGER = get_logger_from_filename(__file__)

FILE_NAME = "Strava_Activity_Calendar.ics"


@track_function_usage
def gen_ics(df: pd.DataFrame) -> str:  # type: ignore[attr-defined,misc]
    """Generate calender in ICS format, dates in UTC."""
    date_str_now = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%dT%H%M%SZ")

    ics_header = """BEGIN:VCALENDAR
CALSCALE:GREGORIAN
VERSION:2.0
X-WR-CALNAME:Strava Activity Export by entorb.net
METHOD:PUBLISH
"""
    ics_footer = "END:VCALENDAR"

    cont = ics_header

    df = df.reset_index()  # id as column

    for row in df.itertuples():  # type: ignore[attr-defined]
        assert type(row.start_date_local) is pd.Timestamp, type(row.start_date_local)  # type: ignore[attr-defined]
        assert type(row.utc_offset) is int, type(row.utc_offset)  # type: ignore[attr-defined]
        assert type(row.elapsed_time) is int, type(row.elapsed_time)  # type: ignore[attr-defined]
        assert type(row.x_min) is float, type(row.x_min)  # type: ignore[attr-defined]

        # note I renamed Strava field start_date_local to start_date
        start_date = row.start_date_local - dt.timedelta(seconds=row.utc_offset)  # type: ignore[attr-defined]
        end_date = start_date + dt.timedelta(seconds=row.elapsed_time)  # type: ignore[attr-defined]
        start_date_str = start_date.strftime("%Y%m%dT%H%M%SZ")
        end_date_str = end_date.strftime("%Y%m%dT%H%M%SZ")

        location = row.x_nearest_city_start or "unknown"  # type: ignore[attr-defined]
        for col in ("location_city", "location_state", "location_country"):
            if getattr(row, col):
                location += "," + getattr(row, col)

        row_id = row.id  # type: ignore[attr-defined]
        row_type = row.type  # type: ignore[attr-defined]
        row_name = row.name  # type: ignore[attr-defined]
        row_x_min = row.x_min  # type: ignore[attr-defined]
        row_x_url = row.x_url  # type: ignore[attr-defined]
        # cspell:disable
        cont += f"""BEGIN:VEVENT
UID:strava-id-{row_id}
TRANSP:OPAQUE
DTSTART:{start_date_str}
DTEND:{end_date_str}
CREATED:{end_date_str}
LAST-MODIFIED:{date_str_now}
DTSTAMP:{date_str_now}
SUMMARY:{row_type}: {row_name} ({round(row_x_min)} min) (Strava)
LOCATION:{location}
URL;VALUE=URI:{row_x_url}
DESCRIPTION:open at Strava: {row_x_url}\\n\\ngenerated via https://entorb.net/strava/
SEQUENCE:0
END:VEVENT
"""  # cspell:enable

    cont += ics_footer
    return cont


def main() -> None:  # noqa: D103
    df = cache_all_activities_and_gears()[0]

    st.download_button(
        label="Download ICS",
        data=gen_ics(df).encode("utf-8"),
        file_name=FILE_NAME,
        mime="text/calendar",
    )


if __name__ == "__main__":
    main()
