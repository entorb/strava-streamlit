"""Helper: Caching of Activities."""

# ruff: noqa: PLR2004

import datetime as dt
import json
import math
from getpass import getuser
from pathlib import Path

import pandas as pd
import streamlit as st

from helper import ENV
from helper_api import DIR_CACHE, fetch_all_activities, fetch_gear_data
from helper_logging import get_logger_from_filename, track_function_usage
from helper_pandas import reorder_cols

_LOGGER = get_logger_from_filename(__file__)


DIR_SERVER = Path("/var/www/virtual") / getuser() / "data-web-pages/strava"
DIR_LOCAL = "./data"

# column order for activity DataFrames
COL_ORDER_ACTIVITIES = [
    "x_date",
    "name",
    "type",
    "x_workout_name",
    "x_url",
    "x_dl",
    "start_date_local",
    "x_min",
    "x_km",
    "x_mi",
    "total_elevation_gain",
    "x_elev_%",
    "x_km/h",
    "x_mph",
    "x_max_km/h",
    "x_max_mph",
    "x_min/km",
    "x_min/mi",
    "x_location_start",
    "x_location_end",
    "x_km_start_end",
    "x_nearest_city_start",
    "location_country",
    "x_gear_name",
    "average_heartrate",
    "max_heartrate",
    "average_cadence",
    "average_watts",
    "kilojoules",
    "elev_high",
    "elev_low",
    "average_temp",
]

# TODO: move to config file
# some global hard coded ones
KNOWN_LOCATIONS = [
    # cspell:disable
    (51.070298, 13.760067, "DD-Alaunpark"),
    (53.330333, 10.138152, "P-MTV-Pattensen"),
    (51.010218, 13.701419, "DD-Robotron"),
    (49.60579, 11.036603, "ER-Meilwald-Handtuchwiese"),
    (49.588036, 11.035357, "ER-ObiKreisel"),
    # cspell:enable
]


# gear and description cache files are deleted after this many days without use
FILE_CACHE_DAYS = 90


@track_function_usage
def get_data_dir() -> Path:
    """Get date path, dependent on env."""
    return Path(DIR_SERVER if ENV == "PROD" else DIR_LOCAL)


@track_function_usage
def get_known_locations_file_path() -> Path:  # noqa: D103
    user_id = st.session_state["USER_ID"]
    return get_data_dir() / "knownLocations" / f"{user_id}.txt"


@track_function_usage
def get_act_desc_cache_file_path() -> Path:  # noqa: D103
    user_id = st.session_state["USER_ID"]
    return get_data_dir() / "act-desc" / f"{user_id}.json"


@track_function_usage
def get_gear_cache_file_path(user_id: int) -> Path:  # noqa: D103
    return get_data_dir() / "gear" / f"{user_id}.json"


@track_function_usage
def delete_gear_cache(user_id: int) -> None:
    """Delete this user's gear file and in-memory gear entries, not other users'."""
    p = get_gear_cache_file_path(user_id)
    if p.exists():
        for gear_id in json.loads(p.read_text(encoding="utf-8")):
            fetch_gear_data.clear(gear_id=gear_id, user_id=user_id)
        p.unlink()


@track_function_usage
def fetch_gears_file_cached(gear_ids: list[str], user_id: int) -> dict[str, dict]:
    """
    Return {gear_id: gear} for gear_ids, persisted per user in a JSON file.

    Files unused for FILE_CACHE_DAYS are deleted, so gear renames show up later.
    """
    p = get_gear_cache_file_path(user_id)
    max_age = dt.timedelta(days=FILE_CACHE_DAYS)
    now = dt.datetime.now(tz=dt.UTC)
    for f in p.parent.glob("*.json"):
        if now - dt.datetime.fromtimestamp(f.stat().st_mtime, tz=dt.UTC) > max_age:
            f.unlink()
    gears: dict[str, dict] = {}
    if p.exists():
        p.touch()  # renew expiry on use
        gears = json.loads(p.read_text(encoding="utf-8"))
    missing = [g for g in gear_ids if g not in gears]
    for gear_id in missing:
        gears[gear_id] = fetch_gear_data(gear_id=gear_id, user_id=user_id)
    if missing:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(gears, ensure_ascii=False), encoding="utf-8")
    return {g: gears[g] for g in gear_ids}


