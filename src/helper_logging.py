"""Helper: Logging."""

from logging import Logger
from pathlib import Path

from streamlit.logger import get_logger


def get_logger_from_filename(file: str) -> Logger:
    """Return logger using filename name."""
    return get_logger(Path(file).stem)
