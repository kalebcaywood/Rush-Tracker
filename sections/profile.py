"""Single PNM: details, photo gallery by day, comments, star vote."""
from __future__ import annotations

from datetime import date

import streamlit as st

import auth
import db

PNM_ID_KEY = "selected_pnm_id"

FLAG_LABELS = {"red": ":red[**RED FLAG**]", "green": ":green[**GREEN FLAG**]"}
STATUS_LABELS = {"active": "Active", "cut": "Cut", "bid": "Bid"}


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

    photo_col, info_col = st.columns([1, 2])
    with photo_col:
        latest = db.most_recent_photo(pnm_id)
        url = db.signed_url(latest["storage_path"]) if latest else None
        if url:
            st.image(url, use_container_width=True)
            if latest.get("day"):
                st.caption(f"Latest photo · {latest['day']}")
        else:
            st.markdown(
                '<div style="border: 2px dashed #ccc; border-radius: 10px; '
                'padding: 48px 12px; text-align: center; color: #888;">'
                "No photo yet<br>"
                '<span style="font-size: 0.8em;">add one below</span></div>',
                unsafe_allow_html=True,
            )
    with info_col:
        fields = [
            ("Year", pnm.get("year")),
            ("Hometown", pnm.get("hometown")),
            ("High school", pnm.get("high_school")),
        ]
        # Everything else the roster sheet had (RC group, socials, …).
        for k, v in (pnm.get("extra") or {}).items():
            if "techniphi" in k.lower():
                continue
            fields.append((k, v))
        for label, value in fields:
            if value:
                st.markdown(f"**{label}:** {value}")
        if pnm.get("major"):
            st.markdown(f"**Major:** {pnm['major']}")
        if pnm.get("notes"):
            st.markdown("**Involvement / notes:**")
            st.write(pnm["notes"])

    st.divider()

    vote_col, upload_col = st.columns(2)

    with vote_col:
        day = db.current_day()
        if day >= 2 and db.is_voting_open():
            st.markdown(f"#### Your vote — Day {day}")
            my_vote = db.get_my_vote(pnm_id, member["id"], day)
            vote_key = f"vote_{day}_{pnm_id}"
            if my_vote and vote_key not in st.session_state:
                st.session_state[vote_key] = my_vote["score"] - 1
            picked = st.feedback("stars", key=vote_key)
            if picked is not None and picked + 1 != (my_vote["score"] if my_vote else None):
                db.upsert_vote(pnm_id, member["id"], picked + 1, day)
                st.rerun()
        else:
            st.markdown("#### Voting")
            st.caption(
                "Voting is closed right now."
                if day >= 2
                else "No voting on Day 1 — voting starts with the first cut round."
            )
        votes = db.list_votes(pnm_id, day) if day >= 2 else []
        if votes:
            avg = sum(v["score"] for v in votes) / len(votes)
            st.caption(f"Day {day} average: {avg:.2f} / 5 from {len(votes)} vote(s)")

    with upload_col:
        st.markdown("#### Add today's photo")
        upload_tab, camera_tab = st.tabs(["Upload", "Camera"])
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
            ["No flag", "Red flag", "Green flag"],
            horizontal=True,
            help="Red = character concern the chapter should know about. Green = strong endorsement.",
        )
        submitted = st.form_submit_button("Post comment")
    if submitted and body.strip():
        flag = {"Red flag": "red", "Green flag": "green"}.get(flag_choice)
        db.add_comment(pnm_id, member["id"], body, flag)
        st.rerun()

    admin = auth.is_admin(member)
    for c in db.list_comments(pnm_id):
        author = (c.get("members") or {}).get("name", "Unknown")
        flag_label = FLAG_LABELS.get(c.get("flag") or "")
        text_col, flag_col = st.columns([8, 1])
        with text_col:
            header = f"**{author}** · {c['created_at'][:16].replace('T', ' ')}"
            if flag_label:
                header = f"{flag_label} · " + header
            st.markdown(header)
            st.write(c["body"])
        # The author can re-tag their own comment; admins can moderate any.
        if admin or c["member_id"] == member["id"]:
            with flag_col:
                with st.popover("Flag"):
                    if st.button("Red", key=f"fr_{c['id']}"):
                        db.set_comment_flag(c["id"], "red")
                        st.rerun()
                    if st.button("Green", key=f"fg_{c['id']}"):
                        db.set_comment_flag(c["id"], "green")
                        st.rerun()
                    if st.button("Clear", key=f"fc_{c['id']}"):
                        db.set_comment_flag(c["id"], None)
                        st.rerun()
        st.markdown("---")

    if st.button("Back to Board"):
        st.switch_page(st.session_state["_board_page"])
