"""Named login: pick your name, enter your PIN. First run bootstraps an admin.

Sets st.session_state['member'] = {"id", "name", "role"} once authenticated.
Every page should call require_login() before rendering anything else.
"""
from __future__ import annotations

import streamlit as st

import db


def _bootstrap_form() -> None:
    st.markdown("### Welcome — set up the first admin account")
    st.caption(
        "No brothers are registered yet. Create the president/rush-chair "
        "account first; you can add everyone else from the Admin page."
    )
    with st.form("bootstrap_admin"):
        name = st.text_input("Your name")
        pin = st.text_input("Choose a PIN", type="password")
        pin2 = st.text_input("Confirm PIN", type="password")
        submitted = st.form_submit_button("Create admin account", type="primary")
    if submitted:
        if not name.strip() or not pin:
            st.error("Name and PIN are required.")
        elif pin != pin2:
            st.error("PINs don't match.")
        else:
            member = db.create_member(name, pin, role="admin")
            st.session_state["member"] = {
                "id": member["id"],
                "name": member["name"],
                "role": member["role"],
            }
            st.rerun()


def _login_form() -> None:
    members = db.list_members()
    names = [m["name"] for m in members]

    st.markdown("### Rush Tracker Login")
    with st.form("login"):
        name = st.selectbox("Your name", names)
        pin = st.text_input("PIN", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted:
        member = db.get_member_by_name(name)
        if member and member["pin_hash"] == db.hash_pin(pin):
            st.session_state["member"] = {
                "id": member["id"],
                "name": member["name"],
                "role": member["role"],
            }
            st.rerun()
        else:
            st.error("Wrong PIN.")


def require_login() -> dict:
    """Render the login/bootstrap gate and halt the script until authenticated.

    Returns the logged-in member dict ({"id", "name", "role"}) once past the gate.
    """
    if "member" in st.session_state:
        return st.session_state["member"]

    if not db.is_configured():
        st.error(
            "Rush Tracker isn't connected to its database yet. Add "
            "SUPABASE_URL and SUPABASE_SERVICE_KEY to .streamlit/secrets.toml "
            "(see secrets.toml.example) and rerun the schema in "
            "supabase_schema.sql."
        )
        st.stop()

    _, center, _ = st.columns([1, 2, 1])
    with center:
        if db.has_any_members():
            _login_form()
        else:
            _bootstrap_form()
    st.stop()


def logout() -> None:
    st.session_state.pop("member", None)
    st.rerun()


def is_admin(member: dict) -> bool:
    return member.get("role") == "admin"
