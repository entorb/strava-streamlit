"""Helper: Logging."""

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from pathlib import Path

import streamlit as st


def init_logging() -> None:
    """Initialize and and configure the logging."""
    logging.addLevelName(logging.DEBUG, "D")
    logging.addLevelName(logging.INFO, "I")
    logging.addLevelName(logging.WARNING, "W")
    logging.addLevelName(logging.ERROR, "E")
    logging.addLevelName(logging.CRITICAL, "C")
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


def get_logger_from_filename(file: str) -> logging.Logger:
    """Return logger using filename name."""
    page = Path(file).stem
    if page != "main" and not page.startswith("helper_"):
        d = get_page_count()
        d[page] = d.get(page, 0) + 1
    return logging.getLogger(page)


@st.cache_resource
def get_call_stats() -> defaultdict[str, dict[str, int | float]]:
    """Create cached dict of call stats."""
    return defaultdict(lambda: {"calls": 0, "total_time": 0.0})


@st.cache_resource
def get_user_login_count() -> dict[int, int]:
    """Create cached dict of user login count."""
    return {}


@st.cache_resource
def get_page_count() -> dict[str, int]:
    """Create cached dict of pages."""
    return {}


def track_function_usage(func: Callable) -> Callable:
    """Annotation for gathering runtime statistics."""

    @wraps(func)
    def wrapper(*args: tuple, **kwargs: dict):  # noqa: ANN202
        start_time = time.time()
        result = func(*args, **kwargs)  # Call the original function
        end_time = time.time()
        call_stats = get_call_stats()
        call_stats[func.__name__]["calls"] += 1
        call_stats[func.__name__]["total_time"] += end_time - start_time
        return result

    return wrapper
