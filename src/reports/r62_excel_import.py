"""Excel Import."""

from zoneinfo import ZoneInfo

import streamlit as st

from helper_activities_caching import cache_all_activities_and_gears
from helper_logging import (
    get_logger_from_filename,
)

TZ_DE = ZoneInfo("Europe/Berlin")

_LOGGER = get_logger_from_filename(__file__)


def main() -> None:
    """Upload activities from Excel."""
    if "activity:write" not in st.session_state["API_SCOPE"]:
        # TODO: sync with r61
        st.warning(
            "API scope 'activity:write' missing. "
            "Please logout and re-login with write permissions (orange button)."
        )
        return

    st.write(
        "Here a list of your Ride activities, filtered on Commute=False for bulk update."  # noqa: E501
    )

    df_gear = cache_all_activities_and_gears()[1].reset_index()[
        ["id", "name", "nickname"]
    ]

    st.dataframe(df_gear, hide_index=True)


if __name__ == "__main__":
    main()

# cspell:words: Krav Maga Pendelei Maloche
