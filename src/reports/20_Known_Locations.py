"""Known Locations."""  # noqa: INP001

import numpy as np
import pandas as pd
import streamlit as st

from helper_activities_caching import (
    get_known_locations,
    get_known_locations_file_path,
)
from helper_logging import init_logger

st.title("Known Locations")

logger = init_logger(__file__)
logger.info("Start")

# TODO: Edit

col1, col2 = st.columns(2)
col1.header("Edit")
kl = get_known_locations(users_only=True)
df = pd.DataFrame(kl, columns=("Lat", "Lng", "Name"))
df = df[["Name", "Lat", "Lng"]].sort_values("Name")
# st.dataframe(df, hide_index=True)

df_edited = col1.data_editor(df, hide_index=True, num_rows="dynamic")
if col1.button("Save"):
    df2 = df_edited[["Lat", "Lng", "Name"]]
    df2[["Lat", "Lng"]] = df2[["Lat", "Lng"]].replace(0, np.nan)
    df2["Name"] = df2["Name"].str.strip().replace("", np.nan)
    df2 = df2.dropna()
    # trim and round
    df2["Lat"] = df2["Lat"].clip(lower=-180, upper=180).round(4)
    df2["Lng"] = df2["Lng"].clip(lower=-90, upper=90).round(4)
    df2 = df2.sort_values("Name")
    path_kl = get_known_locations_file_path()
    df2.to_csv(path_kl, sep=" ", index=False, header=False, lineterminator="\n")
    st.rerun()
    # st.write(df2)

col2.header("Map Links")
df3 = df[["Name", "Lat", "Lng"]]
zoom = 16
df3["Map"] = df3.apply(
    lambda row: f"https://www.openstreetmap.org/?mlat={row['Lat']}&mlon={row['Lng']}#map={zoom}/{row['Lat']}/{row['Lng']}",
    axis=1,
)
col2.dataframe(
    df3[["Name", "Map"]],
    hide_index=True,
    column_config={"Map": st.column_config.LinkColumn(display_text="OSM")},
)


# some more debug output only to me
if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
    st.header("Session State")
    st.write(st.session_state)

logger.info("End")
