"""Excel Import."""

from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from helper_activities_caching import cache_all_activities_and_gears
from helper_api import post_activity
from helper_logging import get_logger_from_filename

TZ_DE = ZoneInfo("Europe/Berlin")

_LOGGER = get_logger_from_filename(__file__)

COLS = {
    "Type": "object",
    "Date": "datetime64[ns]",
    "Duration (s)": "Int64",
    "Distance (m)": "float64",
    "Name": "object",
    "Description": "object",
    "Commute": "Int64",
    "Elevation gain": "float64",
    "Gear ID": "object",
}


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    """Upload activities from Excel."""
    if "activity:write" not in st.session_state["API_SCOPE"]:
        # TODO: sync with r61
        st.warning(
            "API scope 'activity:write' missing. "
            "Please logout and re-login with write permissions (orange button)."
        )
        return

    st.header("List of all your gear to be used in the import.")

    df_gear = cache_all_activities_and_gears()[1].reset_index()[
        ["id", "name", "nickname"]
    ]
    st.dataframe(df_gear, hide_index=True)

    st.markdown("""
## Input
- Use this [template](https://entorb.net/strava/download/StravaImportTemplate.xlsx) to prepare a list of activities in Excel
- Ensure to use the following date format 'YYYY-MM-DD HH:MM:SS'
                """)  # noqa: E501

    column_config = {
        "Type": st.column_config.SelectboxColumn(
            "Type",
            options=["Run", "Ride", "Walk", "Swim", "Hike", "Workout"],
            required=True,
        ),
        "Date": st.column_config.DatetimeColumn("Date", required=True),
        "Duration (s)": st.column_config.NumberColumn(
            "Duration (s)", min_value=0, step=1, required=True
        ),
        "Distance (m)": st.column_config.NumberColumn(
            "Distance (m)", min_value=0.0, format="%.1f", required=False
        ),
        "Name": st.column_config.TextColumn("Name", required=True),
        "Description": st.column_config.TextColumn("Description", required=False),
        "Commute": st.column_config.CheckboxColumn("Commute", default=False),
        "Elevation gain": st.column_config.NumberColumn(
            "Elevation gain", min_value=0.0, format="%.1f", required=False
        ),
        "Gear ID": st.column_config.SelectboxColumn(
            "Gear ID", options=df_gear["id"].tolist(), required=False
        ),
    }

    # --- Excel upload ---
    uploaded = st.file_uploader("Import activities from Excel", type=["xlsx", "xls"])
    if uploaded:
        try:
            imported = pd.read_excel(
                uploaded,
                dtype={k: v for k, v in COLS.items() if v == "object"},
            )
            imported.columns = imported.columns.str.replace("*", "", regex=False)
            missing = [c for c in COLS if c not in imported.columns]
            if missing:
                st.error(f"Missing columns in Excel file: {missing}")
            else:
                imported = imported[list(COLS)]
                imported["Date"] = pd.to_datetime(imported["Date"])
                for col in (k for k, v in COLS.items() if v == "Int64"):
                    imported[col] = imported[col].astype("Int64")
                for col in (k for k, v in COLS.items() if v == "object"):
                    imported[col] = imported[col].fillna("").astype(str)
                st.session_state.df = imported
                st.success(f"Loaded {len(imported)} rows.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Failed to read Excel file: {e}")

    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(
            {col: pd.Series(dtype=t) for col, t in COLS.items()}
        )

    edited_df = st.data_editor(
        st.session_state.df,
        column_config=column_config,
        num_rows="dynamic",
        width="content",
    )
    st.session_state.df = edited_df

    # --- Submit ---
    rows_to_submit = edited_df.dropna(subset=["Name", "Date", "Duration (s)", "Type"])
    if rows_to_submit.empty:
        return

    st.write(f"Ready to submit {len(rows_to_submit)} activities.")

    if st.button("Submit to Strava", type="primary"):
        errors = []
        responses = []
        for _, row in rows_to_submit.iterrows():
            name = row["Name"]
            try:
                distance = row["Distance (m)"]
                gear_id = row["Gear ID"] or None
                elev_gain = (
                    row["Elevation gain"] if pd.notna(row["Elevation gain"]) else None
                )
                commute = bool(row["Commute"])

                date_str = pd.Timestamp(row["Date"]).strftime("%Y-%m-%d %H:%M:%S")

                resp = post_activity(
                    act_type=row["Type"],
                    name=name,
                    date=date_str,
                    duration=int(row["Duration (s)"]),
                    distance=distance if pd.notna(distance) else None,
                    desc=row["Description"] or None,
                    commute=commute,
                    gear_id=gear_id,
                    elev_gain=elev_gain,
                )
                responses.append(
                    {
                        # "id": resp.get("id"),
                        "URL": f"https://www.strava.com/activities/{resp.get('id')}",
                        "Type": resp.get("type"),
                        "Date": pd.to_datetime(
                            resp.get("start_date_local", "").rstrip("Z")
                        ),
                        "Name": resp.get("name"),
                        "Description": resp.get("description"),
                        "Duration": resp.get("elapsed_time"),
                        "Distance": resp.get("distance"),
                        "Elevation Gain": resp.get("total_elevation_gain"),
                        "Gear ID": resp.get("gear_id"),
                        "Gear Name": (resp.get("gear") or {}).get("name"),
                    }
                )
            except Exception as e:
                errors.append(name)
                st.error(f"Failed to post '{name}': {e}")
                _LOGGER.exception("Failed to post activity '%s'", name)

        if responses:
            st.success(f"'{len(responses)}' activities created successfully:")

            st.dataframe(
                pd.DataFrame(responses),
                column_config={
                    "URL": st.column_config.LinkColumn("URL", display_text="🔗"),
                },
                hide_index=True,
            )

        if not errors:
            st.session_state.df = pd.DataFrame(
                {col: pd.Series(dtype=t) for col, t in COLS.items()}
            )


if __name__ == "__main__":
    main()

# cspell:words: Krav Maga Pendelei Maloche
