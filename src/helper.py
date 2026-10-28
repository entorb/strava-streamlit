"""General helper functions."""

import os
from pathlib import Path
from typing import Literal

# unset defaults to PROD: fail safe
_APP_ENV = os.environ.get("APP_ENV", "PROD")
if _APP_ENV not in ("PROD", "Local"):
    msg = f"Invalid APP_ENV: {_APP_ENV!r}, expected 'PROD' or 'Local'"
    raise ValueError(msg)
ENV: Literal["PROD", "Local"] = "PROD" if _APP_ENV == "PROD" else "Local"

if ENV == "Local":
    # when running locally, ensure we have data dirs
    Path("./cache").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
