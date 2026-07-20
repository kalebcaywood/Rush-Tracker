"""Round-based voting: rate every active PNM for the current rush day.

Feeds the brother one unrated PNM at a time with a progress bar, so the
whole active class gets covered before that night's cut meeting.
"""
from __future__ import annotations

import streamlit as st

import db
from sections.profile import PNM_ID_KEY

SKIP_KEY = "voting_skipped"


def render() -> None:
    member = st.session_state["member"]
    day = db.current_day()

    st.markdown("## Voting")
    st.markdown(f"**{db.DAY_LABELS.get(day, f'Day {day}')}**")

    if day < 2:
        st.info(
            "No voting on Day 1 — get out there and meet the PNMs. "
            "Voting opens when the exec board starts the first cut round."
        )
        return
    if not db.is_voting_open():
        st.info("Voting is closed right now. The exec board opens it each round.")
        return

    active = [p for p in db.list_pnms() if p.get("status", "active") == "active"]
    if not active:
        st.info("No active PNMs to vote on.")
        return

    # If today's attendance sheet is uploaded, vote only on who came back —
    # in the same order the slideshow presents them.
    attendance_order = db.attendance_pnm_ids(day)
    if attendance_order:
        active_by_id = {p["id"]: p for p in active}
        queue = [active_by_id[i] for i in attendance_order if i in active_by_id]
        scope = f"today's {len(queue)} returning PNMs, in slideshow order"
    else:
        queue = active
        scope = f"all {len(queue)} active PNMs (no attendance sheet uploaded for today)"
    if not queue:
        st.info("None of today's attendees are still active.")
        return

    voted = db.my_voted_pnm_ids(member["id"], day)
    remaining = [p for p in queue if p["id"] not in voted]
    done = len(queue) - len(remaining)
    st.progress(done / len(queue))
    st.caption(f"You've rated {done} of {len(queue)} — {scope}.")

    if not remaining:
        st.success(
            "You've rated every active PNM for today. You can still change any "
            "rating from the My Activity page until voting closes."
        )
        return

    # Skipped PNMs drop to the back of the queue for this session
    # (stable sort keeps the slideshow order within each group).
    skipped: list[str] = st.session_state.setdefault(SKIP_KEY, [])
    remaining.sort(key=lambda p: p["id"] in skipped)
    p = remaining[0]

    with st.container(border=True):
        photo_col, info_col = st.columns([1, 2])
        with photo_col:
            photo = db.most_recent_photo(p["id"])
            url = db.signed_url(photo["storage_path"]) if photo else None
            if url:
                st.image(url, use_container_width=True)
            else:
                st.caption("No photo yet")
        with info_col:
            st.markdown(f"### {p['full_name']}")
            meta = [b for b in [p.get("year"), p.get("hometown"), p.get("high_school")] if b]
            if meta:
                st.caption(" · ".join(meta))
            rc = (p.get("extra") or {}).get("RC Group")
            if rc:
                st.markdown(f"**RC Group:** {rc}")
            if p.get("notes"):
                st.write(p["notes"][:300] + ("…" if len(p.get("notes") or "") > 300 else ""))

            stars = st.feedback("stars", key=f"voting_{day}_{p['id']}")
            if stars is not None:
                db.upsert_vote(p["id"], member["id"], stars + 1, day)
                st.rerun()

        b1, b2, _ = st.columns([1, 1, 2])
        if b1.button("Skip for now"):
            skipped.append(p["id"])
            st.rerun()
        if b2.button("Full profile"):
            st.session_state[PNM_ID_KEY] = p["id"]
            st.switch_page(st.session_state["_profile_page"])
