"""Helper: Strava API communication."""

# ruff: noqa: S101
from time import time

import requests
import streamlit as st

from helper_logging import init_logger

logger = init_logger(__file__)

API_RETRIES = 2


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


# no caching, as only performed once upon login
def fetch_athlete_info() -> str:
    """Get athlete ID and username and set in session_state."""
    d = _api_get(url="athlete")
    assert type(d) is dict
    st.session_state["USER_ID"] = d["id"]
    st.session_state["USERNAME"] = d.get("username", "no username")
    return st.session_state["USERNAME"]


# not caching this raw data
def fetch_activities_page(page: int) -> list[dict]:
    """Request a page of 200 activities."""
    current_timestamp = int(time())
    lst = _api_get(
        url=f"athlete/activities?per_page=200&page={page}&before={current_timestamp}&after=0"
    )
    assert type(lst) is list
    return lst


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
        # at dev, only download page 1
        if st.session_state["ENV"] == "DEV":
            break
    return lst_all_activities


@st.cache_data(ttl="5m")
def fetch_gear_data(gear_id: int) -> dict:
    """Fetch gear info and return name."""
    d = _api_get(url=f"gear/{gear_id}")
    assert type(d) is dict
    return d
