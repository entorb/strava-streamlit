"""Helper: Pandas."""

import pandas as pd

from helper_logging import get_logger_from_filename, track_function_usage

_LOGGER = get_logger_from_filename(__file__)


@track_function_usage
def reorder_cols(df: pd.DataFrame, col_first: list[str]) -> pd.DataFrame:
    """Reorder DataFrame columns, put col_first to beginning."""
    cols = df.columns.to_list()
    col_first = [col for col in col_first if col in cols]
    cols = [col for col in cols if col not in col_first]
    return df[col_first + cols]
