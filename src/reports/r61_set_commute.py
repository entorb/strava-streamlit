"""Set Commute."""

from zoneinfo import ZoneInfo

import requests
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    refresh_activities_cache,
)
from helper_api import HTTP_TOO_MANY_REQUESTS, HTTP_UNAUTHORIZED, set_commute
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

    if msg := st.session_state.pop("commute_msg", None):
        st.success(msg)

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
            width="stretch",
        )

        selected = edited[edited["select"]]
        if st.form_submit_button("Set Commute", icon=":material/commute:"):
            ids = selected.index.tolist()
            total = len(ids)
            if total:
                updated, failed = set_commute_all(ids)
                if updated:
                    refresh_activities_cache(delete_dev_files=False)
                msg = f"Updated {updated} of {total} activities on Strava."
                if failed:
                    msg += f" Failed: {', '.join(map(str, failed))}"
                st.session_state["commute_msg"] = msg
                st.rerun()


def set_commute_all(ids: list[int]) -> tuple[int, list[int]]:
    """Set commute for ids, continue on errors, stop on rate limit / auth error."""
    bar = st.progress(0)
    updated = 0
    failed = []
    for i, activity_id in enumerate(ids, start=1):
        try:
            set_commute(activity_id)
            updated += 1
        except requests.RequestException as e:
            _LOGGER.exception("set_commute failed for %s", activity_id)
            failed.append(activity_id)
            status = e.response.status_code if e.response is not None else 0
            if status in {HTTP_TOO_MANY_REQUESTS, HTTP_UNAUTHORIZED}:
                failed.extend(ids[i:])  # not attempted
                break
        bar.progress(i / len(ids))
    bar.empty()
    return updated, failed


if __name__ == "__main__":
    main()

# cspell:words: Krav Maga Pendelei Maloche
