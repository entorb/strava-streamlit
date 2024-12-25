"""Helper: Caching of Activities."""

# ruff: noqa: PLR2004

import math
from pathlib import Path
from time import time

import pandas as pd
import streamlit as st

from helper_api import fetch_activities_page, fetch_gear_data
from helper_logging import init_logger

logger = init_logger(__file__)

# counter = 0

DIR_SERVER = "/var/www/virtual/entorb/data-web-pages/strava"
DIR_LOCAL = "./data"


def get_data_dir() -> Path:
    """Get date path, dependent on env."""
    return Path(DIR_SERVER if st.session_state["ENV"] == "PROD" else DIR_LOCAL)


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
        # dev debug: only one page
        # if st.session_state["USERNAME"] == "entorb":
        #     break
        # if st.session_state["ENV"] == "DEV":
        #     break
    return lst_all_activities


def geo_distance_haversine(
    start: tuple[float, float], end: tuple[float, float]
) -> float:
    """
    Geo distance via haversine formula.

    see https://en.wikipedia.org/wiki/Haversine_formula
    """
    # if st.session_state["ENV"] == "DEV":
    #     global counter
    #     counter += 1
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
    lng = round(loc[1], digits)
    return lat, lng


# this cache is for 2h, while all others are only for 5min
@st.cache_data(ttl="2h")
def cache_all_activities_and_gears() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Call fetch_all_activities() and convert to DataFrame."""
    t_start = time()
    logger.info("Start fetch_all_activities()")
    df = pd.DataFrame(fetch_all_activities())
    logger.info("End fetch_all_activities() in %.1fs", (time() - t_start))

    # date parsing
    for col in ("start_date", "start_date_local"):
        df[col] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)

    df = df.sort_values("start_date_local", ascending=False)

    # calc additional fields

    df["x_url"] = "https://www.strava.com/activities/" + df["id"].astype(str)

    df["x_start_h"] = round(
        df["start_date_local"].dt.hour
        + df["start_date_local"].dt.minute / 60
        + df["start_date_local"].dt.second / 3600,
        2,
    )
    df["x_date"] = df["start_date_local"].dt.date
    df["x_week"] = df["start_date_local"].dt.isocalendar().week

    df = df.set_index("start_date_local")

    # ensure the relevant columns are present
    for col in (
        "average_speed",
        "moving_time",
        "distance",
        "total_elevation_gain",
        # "start_latlng", # not working, due to magic of list in column
        "end_latlng",
    ):
        if col not in df:
            df[col] = pd.Series()  # dtype='int'
            df[col] = pd.Series()  # dtype='int'

    # m/s -> min/km = 1 / X / 60 * 1000
    # df["x_min/km"] = 1 / df["average_speed"] / 60 * 1000
    df["x_min/km"] = df.apply(
        lambda row: round(1 / row["average_speed"] / 60 * 1000, 2)  # type: ignore
        if row["average_speed"] and row["average_speed"] > 0
        else None,
        axis=1,
    )
    df["x_min/mi"] = df.apply(
        lambda row: round(1 / row["average_speed"] / 60 * 1000 * 1.60934, 2)  # type: ignore
        if row["average_speed"] and row["average_speed"] > 0
        else None,
        axis=1,
    )
    df["km/h"] = round(df["average_speed"] * 3.6, 1)
    df["x_max_km/h"] = round(df["max_speed"] * 3.6, 1)
    df["x_mph"] = round(df["average_speed"] * 3.6 / 1.60934, 1)
    df["x_max_mph"] = round(df["max_speed"] * 3.6 / 1.60934, 1)

    df["x_min"] = round(df["moving_time"] / 60, 2)
    df["x_km"] = round(df["distance"] / 1000, 3)
    df["x_mi"] = round(df["distance"] / 1000 / 1.60934, 3)  # km -> mile

    df["x_elev_m/km"] = round(df["total_elevation_gain"] / df["x_km"], 0)
    df["x_elev_%"] = round(df["total_elevation_gain"] / df["x_km"] / 10, 1)

    # gear
    gear_ids = df["gear_id"].dropna().unique()
    d_id_name = {}
    lst_gear = []
    for gear_id in gear_ids:
        d_gear = fetch_gear_data(gear_id)
        lst_gear.append(d_gear)
        # st.write(d_gear)
        d_id_name[gear_id] = d_gear["name"]
    df_gear = pd.DataFrame(lst_gear).set_index("id").sort_index()
    df["x_gear_name"] = df["gear_id"].map(d_id_name)

    # geo calculations
    t_start = time()
    logger.info("Start geo_calc()")
    df = geo_calc(df)
    logger.info("End geo_calc() in %.1fs", (time() - t_start))

    return df, df_gear


def geo_calc(df: pd.DataFrame) -> pd.DataFrame:
    """Geo distance calculations."""
    # for each row in df, calc new column x_dist_start_end_km via geo_distance_haversine
    #  using values of columns start_latlng and end_latlng if they are not null

    # 1. rounding
    df["start_latlng"] = df.apply(
        lambda row: reduce_geo_precision(tuple(row["start_latlng"]), 4)
        if len(row["start_latlng"]) == 2  # type: ignore
        else None,
        axis=1,
    )
    df["end_latlng"] = df.apply(
        lambda row: reduce_geo_precision(tuple(row["end_latlng"]), 4)
        if len(row["end_latlng"]) == 2  # type: ignore
        else None,
        axis=1,
    )

    # 2 dist start-end
    df["x_dist_start_end_km"] = df.apply(
        lambda row: geo_distance_haversine(
            tuple(row["start_latlng"]), tuple(row["end_latlng"])
        )  # type: ignore
        if row["start_latlng"]
        and row["end_latlng"]
        and len(row["start_latlng"]) == 2
        and len(row["end_latlng"]) == 2
        else None,
        axis=1,
    )

    # 3.1 is start a known location?
    df["x_start_locality"] = df.apply(
        lambda row: check_is_known_location(
            reduce_geo_precision(tuple(row["start_latlng"]), 3)
        )  # type: ignore
        if row["start_latlng"] and len(row["start_latlng"]) == 2
        else None,
        axis=1,
    )
    # 3.2 is end a known location?
    df["x_end_locality"] = df.apply(
        lambda row: check_is_known_location(
            reduce_geo_precision(tuple(row["end_latlng"]), 3)
        )  # type: ignore
        if row["end_latlng"] and len(row["end_latlng"]) == 2
        else None,
        axis=1,
    )

    # 4. search for nearest city
    df["x_nearest_city_start"] = df.apply(
        lambda row: search_closest_city(
            reduce_geo_precision(tuple(row["start_latlng"]), 2)
        )  # type: ignore
        if row["start_latlng"] and len(row["start_latlng"]) == 2
        else None,
        axis=1,
    )

    # if st.session_state["ENV"] == "DEV":
    #     global counter
    #     st.write(counter)
    return df


@st.cache_data(ttl="5m")
def get_known_locations() -> list[tuple[float, float, str]]:
    """Get known locations from global and user stored data."""
    lst_known_locations = [
        # some global hard coded ones
        # TODO: move to config file
        # cspell:disable
        (49.574986, 10.967483, "ER-Schaeffler-SMB"),
        (51.070298, 13.760067, "DD-Alaunpark"),
        (53.330333, 10.138152, "P-MTV-Pattensen"),
        (51.010218, 13.701419, "DD-Robotron"),
        (49.60579, 11.036603, "ER-Meilwald-Handtuchwiese"),
        (49.588036, 11.035357, "ER-ObiKreisel"),
        # cspell:enable
    ]

    user_id = st.session_state["USER_ID"]

    p = get_data_dir() / "knownLocations" / f"{user_id}.txt"
    if p.is_file():
        for line in p.read_text().strip().split("\n"):
            lat, lng, name = line.split(" ", 3)
            lst_known_locations.append((float(lat), float(lng), name))
    return lst_known_locations


@st.cache_data(ttl="5m")
def check_is_known_location(latlng: tuple[float, float]) -> str | None:
    """
    Check if location is known location (dist<750m).

    reduce to max 3 digits to allow for caching
    """
    lat, lng = latlng
    for kl in get_known_locations():
        kl_lat, kl_lon, kl_name = kl
        dist = geo_distance_haversine((lat, lng), (kl_lat, kl_lon))
        if dist < 0.75:
            return kl_name
    return None


# no cache for raw data
def read_city_db() -> list[tuple[float, float, str]]:
    """Read city database."""
    p = get_data_dir() / "city-gps.dat"
    lst = []
    for line in p.read_text().strip().split("\n"):
        if line.startswith("#"):
            continue
        parts = line.split(",", 6)
        if len(parts) == 6:
            continent, country, subdivision, city, lat, lng = parts
        name = f"{continent}-{country}-{subdivision}-{city}".replace(",", "").replace(
            ";", ""
        )
        lst.append((float(lat), float(lng), name))
    return lst


@st.cache_resource
def cities_into_1deg_geo_boxes() -> (  # noqa: C901
    dict[tuple[float, float], list[tuple[float, float, str]]]
):
    """Stack cities into boxes of 1x1 degree for faster lookup."""
    # boxes of 1 degree
    boxes = {}

    for line in read_city_db():
        lat, lng, name = line
        lat0, lng0 = int(lat), int(lng)
        offset = 0.5
        # lat
        lat1 = int(lat - offset)
        if lat1 == lat0:  # same box, so try + instead
            lat1 = int(lat + offset)
            if lat1 == lat0:  # still same box, so city must be at center
                lat1 = None
        if lat1 and (lat1 > 90 or lat1 < -90):
            lat1 = None
        # lon
        lng1 = int(lng - offset)
        if lng1 == lng0:  # same box, so try + instead
            lng1 = int(lng + offset)
            if lng1 == lng0:
                lng1 = None  # still same box, so city must be at center

        if lng1 and (lng1 > 180 or lng1 < -180):
            lng1 = None
        t = (lat0, lng0)
        boxes.setdefault(t, []).append(line)
        if lat1:
            t = (lat1, lng0)
            boxes.setdefault(t, []).append(line)
        if lng1:
            t = (lat0, lng1)
            boxes.setdefault(t, []).append(line)
        if lat1 and lng1:
            t = (lat1, lng1)
            boxes.setdefault(t, []).append(line)

    return boxes


@st.cache_data(ttl="5m")
def search_closest_city(latlng: tuple[float, float]) -> str | None:
    """Search in 1x1 deg box of cities for closest city."""
    boxes = cities_into_1deg_geo_boxes()
    lat, lng = latlng
    latlng = (int(lat), int(lng))
    if latlng not in boxes:
        return None
    closest_city_dist = 999
    closest_city_name = None
    lst = boxes[latlng]
    for line in lst:
        city_lat, city_lng, city_name = line
        dist = geo_distance_haversine((lat, lng), (city_lat, city_lng))
        if dist < closest_city_dist:
            closest_city_dist = dist
            closest_city_name = city_name
    return closest_city_name
