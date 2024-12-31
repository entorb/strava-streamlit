"""Helper: Strava API communication."""

import datetime as dt
import json
from pathlib import Path

import requests
import streamlit as st

from helper_logging import get_logger_from_filename

logger = get_logger_from_filename(__file__)

API_RETRIES = 2
URL_OAUTH = "https://www.strava.com/api/v3/oauth/token"
URL_BASE = "https://www.strava.com/api/v3"
# only used for local development to prevent api calls
DIR_CACHE = Path("./cache/")


def api_post_oauth(code: str) -> dict:
    """Post the code from the oauth2 redirect to retrieve token."""
    d = {
        "client_id": st.secrets["client_id"],
        "client_secret": st.secrets["secret"],
        "code": code,
        "grant_type": "authorization_code",
    }
    resp = requests.post(URL_OAUTH, json=d, timeout=15)
    # st.write(resp.json())
    resp.raise_for_status()
    return resp.json()


def api_post_token_refresh() -> dict:
    """Refresh the oauth2 token."""
    d = {
        "client_id": st.secrets["client_id"],
        "client_secret": st.secrets["secret"],
        "grant_type": "refresh_token",
        "refresh_token": st.session_state["TOKEN_REFRESH"],
    }
    resp = requests.post(URL_OAUTH, json=d, timeout=15)
    # st.write(resp.text)
    resp.raise_for_status()
    return resp.json()


def api_post_deauthorize() -> None:
    """Deauthorize this app from user's strava account."""
    headers = {"Authorization": f"Bearer {st.session_state['TOKEN']}"}
    resp = requests.post(
        "https://www.strava.com/oauth/deauthorize", headers=headers, timeout=15
    )
    resp.raise_for_status()


# not caching raw data
def _api_get(path: str) -> dict | list:
    """Get data from Strava API."""
    path = f"{URL_BASE}/{path}"
    logger.info(path)

    headers = {"Authorization": f"Bearer {st.session_state['TOKEN']}"}

    for attempt in range(API_RETRIES):  # Try once, then retry once if it fails
        try:
            resp = requests.get(path, headers=headers, timeout=(3, 30))
            # Raise HTTPError if HTTP request returns an unsuccessful status code
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            logger.exception("Attempt %i failed", attempt)
            # If it's the last attempt, raise the exception
            if attempt + 1 == API_RETRIES:
                raise
    return []


def read_cache_file(cache_file: str) -> None | dict | list:
    """Read a json cache file, only used for local dev."""
    p = DIR_CACHE / cache_file
    if not p.is_file():
        return None
    with p.open(encoding="utf-8") as fh:
        d = json.load(fh)
    return d


def write_cache_file(cache_file: str, d: dict | list) -> None:
    """Write a json cache file, only used for local dev."""
    p = DIR_CACHE / cache_file
    with p.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, ensure_ascii=False, sort_keys=False, indent=2)


# no caching, as only performed once upon login
def fetch_athlete_info() -> str:
    """
    Get athlete ID and username and set in session_state.

    not used any more, since also included in api_post_oauth()
    """
    cache_file = "athlete.json"
    d = None
    if st.session_state["ENV"] == "DEV":
        d = read_cache_file(cache_file)
    if not d:
        d = _api_get(path="athlete")
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=d)
    assert type(d) is dict
    st.session_state["USER_ID"] = d["id"]
    st.session_state["USERNAME"] = d.get("username", "no username")
    return st.session_state["USERNAME"]


# not caching this raw data
def fetch_activities_page(
    page: int, year: int = 0, after: int = 0, before: int = 0
) -> list[dict]:
    """Request a page of 200 activities."""
    cache_file = f"activities-page-{year}-{page}.json"
    lst = None
    if st.session_state["ENV"] == "DEV":
        lst = read_cache_file(cache_file)

    if lst is None:
        lst = _api_get(
            path=f"athlete/activities?per_page=200&page={page}&before={before}&after={after}"
        )
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=lst)
    assert type(lst) is list
    return lst


# not caching this raw data
def fetch_all_activities(year: int = 0) -> list[dict]:
    """
    Loop over fetch_activities_page unless the result is empty.

    year:0 -> this year
    year:N -> previous N years
    """
    page = 1
    lst_all_activities = []

    date_today = dt.datetime.now(tz=dt.UTC).date()
    if year == 0:
        after = int(
            dt.datetime(date_today.year, 1, 1, 0, 0, 0, tzinfo=dt.UTC).timestamp()
        )
        before = int(dt.datetime.now(tz=dt.UTC).timestamp())
    else:
        after = int(
            dt.datetime(
                date_today.year - year, 1, 1, 0, 0, 0, tzinfo=dt.UTC
            ).timestamp()
        )
        after = max(0, after)  # not negative
        before = int(
            dt.datetime(date_today.year, 1, 1, 0, 0, 0, tzinfo=dt.UTC).timestamp()
        )

    while True:
        # st.write(f"Downloading page {page}")

        lst = fetch_activities_page(page=page, year=year, after=after, before=before)
        if len(lst) == 0:
            break
        lst_all_activities.extend(lst)
        page += 1
        # dev debug: only one page
        # if st.session_state["USERNAME"] == "entorb":
        #     break
        # if st.session_state["ENV"] == "DEV":
        #     break
    return lst_all_activities


@st.cache_data(ttl="15m")
def fetch_gear_data(gear_id: int) -> dict:
    """Fetch gear info and return name."""
    cache_file = f"gear-{gear_id}.json"
    d = None
    if st.session_state["ENV"] == "DEV":
        d = read_cache_file(cache_file)
    if not d:
        d = _api_get(path=f"gear/{gear_id}")
        if st.session_state["ENV"] == "DEV":
            write_cache_file(cache_file, d=d)
    assert type(d) is dict
    return d
