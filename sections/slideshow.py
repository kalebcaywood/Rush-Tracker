"""Projector slideshow: the day's returning PNMs, one at a time, in the
order of the uploaded attendance sheet. The Voting queue follows the same
order, so the room and everyone's phones stay in sync.
"""
from __future__ import annotations

import streamlit as st

import db

IDX_KEY = "slideshow_idx"
DAY_KEY = "slideshow_day"


def render() -> None:
    st.markdown("## Slideshow")

    current = db.current_day()
    day = st.selectbox(
        "Day", [1, 2, 3, 4, 5],
        index=current - 1 if 1 <= current <= 5 else 0,
        format_func=lambda d: db.DAY_LABELS.get(d, f"Day {d}"),
    )

    pnms = db.attendance_for_day(day)
    if not pnms:
        st.info(
            f"No attendance uploaded for Day {day} yet. Upload the day's "
            "returning-PNM sheet on the **Roster / Import** page first."
        )
        return

    # Reset position when switching days.
    if st.session_state.get(DAY_KEY) != day:
        st.session_state[DAY_KEY] = day
        st.session_state[IDX_KEY] = 0
    idx = max(0, min(st.session_state.get(IDX_KEY, 0), len(pnms) - 1))
    p = pnms[idx]

    nav1, nav2, nav3, nav4 = st.columns([1, 1, 2, 1])
    if nav1.button("Previous", disabled=idx == 0, use_container_width=True):
        st.session_state[IDX_KEY] = idx - 1
        st.rerun()
    if nav2.button("Next", disabled=idx >= len(pnms) - 1, use_container_width=True, type="primary"):
        st.session_state[IDX_KEY] = idx + 1
        st.rerun()
    nav3.markdown(f"**{idx + 1} of {len(pnms)}** — {db.DAY_LABELS.get(day, f'Day {day}')}")
    if nav4.button("Restart", use_container_width=True):
        st.session_state[IDX_KEY] = 0
        st.rerun()

    with st.container(border=True):
        photo_col, info_col = st.columns([1, 1])
        with photo_col:
            photo = db.most_recent_photo(p["id"])
            url = db.signed_url(photo["storage_path"]) if photo else None
            if url:
                st.image(url, use_container_width=True)
            else:
                st.markdown(
                    '<div style="border: 2px dashed #ccc; border-radius: 10px; '
                    'padding: 96px 12px; text-align: center; color: #888;">'
                    "No photo</div>",
                    unsafe_allow_html=True,
                )
        with info_col:
            st.markdown(f"# {p['full_name']}")
            for label, value in [
                ("Year", p.get("year")),
                ("Hometown", p.get("hometown")),
                ("High school", p.get("high_school")),
            ]:
                if value:
                    st.markdown(f"**{label}:** {value}")
            rc = (p.get("extra") or {}).get("RC Group")
            if rc:
                st.markdown(f"**RC Group:** {rc}")
            day_votes = db.list_votes(p["id"], day)
            if day_votes:
                avg = sum(v["score"] for v in day_votes) / len(day_votes)
                st.markdown(f"**Day {day} average:** {avg:.2f} / 5 ({len(day_votes)} votes)")
            flags = db.flag_counts().get(p["id"])
            if flags:
                bits = []
                if flags.get("red"):
                    bits.append(f"{flags['red']} red flag(s)")
                if flags.get("green"):
                    bits.append(f"{flags['green']} green flag(s)")
                st.markdown(f"**Flags:** {', '.join(bits)}")
        if p.get("notes"):
            st.caption(p["notes"])
