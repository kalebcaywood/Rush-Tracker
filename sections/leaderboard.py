"""Sortable ranking across all PNMs — the bid-list builder."""
from __future__ import annotations

import streamlit as st

import db


def render() -> None:
    st.markdown("## Leaderboard")
    df = db.leaderboard_df()
    if df.empty:
        st.info("No PNMs yet — import a roster from the **Roster / Import** page.")
        return

    status_filter = st.radio(
        "Show", ["All", "Active", "Bid", "Cut"], horizontal=True,
        label_visibility="collapsed",
    )
    view = df if status_filter == "All" else df[df["Status"] == status_filter]
    st.dataframe(view, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    c1.download_button(
        "⬇ Full leaderboard (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name="leaderboard.csv",
        use_container_width=True,
    )
    bids = df[df["Status"] == "Bid"]
    c2.download_button(
        f"⬇ Bid list ({len(bids)} PNMs)",
        bids.to_csv(index=False).encode("utf-8"),
        file_name="bid_list.csv",
        disabled=bids.empty,
        use_container_width=True,
        help="PNMs marked 'Bid' — set status on a PNM's profile or the Admin page.",
    )
