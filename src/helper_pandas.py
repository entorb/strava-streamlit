"""Helper: Pandas."""

import pandas as pd

from helper_logging import get_logger_from_filename, track_function_usage

LOGGER = get_logger_from_filename(__file__)


@track_function_usage
def reorder_cols(df: pd.DataFrame, col_first: list[str]) -> pd.DataFrame:
    """Reorder DataFrame columns, put col_first to beginning."""
    col_first = col_first.copy()
    cols = df.columns.to_list()
    for col in reversed(col_first):
        if col not in cols:
            col_first.remove(col)
    for col in col_first:
        if col in cols:
            cols.remove(col)
    col_first.extend(cols)
    return df[col_first]
