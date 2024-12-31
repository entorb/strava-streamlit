"""Helper: Pandas."""

import pandas as pd

from helper_logging import get_logger_from_filename

logger = get_logger_from_filename(__file__)


def reorder_cols(df: pd.DataFrame, col_first: list[str]) -> pd.DataFrame:
    """Reorder DataFrame columns, put col_first to beginning."""
    cols = df.columns.to_list()
    for col in col_first:
        if col in cols:
            cols.remove(col)
        else:
            logger.warning(f"'{col}' not in columns: {df.columns.to_list()} ")  # noqa: G004
    col_first.extend(cols)
    return df[col_first]
