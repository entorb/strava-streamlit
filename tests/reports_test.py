# ruff: noqa: D100 D103 E402 F841 INP001 N802 PLR2004 S101


import sys
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

st.session_state["ENV"] = "DEV"
st.session_state["USER_ID"] = 7656541

sys.path.insert(0, (Path(__file__).parent.parent / "src").as_posix())
sys.path.insert(0, (Path(__file__).parent.parent / "src" / "reports").as_posix())
from helper_activities_caching import cache_all_activities_and_gears


# TODO: add to streamlit-examples
def init_report(path: str) -> AppTest:
    at = AppTest.from_file(path)
    at.session_state["ENV"] = "DEV"
    at.session_state["USER_ID"] = 7656541
    return at


def run_and_assert_no_problems(at: AppTest) -> None:
    at.run()
    assert not at.exception
    assert not at.error
    assert not at.warning


def init_and_run(path: str) -> AppTest:
    at = init_report(path)
    run_and_assert_no_problems(at)
    return at


def test_r01_Caching() -> None:
    init_and_run("src/reports/r01_Caching.py")


def test_r05_Current_Year() -> None:
    at = init_and_run("src/reports/r05_Current_Year.py")
    at.session_state["sel_types"] = ["Run", "Ride"]
    run_and_assert_no_problems(at)


def test_r10_Activity_List() -> None:
    init_and_run("src/reports/r10_Activity_List.py")


def test_r20_Activity_Stats() -> None:
    at = init_and_run("src/reports/r20_Activity_Stats.py")
    at.session_state["sel_freq"] = "Quarter"
    run_and_assert_no_problems(at)
    at.session_state["sel_freq"] = "Month"
    run_and_assert_no_problems(at)
    at.session_state["sel_freq"] = "Week"
    run_and_assert_no_problems(at)


def test_r40_Cal_Export() -> None:
    init_and_run("src/reports/r40_Cal_Export.py")
    df, df_gear = cache_all_activities_and_gears()
    from r40_Cal_Export import gen_ics

    gen_ics(df)


def test_r50_Known_Locations() -> None:
    init_and_run("src/reports/r50_Known_Locations.py")


def test_r97_Contact() -> None:
    init_and_run("src/reports/r97_Contact.py")


def test_r98_Internal_Stats() -> None:
    init_and_run("src/reports/r98_Internal_Stats.py")


def test_r99_Logout() -> None:
    init_and_run("src/reports/r99_Logout.py")
