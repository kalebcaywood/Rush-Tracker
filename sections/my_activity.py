"""The logged-in brother's own ratings and comments, with edit/delete."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import db
from sections.profile import PNM_ID_KEY

FLAG_LABELS = {"red": "Red flag", "green": "Green flag"}


def render() -> None:
    member = st.session_state["member"]
    st.markdown("## My Activity")

    st.markdown("#### My ratings")
    votes = db.list_my_votes(member["id"])
    if not votes:
        st.caption("You haven't rated anyone yet — open a PNM from the Board to start.")
    else:
        st.caption(
            f"You've rated {len(votes)} PNM(s). Select a row to open their "
            "profile and change your rating."
        )
        view = pd.DataFrame(
            [
                {
                    "PNM": (v.get("pnms") or {}).get("full_name", "?"),
                    "My score": f"{v['score']} / 5",
                    "Status": ((v.get("pnms") or {}).get("status") or "active").title(),
                    "Last updated": (v.get("updated_at") or "")[:16].replace("T", " "),
                }
                for v in votes
            ]
        )
        event = st.dataframe(
            view,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="my_votes_table",
        )
        selected = event.selection.rows if event and event.selection else []
        if selected:
            pnm = votes[selected[0]].get("pnms") or {}
            if pnm.get("id"):
                st.session_state[PNM_ID_KEY] = pnm["id"]
                st.switch_page(st.session_state["_profile_page"])

    st.divider()
    st.markdown("#### My comments")
    comments = db.list_my_comments(member["id"])
    if not comments:
        st.caption("You haven't commented on anyone yet.")
        return
    st.caption(f"You've written {len(comments)} comment(s). Expand one to edit or delete it.")

    for c in comments:
        pnm_name = (c.get("pnms") or {}).get("full_name", "?")
        when = (c.get("created_at") or "")[:16].replace("T", " ")
        flag = c.get("flag")
        label = f"{pnm_name} · {when}"
        if flag in FLAG_LABELS:
            label += f" · {FLAG_LABELS[flag]}"
        with st.expander(label):
            new_body = st.text_area(
                "Comment", value=c["body"], key=f"edit_body_{c['id']}",
                label_visibility="collapsed",
            )
            flag_options = ["No flag", "Red flag", "Green flag"]
            current_flag = {"red": "Red flag", "green": "Green flag"}.get(flag, "No flag")
            new_flag_choice = st.radio(
                "Flag", flag_options,
                index=flag_options.index(current_flag),
                horizontal=True,
                key=f"edit_flag_{c['id']}",
            )
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Save changes", key=f"save_{c['id']}", type="primary"):
                if not new_body.strip():
                    st.error("Comment can't be empty — use Delete instead.")
                else:
                    db.update_comment(c["id"], new_body)
                    new_flag = {"Red flag": "red", "Green flag": "green"}.get(new_flag_choice)
                    if new_flag != flag:
                        db.set_comment_flag(c["id"], new_flag)
                    st.success("Saved.")
                    st.rerun()
            if b2.button("Delete", key=f"del_{c['id']}"):
                db.delete_comment(c["id"])
                st.rerun()
