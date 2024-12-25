"""Helper: Logging."""

# ruff: noqa: S101
from logging import Logger
from pathlib import Path

from streamlit.logger import get_logger


def init_logger(file: str) -> Logger:
    """Return logger using  filename name."""
    return get_logger(Path(file).stem)
