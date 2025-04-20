"""Test: Open all Pages/Reports."""
# ruff: noqa: D100 D103 E402 F841 INP001 N802 PLR2004 S101

import sys
import warnings
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

warnings.filterwarnings("ignore", message=".*streamlit.runtime.scriptrunner_utils.*")
st.session_state["ENV"] = "DEV"
st.session_state["USER_ID"] = 7656541

sys.path.insert(0, (Path(__file__).parent.parent / "src").as_posix())
sys.path.insert(0, (Path(__file__).parent.parent / "src" / "reports").as_posix())
from helper_activities_caching import cache_all_activities_and_gears


# helpers
def init_report(path: Path) -> AppTest:
    at = AppTest.from_file(path)
    at.session_state["ENV"] = "DEV"
    at.session_state["USER_ID"] = 7656541
    return at


def run_and_assert_no_problems(at: AppTest, path: Path) -> None:
    at.run(timeout=60)
    assert not at.exception, path.stem
    assert not at.error, path.stem
    assert not at.warning, path.stem


def init_and_run(path: Path) -> AppTest:
    at = init_report(path)
    run_and_assert_no_problems(at, path)
    return at


# tests
def test_all_pages() -> None:
    """Open all pages and check for errors and warnings."""
    for p in sorted(Path("src/reports").glob("*.py")):
        f = p.stem
        t = f[4:]
        print(t)
        _ = init_and_run(p)


def test_r05_current_year() -> None:
    p = Path("src/reports/r05_Current_Year.py")
    at = init_and_run(p)
    at.session_state["sel_types"] = ["Run", "Ride"]
    run_and_assert_no_problems(at, p)


def test_r20_activity_stats() -> None:
    p = Path("src/reports/r20_Activity_Stats.py")
    at = init_and_run(p)
    at.session_state["sel_freq"] = "Quarter"
    run_and_assert_no_problems(at, p)
    at.session_state["sel_freq"] = "Month"
    run_and_assert_no_problems(at, p)
    at.session_state["sel_freq"] = "Week"
    run_and_assert_no_problems(at, p)


def test_r40_cal_export() -> None:
    p = Path("src/reports/r40_Cal_Export.py")
    init_and_run(p)
    df, _df_gear = cache_all_activities_and_gears()
    from reports.r40_Cal_Export import gen_ics

    gen_ics(df)
