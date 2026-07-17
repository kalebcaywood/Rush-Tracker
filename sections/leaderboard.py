"""Sortable ranking table across all PNMs — avg score, votes, comments, activity."""
from __future__ import annotations

import streamlit as st

import db


def render() -> None:
    st.markdown("## Leaderboard")
    df = db.leaderboard_df()
    if df.empty:
        st.info("No PNMs yet — import a roster from the **Roster / Import** page.")
        return
    st.dataframe(df, use_container_width=True, hide_index=True)
