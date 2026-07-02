"""Load Data / Caching of Activities."""

import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
)
from helper_logging import get_logger_from_filename
from helper_ui_components import select_years

_LOGGER = get_logger_from_filename(__file__)


def main() -> None:  # noqa: D103
    col1, _ = st.columns((1, 5))
    select_years(col1)

    df = cache_all_activities_and_gears()[0]

    # export activity_columns
    # lst = sorted(df.columns)
    # Path("activity_columns.txt").write_text("\n".join(lst) + "\n")

    df2 = (
        df[["x_year", "x_url"]]
        .groupby("x_year")
        .count()
        .sort_index(ascending=False)
        .reset_index()
        .rename(columns={"x_year": "year", "x_url": "count"})
    )
    col1.dataframe(
        df2,
        hide_index=True,
        width="stretch",
        column_config={"year": st.column_config.NumberColumn(format="%d")},
    )


if __name__ == "__main__":
    main()
