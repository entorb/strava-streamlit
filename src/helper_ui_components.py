"""Helper functions: UI components."""

import io
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from helper_logging import get_logger_from_filename

logger = get_logger_from_filename(__file__)


def create_navigation_menu() -> None:
    """Create and populate navigation menu."""
    lst = []
    for p in sorted(Path("src/reports").glob("*.py")):
        f = p.stem
        t = f[3:].replace("_", " ")
        lst.append(st.Page(page=f"reports/{f}.py", title=t))
    pg = st.navigation(lst)
    pg.run()


def excel_download_buttons(
    df: pd.DataFrame, file_name: str = "ActivityList.xlsx", *, exclude_index: bool
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
                file_name=file_name,
                mime="application/vnd.ms-excel",
            )
    st.columns(1)


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


def select_sport(
    df: pd.DataFrame, location: DeltaGenerator, *, mandatory: bool = False
) -> str | None:
    """Display a selectbox for sport type."""
    options = list_sports(df)
    index = None if mandatory is False else 0
    return location.selectbox("Sport", options=options, key="sel_type", index=index)
