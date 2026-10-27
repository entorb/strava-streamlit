"""General helper functions."""

from pathlib import Path
from typing import Literal

ENV: Literal["PROD", "Local"] = (
    "PROD" if Path("/var/www/virtual/entorb/").is_dir() else "Local"
)

if ENV == "Local":
    # when running locally, ensure we have data dirs
    Path("./cache").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
