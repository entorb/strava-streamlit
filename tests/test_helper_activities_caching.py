# ruff: noqa: D100, D103, INP001, PLR2004

import sys
from math import isnan
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

sys.path.insert(0, (Path(__file__).parent.parent / "src").as_posix())
from helper_activities_caching import (
    cache_all_activities_and_gears,
    check_is_known_location,
    cities_into_1deg_geo_boxes,
    fetch_all_activities,
    geo_distance_haversine,
    get_known_locations,
    read_city_db,
    reduce_geo_precision,
    search_closest_city,
)

st.session_state["ENV"] = "DEV"
st.session_state["USER_ID"] = 7656541

at = AppTest.from_file("src/helper_activities_caching.py")

hamburg = (53.5715, 10.0110)
munich = (48.1492, 11.5860)


def test_reduce_geo_precision() -> None:
    coord = (53.5665, 10.0110)
    reduced_coord = reduce_geo_precision(coord, 2)
    assert reduced_coord == (53.57, 10.01)


def test_geo_distance_haversine() -> None:
    assert (
        round(geo_distance_haversine(hamburg, munich), 1) * 10 == 6129
    )  # SQ does not like float comparison


def test_check_is_known_location() -> None:
    # cspell:disable-next-line
    known_locations = get_known_locations()
    assert check_is_known_location((49.59, 11.03), known_locations) == "ER-ObiKreisel"


def test_fetch_all_activities() -> None:
    _ = fetch_all_activities(year_start=0, year_end=0)
    assert not at.exception


def test_read_city_db() -> None:
    lst = read_city_db()
    assert len(lst) == 4


def test_cities_into_1deg_geo_boxes() -> None:
    boxes = cities_into_1deg_geo_boxes()
    assert len(boxes) == 16
    assert boxes[(53, 10)][0][2] == "EU-DE-HH-Hamburg"
    assert boxes[(53, 9)][0][2] == "EU-DE-HH-Hamburg"
    assert boxes[(54, 10)][0][2] == "EU-DE-HH-Hamburg"
    assert boxes[(54, 9)][0][2] == "EU-DE-HH-Hamburg"


def test_search_closest_city() -> None:
    assert search_closest_city((53.5, 10.0)) == "EU-DE-HH-Hamburg"


def test_cache_all_activities_and_gears() -> None:
    _df, _df_gear = cache_all_activities_and_gears()
    assert not at.exception


def test_cache_all_activities_and_gears_2() -> None:
    df, _df_gear = cache_all_activities_and_gears()
    print(df)
    # run
    assert df["x_km"].iat[0] * 10 == 131, df["x_km"].iat[0]
    assert round(df["x_km_start_end"].iat[0], 3) * 10 == 34, df["x_km_start_end"].iat[0]
    # ride
    assert df["x_nearest_city_start"].iat[1] == "EU-DE-SN-Dresden", df[
        "x_nearest_city_start"
    ].iat[1]
    assert df["x_mi"].iat[1] * 10 == 189, df["x_mi"].iat[1]
    # swim
    assert isnan(df["x_elev_%"].iat[2]) is True, df["x_elev_%"].iat[2]
