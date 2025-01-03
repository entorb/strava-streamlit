"""Helper: Caching of Activities."""

# ruff: noqa: PLR2004

import math
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from helper_api import fetch_all_activities, fetch_gear_data
from helper_logging import get_logger_from_filename, track_function_usage

logger = get_logger_from_filename(__file__)

# counter = 0

DIR_SERVER = "/var/www/virtual/entorb/data-web-pages/strava"
DIR_LOCAL = "./data"


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


@track_function_usage
def get_data_dir() -> Path:
    """Get date path, dependent on env."""
    return Path(DIR_SERVER if st.session_state["ENV"] == "PROD" else DIR_LOCAL)


@track_function_usage
def get_known_locations_file_path() -> Path:  # noqa: D103
    user_id = st.session_state["USER_ID"]
    return get_data_dir() / "knownLocations" / f"{user_id}.txt"


@track_function_usage
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


@track_function_usage
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
    if years == 0:  # current year
        df, df_gear = cache_all_activities_and_gears_year(user_id=user_id, years=0)
    else:
        df1, df_gear1 = cache_all_activities_and_gears_year(user_id=user_id, years=0)
        # previous X years
        df2, df_gear2 = cache_all_activities_and_gears_year(
            user_id=user_id, years=years
        )
        df = pd.concat([df1, df2]).reset_index(drop=True)
        df_gear = pd.concat([df_gear1, df_gear2]).reset_index(drop=True)
    return df, df_gear


