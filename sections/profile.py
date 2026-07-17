"""Single PNM: details, photo gallery by day, comments, star vote."""
from __future__ import annotations

from datetime import date

import streamlit as st

import db

PNM_ID_KEY = "selected_pnm_id"


def render() -> None:
    pnm_id = st.session_state.get(PNM_ID_KEY)
    if not pnm_id:
        st.info("Pick a PNM from the **Board** page first.")
        return

    pnm = db.get_pnm(pnm_id)
    if not pnm:
        st.error("This PNM no longer exists.")
        return

    member = st.session_state["member"]

    st.markdown(f"## {pnm['full_name']}")
    meta_bits = [b for b in [pnm.get("year"), pnm.get("major"), pnm.get("hometown"), pnm.get("high_school")] if b]
    if meta_bits:
        st.caption(" · ".join(meta_bits))
    if pnm.get("notes"):
        st.write(pnm["notes"])
    if pnm.get("extra"):
        with st.expander("More info from roster"):
            for k, v in pnm["extra"].items():
                st.write(f"**{k}:** {v}")

    st.divider()

    vote_col, upload_col = st.columns(2)

    with vote_col:
        st.markdown("#### Your vote")
        my_vote = db.get_my_vote(pnm_id, member["id"])
        vote_key = f"vote_{pnm_id}"
        if my_vote and vote_key not in st.session_state:
            st.session_state[vote_key] = my_vote["score"] - 1
        picked = st.feedback("stars", key=vote_key)
        if picked is not None and picked + 1 != (my_vote["score"] if my_vote else None):
            db.upsert_vote(pnm_id, member["id"], picked + 1)
            st.rerun()
        votes = db.list_votes(pnm_id)
        if votes:
            avg = sum(v["score"] for v in votes) / len(votes)
            st.caption(f"Average: {avg:.2f} ★ from {len(votes)} vote(s)")

    with upload_col:
        st.markdown("#### Add today's photo")
        files = st.file_uploader(
            "Upload photo(s)", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
            key=f"upload_{pnm_id}",
        )
        if files and st.button("Save photo(s)", key=f"save_{pnm_id}"):
            for f in files:
                db.upload_photo(
                    pnm_id, f.getvalue(), f.name, f.type or "image/jpeg",
                    uploaded_by=member["id"], day=date.today(),
                )
            db.signed_url.clear()
            st.success(f"Saved {len(files)} photo(s).")
            st.rerun()

    st.divider()
    st.markdown("#### Photos")
    photos = db.list_photos(pnm_id)
    if not photos:
        st.caption("No photos yet.")
    else:
        by_day: dict[str, list[dict]] = {}
        for ph in photos:
            by_day.setdefault(ph["day"], []).append(ph)
        for day, day_photos in by_day.items():
            st.markdown(f"**{day}**")
            cols = st.columns(min(len(day_photos), 5) or 1)
            for i, ph in enumerate(day_photos):
                url = db.signed_url(ph["storage_path"])
                if url:
                    with cols[i % len(cols)]:
                        st.image(url, use_container_width=True)

    st.divider()
    st.markdown("#### Comments")
    with st.form(f"comment_form_{pnm_id}", clear_on_submit=True):
        body = st.text_area("Add a comment", label_visibility="collapsed")
        submitted = st.form_submit_button("Post comment")
    if submitted and body.strip():
        db.add_comment(pnm_id, member["id"], body)
        st.rerun()

    for c in db.list_comments(pnm_id):
        author = (c.get("members") or {}).get("name", "Unknown")
        st.markdown(f"**{author}** · {c['created_at'][:16].replace('T', ' ')}")
        st.write(c["body"])
        st.markdown("---")

    if st.button("← Back to Board"):
        st.switch_page(st.session_state["_board_page"])
