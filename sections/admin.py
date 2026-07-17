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
    for p in db.list_pnms():
        c1, c2 = st.columns([5, 1])
        c1.write(p["full_name"])
        if c2.button("Delete", key=f"delpnm_{p['id']}"):
            db.delete_pnm(p["id"])
            st.rerun()

    st.divider()
    st.markdown("#### Backup")
    st.caption("Download every table as CSV — a manual safety net alongside Supabase.")
    if st.button("Export all data"):
        files = db.export_all_csv()
        for name, content in files.items():
            st.download_button(f"Download {name}", content, file_name=name, key=f"dl_{name}")