# this cache is for 2h, while all others are only for 15min
# caching requires user_id is given as parameter!!!
@st.cache_data(ttl="2h")
@track_function_usage
def cache_all_activities_and_gears_year(  # noqa: C901, PLR0915
    user_id: int,
    years: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Call fetch_all_activities() and convert to DataFrame.

    year:0 -> this year
    year:N -> previous N years
    """
    t_start = time.time()
    logger.info("Start fetch_all_activities for user_id = %s", user_id)
    df = pd.DataFrame(fetch_all_activities(years=years))
    logger.info("End fetch_all_activities() in %.1fs", (time.time() - t_start))

    # ensure all columns are there, even if df is empty
    cont = Path("activity_columns.txt").read_text().strip().split()
    for col in cont:
        if col not in df.columns:
            df[col] = None

    df_gear = pd.DataFrame(columns=("id", "name", "nickname"))

    if df.empty:
        return (df, df_gear)

    # dropping and renaming some columns
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
    assert df["start_date_local"].dtype == "datetime64[ns]", df[
        "start_date_local"
    ].dtype

    df = df.sort_values("start_date_local", ascending=False)

    # set int types
    cols = ["id", "utc_offset", "moving_time", "elapsed_time", "total_elevation_gain"]
    for col in cols:
        df[col] = df[col].astype(int)
    # st.write(df)
    # st.write(df.dtypes)
    # st.stop()

    # calc additional fields

    df["x_url"] = "https://www.strava.com/activities/" + df["id"].astype(str)

    df["x_start_h"] = round(
        df["start_date_local"].dt.hour
        + df["start_date_local"].dt.minute / 60
        + df["start_date_local"].dt.second / 3600,
        2,
    )
    df["x_date"] = df["start_date_local"].dt.date
    df["x_year"] = df["start_date_local"].dt.year
    df["x_month"] = df["start_date_local"].dt.month
    df["x_quarter"] = (1 + (df["x_month"] / 4)).astype(int)
    df["x_week"] = df["start_date_local"].dt.isocalendar().week

    # df = df.set_index("start_date_local")

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
    df["x_km/h"] = round(df["average_speed"] * 3.6, 1)
    df["x_max_km/h"] = round(df["max_speed"] * 3.6, 1)
    df["x_mph"] = round(df["average_speed"] * 3.6 / 1.60934, 1)
    df["x_max_mph"] = round(df["max_speed"] * 3.6 / 1.60934, 1)

    df["x_min"] = round(df["moving_time"] / 60, 1)
    df["x_km"] = round(df["distance"] / 1000, 1)
    df["x_mi"] = round(df["distance"] / 1000 / 1.60934, 1)  # km -> mile

    # df["x_elev_m/km"] = round(df["total_elevation_gain"] / df["x_km"], 0)
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
    if lst_gear:
        df_gear = pd.DataFrame(lst_gear).set_index("id").sort_index()
    df["x_gear_name"] = df["gear_id"].map(d_id_name)

    # geo calculations
    t_start = time.time()
    logger.info("Start geo_calc()")
    df = geo_calc(df)
    logger.info("End geo_calc() in %.1fs", (time.time() - t_start))

    # renaming
    df = df.rename(columns={"start_date_local": "start_date_local"})

    # ordering
    cols = df.columns.to_list()
    col_first = [
        "x_date",
        "name",
        "type",
        "x_url",
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
    for col in col_first:
        if col in cols:
            cols.remove(col)
        else:
            df[col] = None
            # st.write(f"'{col}' not in columns")
    col_first.extend(cols)
    df = df[col_first]

    return df, df_gear


@track_function_usage
def geo_calc(df: pd.DataFrame) -> pd.DataFrame:
    """Geo distance calculations."""
    # for each row in df, calc new column x_km_start_end via geo_distance_haversine
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
    df["x_km_start_end"] = df.apply(
        lambda row: round(
            geo_distance_haversine(
                tuple(row["start_latlng"]), tuple(row["end_latlng"])
            ),
            1,
        )  # type: ignore
        if row["start_latlng"]
        and row["end_latlng"]
        and len(row["start_latlng"]) == 2
        and len(row["end_latlng"]) == 2
        else None,
        axis=1,
    )

    # 3.1 is start a known location?
    known_locations = get_known_locations()
    df["x_location_start"] = df.apply(
        lambda row: check_is_known_location(
            reduce_geo_precision(tuple(row["start_latlng"]), 3), known_locations
        )  # type: ignore
        if row["start_latlng"] and len(row["start_latlng"]) == 2
        else None,
        axis=1,
    )
    # 3.2 is end a known location?
    df["x_location_end"] = df.apply(
        lambda row: check_is_known_location(
            reduce_geo_precision(tuple(row["end_latlng"]), 3), known_locations
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
    #     counter = 0
    return df


@track_function_usage
def get_known_locations(*, users_only: bool = False) -> list[tuple[float, float, str]]:
    """Get known locations from global and user stored data."""
    lst_known_locations = KNOWN_LOCATIONS if users_only is False else []

    p = get_known_locations_file_path()
    if p.is_file():
        for line in p.read_text().strip().split("\n"):
            lat, lon, name = line.split(" ", 3)
            lst_known_locations.append((float(lat), float(lon), name))
    return lst_known_locations


@track_function_usage
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


# no cache for raw data
@track_function_usage
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
@track_function_usage
def cities_into_1deg_geo_boxes() -> (  # noqa: C901
    dict[tuple[float, float], list[tuple[float, float, str]]]
):
    """Stack cities into boxes of 1x1 degree for faster lookup."""
    # boxes of 1 degree
    boxes = {}

    for line in read_city_db():
        lat, lon, name = line
        lat0, lon0 = int(lat), int(lon)
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
        lon1 = int(lon - offset)
        if lon1 == lon0:  # same box, so try + instead
            lon1 = int(lon + offset)
            if lon1 == lon0:
                lon1 = None  # still same box, so city must be at center

        if lon1 and (lon1 > 180 or lon1 < -180):
            lon1 = None
        t = (lat0, lon0)
        boxes.setdefault(t, []).append(line)
        if lat1:
            t = (lat1, lon0)
            boxes.setdefault(t, []).append(line)
        if lon1:
            t = (lat0, lon1)
            boxes.setdefault(t, []).append(line)
        if lat1 and lon1:
            t = (lat1, lon1)
            boxes.setdefault(t, []).append(line)

    return boxes


@st.cache_data(ttl="15m")
@track_function_usage
def search_closest_city(latlng: tuple[float, float]) -> str | None:
    """Search in 1x1 deg box of cities for closest city."""
    boxes = cities_into_1deg_geo_boxes()
    lat, lon = latlng
    latlng = (int(lat), int(lon))
    if latlng not in boxes:
        return None
    closest_city_dist = 999
    closest_city_name = None
    lst = boxes[latlng]
    for line in lst:
        city_lat, city_lng, city_name = line
        dist = geo_distance_haversine((lat, lon), (city_lat, city_lng))
        if dist < closest_city_dist:
            closest_city_dist = dist
            closest_city_name = city_name
    return closest_city_name
