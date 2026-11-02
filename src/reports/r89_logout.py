"""Logout."""

import json

import streamlit as st

from helper_activities_caching import (
    delete_gear_cache,
    get_act_desc_cache_file_path,
    refresh_activities_cache,
)
from helper_api import fetch_activity_description
from helper_logging import get_logger_from_filename
from helper_login import (
    logout,
)

_LOGGER = get_logger_from_filename(__file__)


def logout_and_delete() -> None:
    """Delete selected caches of this user, then logout (clears session_state)."""
    user_id = st.session_state["USER_ID"]
    if st.session_state.get("del_gear"):
        delete_gear_cache(user_id)
        refresh_activities_cache()
    p = get_act_desc_cache_file_path()
    if st.session_state.get("del_desc") and p.exists():
        # only this user's in-memory entries, not other users'
        for activity_id in json.loads(p.read_text()):
            fetch_activity_description.clear(
                activity_id=int(activity_id), user_id=user_id
            )
        p.unlink()
    logout()


def main() -> None:  # noqa: D103
    st.checkbox("Delete cached gear data", value=False, key="del_gear")
    if get_act_desc_cache_file_path().exists():
        st.checkbox("Delete cached activity descriptions", value=False, key="del_desc")
    st.button("Logout", on_click=logout_and_delete)


if __name__ == "__main__":
    main()
