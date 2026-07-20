"""Rush Tracker — entry point."""
from __future__ import annotations

import streamlit as st

import auth
import theme
from sections import admin, board, leaderboard, my_activity, profile, roster, slideshow, voting

st.set_page_config(page_title="Rush Tracker", page_icon="static/icon-192.png", layout="wide")
theme.apply_theme()
theme.inject_pwa()

member = auth.require_login()

# Every render function is named "render", so each page needs an explicit
# url_path — st.navigation otherwise derives all five from the function name
# and rejects the duplicates.
board_page = st.Page(board.render, title="Board", url_path="board", default=True)
profile_page = st.Page(profile.render, title="PNM Profile", url_path="pnm")
st.session_state["_board_page"] = board_page
st.session_state["_profile_page"] = profile_page

pages = [
    board_page,
    st.Page(voting.render, title="Voting", url_path="voting"),
    profile_page,
    st.Page(leaderboard.render, title="Leaderboard", url_path="leaderboard"),
    st.Page(my_activity.render, title="My Activity", url_path="my-activity"),
]
if auth.is_admin(member):
    pages.append(st.Page(slideshow.render, title="Slideshow", url_path="slideshow"))
    pages.append(st.Page(roster.render, title="Roster / Import", url_path="roster"))
    pages.append(st.Page(admin.render, title="Admin", url_path="admin"))

with st.sidebar:
    st.markdown(f"**{member['name']}**")
    if st.button("Log out"):
        auth.logout()

nav = st.navigation(pages)
nav.run()
