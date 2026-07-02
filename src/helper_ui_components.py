"""Helper functions: UI components."""

import io
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator
from streamlit.navigation.page import StreamlitPage

from helper_logging import get_logger_from_filename, track_function_usage

_LOGGER = get_logger_from_filename(__file__)


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

        lst.append(st.Page(page=f"reports/{f}.py", title=t))
    pg = st.navigation(lst)
    return pg


@track_function_usage
def excel_download_buttons(
    df: pd.DataFrame, file_name: str, *, exclude_index: bool
) -> None:
    """Show prepare data and download buttons."""
    col1, col2, _ = st.columns((1, 1, 6))
    if col1.button(label="Excel Prepare"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Sheet1", index=not exclude_index)
            writer.close()

            col2.download_button(
                label="Excel Download",
                data=buffer,
                file_name=file_name.replace(" ", "_"),
                mime="application/vnd.ms-excel",
            )
    st.columns(1)


@track_function_usage
def list_sports(df: pd.DataFrame) -> list:
    """Return list of sport types."""
    sports = sorted(df["type"].unique())
    first = ["Run", "Ride", "Swim", "Hike"]
    for col in reversed(first):
        if col in sports:
            sports.remove(col)
        else:
            first.remove(col)
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
_YEARS_VALUE_TO_INDEX = {0: 0, 1: 1, 5: 2, 10: 3}


@track_function_usage
def select_years(location: DeltaGenerator) -> None:
    """
    Display a selectbox to choose how many years of activities to load.

    Stores the selection in st.session_state["years"], which is read by
    cache_all_activities_and_gears().
    """
    if "years" not in st.session_state:
        st.session_state["years"] = 0
    index = _YEARS_VALUE_TO_INDEX.get(st.session_state["years"], 4)
    sel = location.selectbox(label="Years", options=_YEARS_OPTIONS, index=index)
    st.session_state["years"] = _YEARS_LABEL_TO_VALUE[sel]
