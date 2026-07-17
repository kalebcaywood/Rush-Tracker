"""Grid of PNM cards — thumbnail, name, live average score, search."""
from __future__ import annotations

import streamlit as st

import db
from sections.profile import PNM_ID_KEY

CARD_COLS = 4


def render() -> None:
    st.markdown("## Board")
    pnms = db.list_pnms()
    if not pnms:
        st.info("No PNMs yet — import a roster from the **Roster / Import** page.")
        return

    query = st.text_input("Search by name", "").strip().lower()
    if query:
        pnms = [p for p in pnms if query in p["full_name"].lower()]

    lb = db.leaderboard_df().set_index("PNM")

    cols = st.columns(CARD_COLS)
    for i, p in enumerate(pnms):
        with cols[i % CARD_COLS]:
            with st.container(border=True):
                photo = db.most_recent_photo(p["id"])
                if photo:
                    url = db.signed_url(photo["storage_path"])
                    if url:
                        st.image(url, use_container_width=True)
                st.markdown(f"**{p['full_name']}**")
                meta_bits = [b for b in [p.get("year"), p.get("major")] if b]
                if meta_bits:
                    st.caption(" · ".join(meta_bits))
                avg = lb.loc[p["full_name"], "Avg Score"] if p["full_name"] in lb.index else None
                if avg is not None and avg == avg:  # not NaN
                    st.markdown(f'<span class="score-badge">★ {avg:.2f}</span>', unsafe_allow_html=True)
                else:
                    st.caption("No votes yet")
                if st.button("View", key=f"view_{p['id']}", use_container_width=True):
                    st.session_state[PNM_ID_KEY] = p["id"]
                    st.switch_page(st.session_state["_profile_page"])