# no @track_function_usage on per-row hot paths, overhead
def geo_distance_haversine(
    start: tuple[float, float], end: tuple[float, float]
) -> float:
    """
    Geo distance via haversine formula.

    see https://en.wikipedia.org/wiki/Haversine_formula
    """
    lat1, lon1 = start
    lat2, lon2 = end

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Radius of the Earth in kilometers (mean radius)
    r = 6371.01
    return r * c


def reduce_geo_precision(loc: tuple[float, float], digits: int) -> tuple[float, float]:  # noqa: D103
    lat = round(loc[0], digits)
    lon = round(loc[1], digits)
    return lat, lon


# no caching here, as no user_id in parameters, and since session_state.years may change
@track_function_usage
def cache_all_activities_and_gears() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Set st.session_state["years"] and call cache_all_activities_and_gears_year().
    """
    user_id = st.session_state["USER_ID"]
    if "years" not in st.session_state:
        st.session_state["years"] = 0  # this year
    years = st.session_state["years"]
    # always fetch current year
    df, df_gear = cache_all_activities_and_gears_in_year_range(
        user_id=user_id, year_start=0, year_end=0
    )
    if years > 0:  # previous years as well
        dfs = []
        dfs_gear = []
        dfs.append(df)
        dfs_gear.append(df_gear)
        if years >= 1:
            df2, df_gear2 = cache_all_activities_and_gears_in_year_range(
                user_id=user_id, year_start=1, year_end=0
            )
            dfs.append(df2)
            dfs_gear.append(df_gear2)
        if years >= 5:
            df2, df_gear2 = cache_all_activities_and_gears_in_year_range(
                user_id=user_id, year_start=5, year_end=1
            )
            dfs.append(df2)
            dfs_gear.append(df_gear2)
        if years >= 10:
            df2, df_gear2 = cache_all_activities_and_gears_in_year_range(
                user_id=user_id, year_start=10, year_end=5
            )
            dfs.append(df2)
            dfs_gear.append(df_gear2)
        if years > 10:
            df2, df_gear2 = cache_all_activities_and_gears_in_year_range(
                user_id=user_id, year_start=100, year_end=10
            )
            dfs.append(df2)
            dfs_gear.append(df_gear2)
        # index is id, so concat is safe.
        dfs = [d for d in dfs if not d.empty]
        dfs_gear = [d for d in dfs_gear if not d.empty]
        df = pd.concat(dfs) if dfs else pd.DataFrame()
        if df.empty:
            st.error("No activity data found, please record/upload data at strava.com.")
            st.stop()
        df_gear = pd.concat(dfs_gear) if dfs_gear else pd.DataFrame()
    return df, df_gear


@track_function_usage
def refresh_activities_cache(*, delete_dev_files: bool = True) -> None:
    """
    Clear this user's cached activity lists so the next load re-fetches.

    Gear and per-activity description caches are kept intact (descriptions are
    expensive to re-fetch due to API rate limits).
    delete_dev_files=False: only recompute from local page files, no API calls.
    """
    user_id = st.session_state["USER_ID"]
    # only this user's entries; keep in sync with cache_all_activities_and_gears()
    for year_start, year_end in ((0, 0), (1, 0), (5, 1), (10, 5), (100, 10)):
        cache_all_activities_and_gears_in_year_range.clear(
            user_id=user_id, year_start=year_start, year_end=year_end
        )
    # in DEV the activity-list pages are also cached to disk, remove them too
    if ENV == "Local" and delete_dev_files:
        for p in DIR_CACHE.glob("activities-page-*.json"):
            p.unlink()


# this cache is for 2h, while all others are only for 15min
# caching requires user_id is given as parameter!!!
# max_entries: expired ttl entries are only evicted lazily, so cap to avoid OOM
# 5 year ranges per user -> ~40 users; eviction = refetch = app wide rate limit
@st.cache_data(ttl="2h", max_entries=200, show_spinner="Fetching your activities")
@track_function_usage
def cache_all_activities_and_gears_in_year_range(
    user_id: int,
    year_start: int,
    year_end: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Call fetch_all_activities() and convert to DataFrame.

    year_start=0 -> this year
    year_start=5, year_end=0 -> previous 5 years
    returns 2 DataFrames:
    - Activities using id as index, ordered by start_date_local
    - Gears, using id as index, ordered by index
    """
    _LOGGER.info("cache_all_activities_and_gears_year for user_id=%s", user_id)

    df = pd.DataFrame(fetch_all_activities(year_start=year_start, year_end=year_end))

    # ensure all expected columns are there, even if df is empty
    cont = Path("activity_columns.txt").read_text(encoding="utf-8").strip().split()
    for col in cont:
        if col not in df.columns:
            df[col] = None

    # round elevation gain
    df["total_elevation_gain"] = df["total_elevation_gain"].round(0)

    # set int types (before set_index)
    cols = ["id", "utc_offset", "moving_time", "elapsed_time", "total_elevation_gain"]
    for col in cols:
        df[col] = df[col].astype(int)

    # Replace 0 by None in total_elevation_gain
    df["total_elevation_gain"] = (
        df["total_elevation_gain"].replace(0, None).astype("float64")
    )
    # For Swim, set total_elevation_gain to None
    df.loc[df["type"] == "Swim", "total_elevation_gain"] = None

    # id as index
    df = df.set_index("id")

    # init empty df_gear of minimum columns
    df_gear = pd.DataFrame(columns=["id", "name", "nickname"])  # type: ignore[arg-type]
    df_gear = df_gear.set_index("id")

    if df.empty:
        return (df, df_gear)

    # dropping some columns
    df = df.drop(
        columns=[
            "resource_state",
            "athlete",
            "map",
            "upload_id",
            "upload_id_str",
            "external_id",
            "start_date",
        ]
    )

    # date parsing
    df["start_date_local"] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)
    assert pd.api.types.is_datetime64_dtype(df["start_date_local"]), df[
        "start_date_local"
    ].dtype

    df = df.sort_values("start_date_local", ascending=False)

    df = caching_calc_additional_fields(df)

    # gear
    gears = fetch_gears_file_cached(
        gear_ids=list(df["gear_id"].dropna().unique()), user_id=user_id
    )
    d_id_name = {gear_id: d["name"] for gear_id, d in gears.items()}
    if gears:
        df_gear = pd.DataFrame(list(gears.values())).set_index("id").sort_index()

    # convert gear_id to name
    df["x_gear_name"] = df["gear_id"].map(d_id_name)

    # geo calculations
    df = caching_geo_calc(df)

    df = reorder_cols(df, COL_ORDER_ACTIVITIES)
    return df, df_gear


