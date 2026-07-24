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

    with st.expander("Download as PowerPoint"):
        st.caption(
            "Builds a .pptx of this day's slideshow — title slide, round "
            "dividers, one slide per PNM with their latest photo — for "
            "presenting from the projector machine."
        )
        if st.button(f"Build Day {day} deck ({len(pnms)} PNMs)"):
            import deck_export

            with st.spinner("Building deck (fetching photos)…"):
                deck = deck_export.build_deck(day)
            if deck:
                st.session_state["deck_bytes"] = deck
                st.session_state["deck_day"] = day
        if st.session_state.get("deck_bytes") and st.session_state.get("deck_day") == day:
            st.download_button(
                "Download deck",
                st.session_state["deck_bytes"],
                file_name=f"rush_day{day}_slideshow.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                type="primary",
            )

    rounds = sorted({p.get("_round", 1) for p in pnms})
    round_pick = "All rounds"
    if len(rounds) > 1:
        round_pick = st.radio(
            "Round", ["All rounds"] + [f"Round {r}" for r in rounds],
            horizontal=True, label_visibility="collapsed",
        )
        if round_pick != "All rounds":
            rnd = int(round_pick.split()[-1])
            pnms = [p for p in pnms if p.get("_round", 1) == rnd]

    # Reset position when switching days or rounds.
    view_key = f"{day}|{round_pick}"
    if st.session_state.get(DAY_KEY) != view_key:
        st.session_state[DAY_KEY] = view_key
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
    slide_round = p.get("_round", 1)
    nav3.markdown(
        f"**{idx + 1} of {len(pnms)}** — Round {slide_round} — "
        f"{db.DAY_LABELS.get(day, f'Day {day}')}"
    )
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
                    bits.append(f":red[**{flags['red']} red flag{'s' if flags['red'] != 1 else ''}**]")
                if flags.get("green"):
                    bits.append(f":green[**{flags['green']} green flag{'s' if flags['green'] != 1 else ''}**]")
                st.markdown(" · ".join(bits))
        if p.get("notes"):
            st.caption(p["notes"])
