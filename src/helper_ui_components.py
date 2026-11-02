"""Helper functions: UI components."""

import io
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import streamlit as st

from helper_logging import get_logger_from_filename, track_function_usage

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.navigation.page import StreamlitPage

_LOGGER = get_logger_from_filename(__file__)

# page file name without rNN_ prefix -> icon, unknown pages get a default icon
_PAGE_ICONS = {
    "load_data": ":material/download:",
    "current_year": ":material/today:",
    "activity_list_and_excel_export": ":material/table_view:",
    "activity_statistics": ":material/bar_chart:",
    "calendar_export": ":material/calendar_month:",
    "known_locations": ":material/location_on:",
    "set_commute": ":material/commute:",
    "excel_import": ":material/upload_file:",
    "contact": ":material/mail:",
    "logout": ":material/logout:",
    "internal_stats": ":material/monitoring:",
    "tm_write": ":material/edit:",
}


@track_function_usage
def create_navigation_menu() -> StreamlitPage:
    """Create and populate navigation menu."""
    lst: list[StreamlitPage] = []
    for p in sorted(Path("src/reports").glob("*.py")):
        f = p.stem
        if f.startswith("_"):
            continue
        t = f[4:].replace("_", " ").title()
        # stats page for debugging only visible for me
        if (
            f.startswith("r99")
            and st.session_state["USER_ID"] != st.secrets["my_user_id"]
        ):
            continue

        icon = _PAGE_ICONS.get(f[4:], ":material/description:")
        lst.append(st.Page(page=f"reports/{f}.py", title=t, icon=icon))
    pg = st.navigation(lst)
    return pg


@track_function_usage
def excel_download_buttons(
    df: pd.DataFrame, file_name: str, *, exclude_index: bool
) -> None:
    """Download Excel — generated on click via callable data."""

    def _make_excel() -> bytes:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:  # type: ignore[arg-type]
            df.to_excel(writer, sheet_name="Sheet1", index=not exclude_index)
        return buffer.getvalue()

    st.download_button(
        label="Download Excel",
        icon=":material/download:",
        data=_make_excel,
        file_name=file_name.replace(" ", "_"),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        on_click="ignore",
    )


@track_function_usage
def list_sports(df: pd.DataFrame) -> list:
    """Return list of sport types."""
    sports = sorted(df["type"].unique())
    first = ["Run", "Ride", "Swim", "Hike"]
    first = [col for col in first if col in sports]
    sports = [col for col in sports if col not in first]
    first.extend(sports)
    return first


@track_function_usage
def select_sport(
    df: pd.DataFrame, location: DeltaGenerator, *, mandatory: bool = False
) -> str | None:
    """Display a selectbox for sport type."""
    options = list_sports(df)
    index = None if mandatory is False else 0
    return location.selectbox(
        label="Sport", options=options, key="sel_type", index=index
    )


# how many years of activities to load, mapped to st.session_state["years"]
_YEARS_OPTIONS = ["Current", "Last", "Last 5", "Last 10", "All"]
_YEARS_LABEL_TO_VALUE = {
    "Current": 0,
    "Last": 1,
    "Last 5": 5,
    "Last 10": 10,
    "All": 100,
}
_YEARS_VALUE_TO_LABEL = {v: k for k, v in _YEARS_LABEL_TO_VALUE.items()}


@track_function_usage
def select_years() -> None:
    """
    Display a segmented control to choose how many years of activities to load.

    Stores the selection in st.session_state["years"], which is read by
    cache_all_activities_and_gears().
    """
    if "years" not in st.session_state:
        st.session_state["years"] = 0
    sel = st.segmented_control(
        label="Years",
        options=_YEARS_OPTIONS,
        default=_YEARS_VALUE_TO_LABEL.get(st.session_state["years"], "All"),
        required=True,
    )
    st.session_state["years"] = _YEARS_LABEL_TO_VALUE[sel]
