"""Grid of PNM cards — thumbnail, name, live average score, filters."""
from __future__ import annotations

import streamlit as st

import db
from sections.profile import PNM_ID_KEY

CARD_COLS = 4
PAGE_SIZE = 24

STATUS_BADGES = {"cut": "❌ Cut", "bid": "🤝 Bid"}


def render() -> None:
    st.markdown("## Board")
    pnms = db.list_pnms()
    if not pnms:
        st.info("No PNMs yet — import a roster from the **Roster / Import** page.")
        return

    member = st.session_state["member"]

    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    query = c1.text_input("Search by name", "").strip().lower()
    status_filter = c2.selectbox("Status", ["Active", "All", "Bid", "Cut"])
    sort_by = c3.selectbox("Sort", ["Name", "Highest score", "Lowest score"])
    only_unvoted = c4.toggle("I haven't voted", help="Only show PNMs you haven't scored yet")

    if query:
        pnms = [p for p in pnms if query in p["full_name"].lower()]
    if status_filter != "All":
        pnms = [p for p in pnms if p.get("status", "active") == status_filter.lower()]
    if only_unvoted:
        voted = db.my_voted_pnm_ids(member["id"])
        pnms = [p for p in pnms if p["id"] not in voted]

    lb = db.leaderboard_df().set_index("PNM")
    flags = db.flag_counts()

    def avg_of(p: dict):
        if p["full_name"] in lb.index:
            v = lb.loc[p["full_name"], "Avg Score"]
            if v == v:  # not NaN
                return v
        return None

    if sort_by == "Highest score":
        pnms = sorted(pnms, key=lambda p: (avg_of(p) is None, -(avg_of(p) or 0)))
    elif sort_by == "Lowest score":
        pnms = sorted(pnms, key=lambda p: (avg_of(p) is None, avg_of(p) or 0))

    if not pnms:
        st.caption("Nothing matches these filters." + (" You've voted on everyone — nice." if only_unvoted else ""))
        return

    n_pages = (len(pnms) + PAGE_SIZE - 1) // PAGE_SIZE
    if n_pages > 1:
        pc1, pc2 = st.columns([1, 3])
        page = pc1.number_input("Page", min_value=1, max_value=n_pages, value=1)
        start = (page - 1) * PAGE_SIZE
        shown = pnms[start : start + PAGE_SIZE]
        pc2.caption(
            f"Showing {start + 1}–{start + len(shown)} of {len(pnms)} PNMs "
            f"(page {page} of {n_pages})"
        )
    else:
        shown = pnms

    photo_map = db.latest_photo_map()

    cols = st.columns(CARD_COLS)
    for i, p in enumerate(shown):
        with cols[i % CARD_COLS]:
            with st.container(border=True):
                storage_path = photo_map.get(p["id"])
                if storage_path:
                    url = db.signed_url(storage_path)
                    if url:
                        st.image(url, use_container_width=True)
                name_line = f"**{p['full_name']}**"
                badge = STATUS_BADGES.get(p.get("status", "active"))
                if badge:
                    name_line += f" · {badge}"
                st.markdown(name_line)
                meta_bits = [b for b in [p.get("year"), p.get("major")] if b]
                if meta_bits:
                    st.caption(" · ".join(meta_bits))
                avg = avg_of(p)
                if avg is not None:
                    st.markdown(f'<span class="score-badge">★ {avg:.2f}</span>', unsafe_allow_html=True)
                else:
                    st.caption("No votes yet")
                pf = flags.get(p["id"])
                if pf:
                    bits = []
                    if pf.get("red"):
                        bits.append(f"🚩 {pf['red']}")
                    if pf.get("green"):
                        bits.append(f"✅ {pf['green']}")
                    st.caption(" · ".join(bits))
                if st.button("View", key=f"view_{p['id']}", use_container_width=True):
                    st.session_state[PNM_ID_KEY] = p["id"]
                    st.switch_page(st.session_state["_profile_page"])
