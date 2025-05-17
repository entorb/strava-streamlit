# ruff: noqa: D100 D103 INP001 PLR2004 S101 E402

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

st.session_state["ENV"] = "DEV"
st.session_state["USER_ID"] = 7656541

sys.path.insert(0, (Path(__file__).parent.parent / "src").as_posix())
sys.path.insert(0, (Path(__file__).parent.parent / "src" / "reports").as_posix())
from reports.r20_activity_stats import add_data_and_empty_df, generate_empty_df

at = AppTest.from_file("src/reports/r20_activity_stats.py")


def test_generate_empty_df_quarter() -> None:
    df = generate_empty_df(
        sport="Run",
        freq="Quarter",
        year_min=2022,
        year_max=2024,
        aggregation_name="Kilometer-sum",
    )
    assert len(df) == 12, len(df)
    assert df.columns == ["Kilometer-sum"], df.columns
    df = df.reset_index()
    assert df.columns.tolist() == [
        "year",
        "quarter",
        "type",
        "Kilometer-sum",
    ], df.columns.tolist()
    assert not at.exception


def test_generate_empty_df_month() -> None:
    df = generate_empty_df(
        sport="Ride",
        freq="Month",
        year_min=2020,
        year_max=2023,
        aggregation_name="Hour-sum",
    )
    assert len(df) == 48, len(df)


def test_generate_empty_df_week() -> None:
    df = generate_empty_df(
        sport="Swim",
        freq="Week",
        year_min=2020,
        year_max=2020,
        aggregation_name="Hour-sum",
    )
    assert len(df) == 52, len(df)


def test_add_data_and_empty_df_run_only() -> None:
    df_data = pd.DataFrame(
        {
            "year": [2022, 2022, 2023, 2023],
            "quarter": [1, 2, 1, 2],
            "type": ["Run", "Run", "Run", "Run"],
            "Kilometer-sum": [10, 20, 30, 40],
        }
    ).set_index(["year", "quarter", "type"])

    df_empty = generate_empty_df(
        sport="Run",
        freq="Quarter",
        year_min=2022,
        year_max=2023,
        aggregation_name="Kilometer-sum",
    )

    df = add_data_and_empty_df(df_data, df_empty, aggregation_name="Kilometer-sum")

    assert len(df) == 6, len(df)
    assert df["Kilometer-sum"].sum() == 100, df["Kilometer-sum"].sum()


def test_add_data_and_empty_df_mixed() -> None:
    df_data = pd.DataFrame(
        {
            "year": [2022, 2022, 2023, 2023],
            "quarter": [1, 2, 1, 2],
            "type": ["Run", "Ride", "Swim", "Hike"],
            "Kilometer-sum": [10, 20, 30, 40],
        }
    ).set_index(["year", "quarter", "type"])

    df_empty = generate_empty_df(
        sport="Run",
        freq="Quarter",
        year_min=2022,
        year_max=2023,
        aggregation_name="Kilometer-sum",
    )

    df = add_data_and_empty_df(df_data, df_empty, aggregation_name="Kilometer-sum")

    assert len(df) == 8, len(df)
    assert df["Kilometer-sum"].sum() == 100, df["Kilometer-sum"].sum()
