"""Rush Tracker — entry point."""
from __future__ import annotations

import streamlit as st

import auth
import theme
from sections import admin, board, leaderboard, profile, roster

st.set_page_config(page_title="Rush Tracker", page_icon="static/icon-192.png", layout="wide")
theme.apply_theme()
theme.inject_pwa()

member = auth.require_login()

board_page = st.Page(board.render, title="Board", icon="🧑‍🤝‍🧑", default=True)
profile_page = st.Page(profile.render, title="PNM Profile", icon="👤")
st.session_state["_board_page"] = board_page
st.session_state["_profile_page"] = profile_page

pages = [
    board_page,
    profile_page,
    st.Page(leaderboard.render, title="Leaderboard", icon="🏆"),
    st.Page(roster.render, title="Roster / Import", icon="📋"),
]
if auth.is_admin(member):
    pages.append(st.Page(admin.render, title="Admin", icon="🛠️"))

with st.sidebar:
    st.markdown(f"**{member['name']}**")
    st.caption(member["role"])
    if st.button("Log out"):
        auth.logout()

nav = st.navigation(pages)
nav.run()
