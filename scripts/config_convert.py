"""Read config.toml, modify and export as config-prod.toml."""  # noqa: INP001

import tomllib
from pathlib import Path

import tomli_w  # pip install tomli-w

p_in = Path(__file__).parent.parent / ".streamlit/config.toml"
p_out = p_in.parent / "config-prod.toml"

with p_in.open("rb") as fh:
    o = tomllib.load(fh)

o["server"]["fileWatcherType"] = "none"
o["server"]["baseUrlPath"] = "/strava-streamlit"
del o["server"]["address"]

with p_out.open("wb") as fh:
    tomli_w.dump(o, fh)
