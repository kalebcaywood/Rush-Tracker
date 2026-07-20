"""Sortable ranking across all PNMs — the bid-list builder."""
from __future__ import annotations

import streamlit as st

import auth
import db
from sections.profile import PNM_ID_KEY


def render() -> None:
    st.markdown("## Leaderboard")

    current = db.current_day()
    day_options: list = ["All days"] + [d for d in range(2, 6) if d <= max(current, 2)]
    default_idx = day_options.index(current) if current in day_options else 0
    c1, c2 = st.columns([1, 3])
    day_pick = c1.selectbox("Scores from", day_options, index=default_idx)
    day = None if day_pick == "All days" else int(day_pick)
    if day is not None:
        c2.caption(db.DAY_LABELS.get(day, ""))

    df = db.leaderboard_df(day)
    if df.empty:
        st.info("No PNMs yet — import a roster from the **Roster / Import** page.")
        return

    if day is not None:
        attendees = db.attendance_for_day(day)
        if attendees:
            if st.checkbox(f"Only the {len(attendees)} PNMs who came Day {day}", value=True):
                names = {p["full_name"] for p in attendees}
                df = df[df["PNM"].isin(names)]

    status_filter = st.radio(
        "Show", ["All", "Active", "Bid", "Cut"], horizontal=True,
        label_visibility="collapsed",
    )
    view = (df if status_filter == "All" else df[df["Status"] == status_filter]).reset_index(drop=True)
    st.caption("Select a row to open that PNM's profile.")
    event = st.dataframe(
        view,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="leaderboard_table",
    )
    selected = event.selection.rows if event and event.selection else []
    if selected:
        name = view.iloc[selected[0]]["PNM"]
        pnm = next((p for p in db.list_pnms() if p["full_name"] == name), None)
        if pnm:
            st.session_state[PNM_ID_KEY] = pnm["id"]
            st.switch_page(st.session_state["_profile_page"])

    if auth.is_admin(st.session_state["member"]):
        c1, c2 = st.columns(2)
        c1.download_button(
            "Download full leaderboard (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name="leaderboard.csv",
            use_container_width=True,
        )
        bids = df[df["Status"] == "Bid"]
        c2.download_button(
            f"Download bid list ({len(bids)} PNMs)",
            bids.to_csv(index=False).encode("utf-8"),
            file_name="bid_list.csv",
            disabled=bids.empty,
            use_container_width=True,
            help="PNMs marked 'Bid' — set status on a PNM's profile or the Admin page.",
        )