@track_function_usage
def caching_calc_additional_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate additional fields."""
    df["x_url"] = "https://www.strava.com/activities/" + df.index.astype(str)
    df["x_dl"] = (
        "https://www.strava.com/activities/" + df.index.astype(str) + "/export_original"
    )

    df["x_start_h"] = round(
        df["start_date_local"].dt.hour  # type: ignore
        + df["start_date_local"].dt.minute / 60  # type: ignore
        + df["start_date_local"].dt.second / 3600,  # type: ignore
        2,
    )
    df["x_date"] = df["start_date_local"].dt.date  # type: ignore
    df["x_year"] = df["start_date_local"].dt.year.astype(int)  # type: ignore
    df["x_month"] = df["start_date_local"].dt.month.astype(int)  # type: ignore
    df["x_quarter"] = df["start_date_local"].dt.quarter.astype(int)  # type: ignore
    df["x_week"] = df["start_date_local"].dt.isocalendar().week.astype(int)  # type: ignore
    df.loc[(df["x_week"] == 53) & (df["x_month"] == 1), "x_week"] = 1
    df.loc[(df["x_week"] == 53) & (df["x_month"] == 12), "x_week"] = 52
    assert max(df["x_week"]) <= 52

    # m/s -> min/km = 1 / X / 60 * 1000
    speed = df["average_speed"]
    mask = speed > 0
    df["x_min/km"] = None
    df.loc[mask, "x_min/km"] = (1 / speed[mask] / 60 * 1000).round(2)
    df["x_min/mi"] = None
    df.loc[mask, "x_min/mi"] = (1 / speed[mask] / 60 * 1000 * 1.60934).round(2)
    df["x_km/h"] = (df["average_speed"] * 3.6).round(1)
    df["x_max_km/h"] = (df["max_speed"] * 3.6).round(1)
    df["x_mph"] = (df["average_speed"] * 3.6 / 1.60934).round(1)
    df["x_max_mph"] = (df["max_speed"] * 3.6 / 1.60934).round(1)

    df["x_min"] = (df["moving_time"] / 60).round(1)
    df["x_km"] = (df["distance"] / 1000).round(1)
    df["x_mi"] = (df["distance"] / 1000 / 1.60934).round(1)  # km -> mile

    df["x_elev_%"] = round(df["total_elevation_gain"] / df["x_km"] / 10, 1)

    workout_map = {
        ("Run", 0): "Recovery",
        ("Run", 1): "Race",
        ("Run", 2): "Longrun",
        ("Ride", 11): "Race",
        ("Ride", 12): "Workout",
    }
    # no workout_type for
    # Run:workout
    # Ride:recovery
    # Swim:race
    idx = pd.MultiIndex.from_frame(pd.DataFrame(df[["type", "workout_type"]]))
    df["x_workout_name"] = idx.map(workout_map.get)

    return df


def _round_latlng(latlng: list | None, digits: int) -> tuple[float, float] | None:
    """Round [lat, lng] to digits, None if no GPS (Strava sends [])."""
    if latlng is None or len(latlng) != 2:
        return None
    return reduce_geo_precision((latlng[0], latlng[1]), digits)


@track_function_usage
def caching_geo_calc(df: pd.DataFrame) -> pd.DataFrame:
    """Geo calculations: rounding, start-end distance, known locations, city."""
    # list comprehensions instead of df.apply(axis=1): no per-row Series overhead
    # 1. rounding
    start = [_round_latlng(x, 4) for x in df["start_latlng"]]
    end = [_round_latlng(x, 4) for x in df["end_latlng"]]
    df["start_latlng"] = pd.Series(start, index=df.index, dtype=object)
    df["end_latlng"] = pd.Series(end, index=df.index, dtype=object)

    # 2. dist start-end
    df["x_km_start_end"] = [
        round(geo_distance_haversine(s, e), 1) if s and e else None
        for s, e in zip(start, end, strict=True)
    ]

    # 3. is start/end a known location?
    known_locations = get_known_locations()
    df["x_location_start"] = [
        check_is_known_location(reduce_geo_precision(s, 3), known_locations)
        if s
        else None
        for s in start
    ]
    df["x_location_end"] = [
        check_is_known_location(reduce_geo_precision(e, 3), known_locations)
        if e
        else None
        for e in end
    ]

    # 4. search for nearest city, once per rounded location
    rounded = [reduce_geo_precision(s, 2) if s else None for s in start]
    unique = {r for r in rounded if r}
    cities = load_cities_in_boxes(set().union(*(_boxes_around(*r) for r in unique)))
    city_of = {r: search_closest_city(r, cities) for r in unique}
    df["x_nearest_city_start"] = [city_of[r] if r else None for r in rounded]
    return df


@track_function_usage
def get_known_locations(*, users_only: bool = False) -> list[tuple[float, float, str]]:
    """Get known locations from global and user stored data."""
    # copy: appending must not mutate the global list shared by all users
    lst_known_locations = [] if users_only else list(KNOWN_LOCATIONS)

    p = get_known_locations_file_path()
    if p.is_file():
        for line in p.read_text(encoding="utf-8").strip().split("\n"):
            lat, lon, name = line.split(" ", 2)  # maxsplit=2 gives 3 parts
            lst_known_locations.append((float(lat), float(lon), name))
    return lst_known_locations


def check_is_known_location(
    latlng: tuple[float, float], known_locations: list[tuple[float, float, str]]
) -> str | None:
    """
    Check if location is known location (dist<750m).
    """
    max_distance = 0.75  # 750m

    lat, lon = latlng
    for kl in known_locations:
        kl_lat, kl_lon, kl_name = kl
        # an angle of 0.1 is > 10km, so no calculation needed
        if abs(lat - kl_lat) > 0.1 or abs(lon - kl_lon) > 0.1:
            continue
        dist = geo_distance_haversine((lat, lon), (kl_lat, kl_lon))
        if dist < max_distance:
            return kl_name
    return None


def _box(lat: float, lon: float) -> tuple[int, int]:
    """1x1 degree box of a coordinate."""
    return math.floor(lat), math.floor(lon)


def _boxes_around(lat: float, lon: float) -> set[tuple[int, int]]:
    """Own box and its 8 neighbors, so the closest city across a border is found."""
    b_lat, b_lon = _box(lat, lon)
    return {
        (b_lat + d_lat, b_lon + d_lon) for d_lat in (-1, 0, 1) for d_lon in (-1, 0, 1)
    }


@track_function_usage
def load_cities_in_boxes(
    boxes: set[tuple[int, int]],
) -> dict[tuple[int, int], list[tuple[float, float, str]]]:
    """
    Stream the city DB, keep only cities inside the given 1x1 degree boxes.

    Not cached and not fully loaded: the full DB costs ~30MB RAM, which OOM-killed
    PROD. Only called from the 2h cached activity calculation.
    """
    cities: dict[tuple[int, int], list[tuple[float, float, str]]] = {}
    if not boxes:
        return cities
    with (get_data_dir() / "city-gps.dat").open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split(",")
            if len(parts) != 6:  # skip malformed lines
                continue
            continent, country, subdivision, city, lat_s, lon_s = parts
            lat, lon = float(lat_s), float(lon_s)
            box = _box(lat, lon)
            if box in boxes:
                name = f"{continent}-{country}-{subdivision}-{city}".replace(";", "")
                cities.setdefault(box, []).append((lat, lon, name))
    return cities


def search_closest_city(
    latlng: tuple[float, float],
    cities: dict[tuple[int, int], list[tuple[float, float, str]]],
) -> str | None:
    """Closest city in own and neighbor boxes, cities from load_cities_in_boxes()."""
    candidates = [c for b in _boxes_around(*latlng) for c in cities.get(b, [])]
    if not candidates:
        return None
    return min(candidates, key=lambda c: geo_distance_haversine(latlng, c[:2]))[2]


@track_function_usage
def reduce_and_rename_activity_df_for_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce activity DataFrame to relevant columns for stats.

    VirtualRide -> Ride, Walk -> Hike
    """
    # reduce
    cols = [
        "type",
        "x_date",
        "x_year",
        "x_quarter",
        "x_month",
        "x_week",
        "x_min",
        "x_km",
        "total_elevation_gain",
        "x_elev_%",
        "x_km/h",
        "average_heartrate",
        "max_heartrate",
        "x_max_km/h",
    ]
    df = df.loc[:, cols]

    # rename
    df = df.rename(
        columns={
            "x_year": "year",
            "x_quarter": "quarter",
            "x_month": "month",
            "x_week": "week",
            "x_date": "date",
            "x_min": "Hour-sum",
            "x_km": "Kilometer-sum",
            "total_elevation_gain": "Elevation-sum",
            "x_elev_%": "Elevation%-avg",
            "x_km/h": "Speed_km/h-avg",
            "average_heartrate": "Heartrate-avg",
        },
    )

    # add count
    df["Count"] = 0

    # change
    # VirtualRide to Ride
    # Walk to Hike
    df.loc[df["type"] == "VirtualRide", "type"] = "Ride"
    df.loc[df["type"] == "Walk", "type"] = "Hike"

    # add some more columns
    df["Hour-sum"] = df["Hour-sum"] / 60
    df["Hour-avg"] = df["Hour-sum"]
    df["Kilometer-avg"] = df["Kilometer-sum"]
    df["Elevation-avg"] = df["Elevation-sum"]
    df["Speed_km/h-max"] = df["Speed_km/h-avg"]
    df["Heartrate-max"] = df["Heartrate-avg"]
    return df
