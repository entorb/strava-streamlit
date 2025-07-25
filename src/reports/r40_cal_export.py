"""Calendar Export."""

import datetime as dt
import io

import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename, track_function_usage

st.title(__doc__[:-1])  # type: ignore
logger = get_logger_from_filename(__file__)


@track_function_usage
def gen_ics(df: pd.DataFrame) -> str:
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

    for row in df.itertuples():
        assert type(row.start_date_local) is pd.Timestamp, type(row.start_date_local)
        assert type(row.utc_offset) is int, type(row.utc_offset)
        assert type(row.elapsed_time) is int, type(row.elapsed_time)
        assert type(row.x_min) is float, type(row.x_min)

        # note I renamed Strava field start_date_local to start_date
        start_date = row.start_date_local - dt.timedelta(seconds=row.utc_offset)
        end_date = start_date + dt.timedelta(seconds=row.elapsed_time)
        start_date_str = start_date.strftime("%Y%m%dT%H%M%SZ")
        end_date_str = end_date.strftime("%Y%m%dT%H%M%SZ")

        location = row.x_nearest_city_start or "unknown"
        for col in ("location_city", "location_state", "location_country"):
            if getattr(row, col):
                location += "," + getattr(row, col)
        # cspell:disable
        cont += f"""BEGIN:VEVENT
UID:strava-id-{row.id}
TRANSP:OPAQUE
DTSTART:{start_date_str}
DTEND:{end_date_str}
CREATED:{end_date_str}
LAST-MODIFIED:{date_str_now}
DTSTAMP:{date_str_now}
SUMMARY:{row.type}: {row.name} ({round(row.x_min)} min) (Strava)
LOCATION:{location}
URL;VALUE=URI:{row.x_url}
DESCRIPTION:open at Strava: {row.x_url}\\n\\ngenerated via https://entorb.net/strava/
SEQUENCE:0
END:VEVENT
"""  # cspell:enable

    cont += ics_footer
    return cont


file_name = "Strava_Activity_Calendar.ics"
df = cache_all_activities_and_gears()[0]

col1, col2, _ = st.columns((1, 1, 6))
if col1.button(label="ICS Prepare"):
    buffer = io.BytesIO()
    buffer.write(gen_ics(df).encode("utf-8"))
    buffer.seek(0)

    col2.download_button(
        label="ICS Download",
        data=buffer,
        file_name=file_name,
        mime="text/calendar",
    )
    # Path("/tmp/ActivityList.ics").write_text(cont)
