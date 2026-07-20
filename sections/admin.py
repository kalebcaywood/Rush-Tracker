"""Admin-only: manage brothers, manage PNMs, export a CSV backup."""
from __future__ import annotations

import streamlit as st

import db


def render() -> None:
    st.markdown("## Admin")

    st.markdown("#### Brothers")
    with st.form("add_member", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        name = c1.text_input("Name")
        pin = c2.text_input("PIN", type="password")
        role = c3.selectbox("Role", ["brother", "admin"])
        submitted = st.form_submit_button("Add brother", type="primary")
    if submitted:
        if not name.strip() or not pin:
            st.error("Name and PIN are required.")
        else:
            try:
                db.create_member(name, pin, role)
                st.success(f"Added {name}.")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't add {name}: {e}")

    for m in db.list_members():
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        c1.write(m["name"])
        c2.caption(m["role"])
        new_pin = c3.text_input("Reset PIN", key=f"pin_{m['id']}", type="password", label_visibility="collapsed", placeholder="new PIN")
        if c3.button("Reset", key=f"resetbtn_{m['id']}") and new_pin:
            db.update_member_pin(m["id"], new_pin)
            st.success(f"PIN reset for {m['name']}.")
        if c4.button("Remove", key=f"rm_{m['id']}"):
            if m["id"] == st.session_state["member"]["id"]:
                st.error("You can't remove your own account.")
            else:
                db.delete_member(m["id"])
                st.rerun()

    st.divider()
    st.markdown("#### PNMs")
    status_labels = {"active": "Active", "cut": "❌ Cut", "bid": "🤝 Bid"}
    all_pnms = db.list_pnms()
    pnm_query = st.text_input(
        "Find a PNM", placeholder="Type a name to manage status / delete",
    ).strip().lower()
    matches = [p for p in all_pnms if pnm_query in p["full_name"].lower()] if pnm_query else all_pnms
    if len(matches) > 50:
        st.caption(f"{len(matches)} PNMs — showing the first 50, search to narrow down.")
        matches = matches[:50]
    for p in matches:
        c1, c2, c3 = st.columns([4, 2, 1])
        c1.write(p["full_name"])
        current = p.get("status", "active")
        new_status = c2.selectbox(
            "Status", db.PNM_STATUSES,
            index=db.PNM_STATUSES.index(current),
            format_func=lambda s: status_labels[s],
            key=f"adminstatus_{p['id']}",
            label_visibility="collapsed",
        )
        if new_status != current:
            db.set_pnm_status(p["id"], new_status)
            st.rerun()
        if c3.button("Delete", key=f"delpnm_{p['id']}"):
            db.delete_pnm(p["id"])
            st.rerun()

    st.divider()
    st.markdown("#### Vote analytics")
    votes = db.all_votes()
    if not votes:
        st.caption("No votes cast yet.")
    else:
        import pandas as pd

        votes_df = pd.DataFrame(votes)
        pnms = db.list_pnms()
        names = {p["id"]: p["full_name"] for p in pnms}
        active_count = sum(1 for p in pnms if p.get("status", "active") == "active")

        st.markdown("**Score distribution** (all votes)")
        dist = votes_df["score"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        dist.index = [f"{s} ★" for s in dist.index]
        st.bar_chart(dist)

        st.markdown("**Most divisive PNMs** (highest vote spread, 2+ votes)")
        g = votes_df.groupby("pnm_id")["score"]
        spread = pd.DataFrame(
            {"Avg": g.mean().round(2), "Spread (std)": g.std().round(2), "# Votes": g.count()}
        )
        spread = spread[spread["# Votes"] >= 2].sort_values("Spread (std)", ascending=False)
        spread.insert(0, "PNM", [names.get(i, "?") for i in spread.index])
        st.dataframe(spread.head(10), use_container_width=True, hide_index=True)

        st.markdown("**Voting participation** — who still needs to vote")
        cast = votes_df.groupby("member_id").size()
        part = pd.DataFrame(
            [
                {
                    "Brother": m["name"],
                    "Votes cast": int(cast.get(m["id"], 0)),
                    "Out of (active PNMs)": active_count,
                }
                for m in db.list_members()
            ]
        ).sort_values("Votes cast")
        st.dataframe(part, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Share with the chapter")
    st.caption(
        "Paste the app's URL (your *.streamlit.app link once deployed) to get a "
        "QR code you can screenshot, print, or drop in the GroupMe. Brothers "
        "scan it, log in, then use their phone's 'Add to Home Screen' to keep "
        "it as an app icon."
    )
    app_url = st.text_input("App URL", placeholder="https://your-app.streamlit.app")
    if app_url.strip():
        import io

        import qrcode

        img = qrcode.make(app_url.strip())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        c1, _ = st.columns([1, 2])
        c1.image(buf.getvalue(), caption=app_url.strip())
        st.download_button("Download QR code", buf.getvalue(), file_name="rush_tracker_qr.png")

    st.divider()
    st.markdown("#### Backup")
    st.caption("Download every table as CSV — a manual safety net alongside Supabase.")
    if st.button("Export all data"):
        files = db.export_all_csv()
        for name, content in files.items():
            st.download_button(f"Download {name}", content, file_name=name, key=f"dl_{name}")
