"""Helper functions: UI components."""

import io

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from helper_logging import init_logger

logger = init_logger(__file__)


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


def select_sport(
    df: pd.DataFrame, location: DeltaGenerator, *, mandatory: bool = False
) -> str | None:
    """Display a selectbox for sport type."""
    lst = sorted(df["type"].unique())
    options = ["Run", "Ride", "Swim", "Hike"]
    # remove manual selected and missing ones
    for col in reversed(options):
        if col in lst:
            lst.remove(col)
        else:
            options.remove(col)
    options.extend(lst)

    index = None if mandatory is False else 0
    return location.selectbox("Sport", options=options, key="sel_type", index=index)
