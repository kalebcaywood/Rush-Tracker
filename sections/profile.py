"""Single PNM: details, photo gallery by day, comments, star vote."""
from __future__ import annotations

from datetime import date

import streamlit as st

import auth
import db

PNM_ID_KEY = "selected_pnm_id"

FLAG_ICONS = {"red": "🚩", "green": "✅"}
STATUS_LABELS = {"active": "Active", "cut": "❌ Cut", "bid": "🤝 Bid"}


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

    title_col, status_col = st.columns([4, 1])
    status = pnm.get("status", "active")
    with title_col:
        suffix = f" · {STATUS_LABELS[status]}" if status != "active" else ""
        st.markdown(f"## {pnm['full_name']}{suffix}")
    with status_col:
        if auth.is_admin(member):
            new_status = st.selectbox(
                "Status",
                db.PNM_STATUSES,
                index=db.PNM_STATUSES.index(status),
                format_func=lambda s: STATUS_LABELS[s],
                key=f"status_{pnm_id}",
            )
            if new_status != status:
                db.set_pnm_status(pnm_id, new_status)
                st.rerun()

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
        upload_tab, camera_tab = st.tabs(["📁 Upload", "📷 Camera"])
        with upload_tab:
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
        with camera_tab:
            shot = st.camera_input("Take a photo", key=f"camera_{pnm_id}")
            if shot is not None and st.button("Save this photo", key=f"savecam_{pnm_id}"):
                db.upload_photo(
                    pnm_id, shot.getvalue(),
                    f"camera_{date.today().isoformat()}.jpg", "image/jpeg",
                    uploaded_by=member["id"], day=date.today(),
                )
                db.signed_url.clear()
                st.success("Photo saved.")
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
        flag_choice = st.radio(
            "Tag it",
            ["No flag", "🚩 Red flag", "✅ Green flag"],
            horizontal=True,
            help="Red = character concern the chapter should know about. Green = strong endorsement.",
        )
        submitted = st.form_submit_button("Post comment")
    if submitted and body.strip():
        flag = {"🚩 Red flag": "red", "✅ Green flag": "green"}.get(flag_choice)
        db.add_comment(pnm_id, member["id"], body, flag)
        st.rerun()

    admin = auth.is_admin(member)
    for c in db.list_comments(pnm_id):
        author = (c.get("members") or {}).get("name", "Unknown")
        icon = FLAG_ICONS.get(c.get("flag") or "", "")
        text_col, flag_col = st.columns([8, 1])
        with text_col:
            st.markdown(f"{icon} **{author}** · {c['created_at'][:16].replace('T', ' ')}")
            st.write(c["body"])
        # The author can re-tag their own comment; admins can moderate any.
        if admin or c["member_id"] == member["id"]:
            with flag_col:
                with st.popover("⚑"):
                    if st.button("🚩 Red", key=f"fr_{c['id']}"):
                        db.set_comment_flag(c["id"], "red")
                        st.rerun()
                    if st.button("✅ Green", key=f"fg_{c['id']}"):
                        db.set_comment_flag(c["id"], "green")
                        st.rerun()
                    if st.button("Clear", key=f"fc_{c['id']}"):
                        db.set_comment_flag(c["id"], None)
                        st.rerun()
        st.markdown("---")

    if st.button("← Back to Board"):
        st.switch_page(st.session_state["_board_page"])
