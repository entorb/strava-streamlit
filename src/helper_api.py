"""Helper: Strava API communication."""

# ruff: noqa: S101
import json
from pathlib import Path
from time import time

import requests
import streamlit as st

from helper_logging import init_logger

logger = init_logger(__file__)

API_RETRIES = 2
# only used for local development to prevent api calls
DIR_CACHE = Path("./cache/")


# not caching raw data
def _api_get(url: str) -> dict | list:
    """Get data from Strava API."""
    baseurl = "https://www.strava.com/api/v3"
    url = f"{baseurl}/{url}"
    logger.info(url)

    headers = {"Authorization": f"Bearer {st.session_state['TOKEN']}"}

    for attempt in range(API_RETRIES):  # Try once, then retry once if it fails
        try:
            resp = requests.get(url, headers=headers, timeout=(3, 30))
            # Raise HTTPError if HTTP request returns an unsuccessful status code
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            logger.exception("Attempt %i failed", attempt)
            # If it's the last attempt, raise the exception
            if attempt + 1 == API_RETRIES:
                raise
    return []


def read_cache_file(cache_file: Path) -> None | dict | list:
    """Read a json cache file, only used for local dev."""
    if not cache_file.is_file():
        return None
    with cache_file.open(encoding="utf-8") as fh:
        d = json.load(fh)
    return d


def write_cache_file(cache_file: Path, d: dict | list) -> None:
    """Write a json cache file, only used for local dev."""
    with cache_file.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, ensure_ascii=False, sort_keys=False, indent=2)


# no caching, as only performed once upon login
def fetch_athlete_info() -> str:
    """Get athlete ID and username and set in session_state."""
    cache_file = DIR_CACHE / "athlete.json"
    d = None
    if st.session_state["ENV"] == "DEV":
        d = read_cache_file(cache_file)
    if not d:
        d = _api_get(url="athlete")
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=d)
    assert type(d) is dict
    st.session_state["USER_ID"] = d["id"]
    st.session_state["USERNAME"] = d.get("username", "no username")
    return st.session_state["USERNAME"]


# not caching this raw data
def fetch_activities_page(page: int) -> list[dict]:
    """Request a page of 200 activities."""
    cache_file = DIR_CACHE / f"activities-page-{page}.json"
    lst = None
    current_timestamp = int(time())
    if st.session_state["ENV"] == "DEV":
        lst = read_cache_file(cache_file)
    if not lst:
        lst = _api_get(
            url=f"athlete/activities?per_page=200&page={page}&before={current_timestamp}&after=0"
        )
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=lst)
    assert type(lst) is list
    return lst


@st.cache_data(ttl="5m")
def fetch_gear_data(gear_id: int) -> dict:
    """Fetch gear info and return name."""
    cache_file = DIR_CACHE / f"gear-{gear_id}.json"
    d = None
    if st.session_state["ENV"] == "DEV":
        d = read_cache_file(cache_file)
    if not d:
        d = _api_get(url=f"gear/{gear_id}")
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=d)
    assert type(d) is dict
    return d


# not caching this raw data
def fetch_all_activities() -> list[dict]:
    """Loop over fetch_activities_page unless the result is empty."""
    page = 1
    lst_all_activities = []
    while True:
        # st.write(f"Downloading page {page}")
        lst = fetch_activities_page(page=page)
        if len(lst) == 0:
            break
        lst_all_activities.extend(lst)
        page += 1
        # # at dev, only download page 1
        # if st.session_state["ENV"] == "DEV":
        #     break
    return lst_all_activities
