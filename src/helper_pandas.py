"""Helper: Pandas."""

import pandas as pd

from helper_logging import get_logger_from_filename

logger = get_logger_from_filename(__file__)


def reorder_cols(df: pd.DataFrame, col_first: list[str]) -> pd.DataFrame:
    """Reorder DataFrame columns, put col_first to beginning."""
    cols = df.columns.to_list()
    for col in reversed(col_first):
        if col not in cols:
            col_first.remove(col)
    for col in col_first:
        if col in cols:
            cols.remove(col)
    col_first.extend(cols)
    return df[col_first]
