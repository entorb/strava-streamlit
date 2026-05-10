"""Internal Stats."""

from zoneinfo import ZoneInfo

import streamlit as st

from helper_activities_caching import cache_all_activities_and_gears
from helper_api import set_commute
from helper_logging import (
    get_logger_from_filename,
)

TZ_DE = ZoneInfo("Europe/Berlin")

_LOGGER = get_logger_from_filename(__file__)


def main() -> None:
    """Set commute flag for multiple ride activities."""
    if "activity:write" not in st.session_state["API_SCOPE"]:
        st.warning(
            "API scope 'activity:write' missing. "
            "Please logout and re-login with write permissions (orange button)."
        )
        return

    st.write(
        "Here a list of your Ride activities, filtered on Commute=False for bulk update."  # noqa: E501
    )

    df, _df_gear = cache_all_activities_and_gears()
    df = df.query("type == 'Ride' and commute == False")[
        ["name", "x_gear_name", "x_date", "x_url"]
    ].rename(columns={"x_gear_name": "Bike", "x_date": "Date", "name": "Name"})
    df.insert(0, "select", False)

    with st.form("commute_select"):
        edited = st.data_editor(
            df,
            column_config={
                "select": st.column_config.CheckboxColumn("Select", default=False),
                "x_url": st.column_config.LinkColumn("ID", display_text=r"/(\d+)$"),
            },
            disabled=["Name", "Date", "x_url", "Bike"],
            hide_index=True,
            use_container_width=True,
        )

        selected = edited[edited["select"]]
        if st.form_submit_button("Set Commute"):
            ids = selected.index.tolist()
            total = len(ids)
            if total:
                bar = st.progress(0)
                for i, activity_id in enumerate(ids, start=1):
                    set_commute(activity_id)
                    bar.progress(i / total)
                bar.empty()  # remove bar when done, or replace with success message
                st.success(f"Updated {total} activity/activities on Strava.")
                st.info("Data here is cached for 2h, so now outdated.")


if __name__ == "__main__":
    main()

# cspell:words: Krav Maga Pendelei Maloche
