"""Helper functions: UI components."""

import io

import pandas as pd
import streamlit as st

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