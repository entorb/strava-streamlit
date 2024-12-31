"""Helper: Logging."""

import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from logging import Logger
from pathlib import Path

import streamlit as st
from streamlit.logger import get_logger


def get_logger_from_filename(file: str) -> Logger:
    """Return logger using filename name."""
    return get_logger(Path(file).stem)


# Dictionary to store metrics
@st.cache_resource
def get_call_stats() -> defaultdict[str, dict[str, int | float]]:
    """Create cached dict of call stats."""
    return defaultdict(lambda: {"calls": 0, "total_time": 0.0})


def track_function_usage(func: Callable) -> Callable:
    """Annotation for gathering runtime statistics."""

    @wraps(func)
    def wrapper(*args: tuple, **kwargs: dict):  # noqa: ANN202
        # Gather stats only for me
        if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
            start_time = time.time()
            result = func(*args, **kwargs)  # Call the original function
            end_time = time.time()
            call_stats = get_call_stats()
            call_stats[func.__name__]["calls"] += 1
            call_stats[func.__name__]["total_time"] += end_time - start_time
            return result

        # normal user
        return func(*args, **kwargs)  # Call the original function

    return wrapper
