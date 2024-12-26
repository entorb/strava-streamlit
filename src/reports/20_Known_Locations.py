"""Known Locations."""  # noqa: INP001

import numpy as np
import pandas as pd
import streamlit as st

from helper_activities_caching import (
    cache_all_activities_and_gears,
    get_known_locations,
    get_known_locations_file_path,
    reduce_geo_precision,
)
from helper_logging import init_logger

st.title(__doc__[:-1])  # type: ignore

logger = init_logger(__file__)
logger.info("Start")

# TODO: Edit

col1, col2 = st.columns(2)
col1.header("Edit")
kl = get_known_locations(users_only=True)
df = pd.DataFrame(kl, columns=("Lat", "Lon", "Name"))
df = df[["Name", "Lat", "Lon"]].sort_values("Name")
# st.dataframe(df, hide_index=True)

df_edited = col1.data_editor(df, hide_index=True, num_rows="dynamic")
if col1.button("Save"):
    df2 = df_edited[["Lat", "Lon", "Name"]]
    df2[["Lat", "Lon"]] = df2[["Lat", "Lon"]].replace(0, np.nan)
    df2["Name"] = df2["Name"].str.strip().replace("", np.nan)
    df2["Name"] = df2["Name"].str.replace(r"[\s\n\r]+", "", regex=True)
    df2 = df2.dropna()
    # trim and round
    df2["Lat"] = df2["Lat"].clip(lower=-180, upper=180).round(4)
    df2["Lon"] = df2["Lon"].clip(lower=-90, upper=90).round(4)
    df2 = df2.sort_values("Name")
    path_kl = get_known_locations_file_path()
    df2.to_csv(path_kl, sep=" ", index=False, header=False, lineterminator="\n")
    st.rerun()
    # st.write(df2)

col2.header("Map Links")
df3 = df[["Name", "Lat", "Lon"]]
zoom = 16
df3["Map"] = df3.apply(
    lambda row: f"https://www.openstreetmap.org/?mlat={row['Lat']}&mlon={row['Lon']}#map={zoom}/{row['Lat']}/{row['Lon']}",
    axis=1,
)
col2.dataframe(
    df3[["Name", "Map"]],
    hide_index=True,
    column_config={"Map": st.column_config.LinkColumn(display_text="OSM")},
)


# # some more debug output only to me
# if st.session_state["USER_ID"] == st.secrets["my_user_id"]:
#     st.header("Session State")
#     st.write(st.session_state)

st.header("Unknown Frequent Locations")
df = cache_all_activities_and_gears()[0]
df = df[df["x_location_start"].isna() & df["start_latlng"].notna()]
lst = df["start_latlng"].to_list()

df = cache_all_activities_and_gears()[0]
df = df[df["x_location_end"].isna() & df["end_latlng"].notna()]
lst.extend(df["end_latlng"].to_list())

# instead of the complicated calculation of V1, here a simple grouping
#   by rounding of coordinates.
lst = [reduce_geo_precision(x, 3) for x in lst if x]

d = {}
for el in lst:
    x = f"{el[0]}_{el[1]}"
    d[x] = d.get(x, 0) + 1

data = []
for latlng, count in sorted(d.items(), key=lambda item: item[1], reverse=True):
    # st.write(key.replace("_", "/", 1), value)
    lat, lon = latlng.split("_", 1)
    data.append((lat, lon, count))
    if count < 5:  # noqa: PLR2004
        break

df = pd.DataFrame(data, columns=("Lat", "Lon", "Count"))
zoom = 16
df["Map"] = df.apply(
    lambda row: f"https://www.openstreetmap.org/?mlat={row['Lat']}&mlon={row['Lon']}#map={zoom}/{row['Lat']}/{row['Lon']}",
    axis=1,
)
st.dataframe(
    df,
    hide_index=True,
    column_config={"Map": st.column_config.LinkColumn(display_text="OSM")},
)

logger.info("End")
