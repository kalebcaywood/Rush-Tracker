"""Lightweight UT-styled theme for Rush Tracker."""
from __future__ import annotations

import streamlit as st

UT_ORANGE = "#FF8200"
UT_SMOKEY = "#58595B"
UT_WHITE = "#FFFFFF"
UT_DARK = "#1A1A1A"


def apply_theme() -> None:
    st.markdown(
        f"""
<style>
.stApp {{ background: #f7f7f5; }}
h1, h2, h3 {{ color: {UT_DARK}; }}
[data-testid="stSidebar"] {{ background: {UT_DARK}; }}
[data-testid="stSidebar"] * {{ color: {UT_WHITE} !important; }}
.stButton>button[kind="primary"] {{
    background: {UT_ORANGE}; border-color: {UT_ORANGE}; color: white;
}}
.stButton>button[kind="primary"]:hover {{
    background: #e07500; border-color: #e07500;
}}
.pnm-card {{
    border: 1px solid #e2e2e0; border-radius: 10px; padding: 12px;
    background: white; margin-bottom: 12px;
}}
.score-badge {{
    display: inline-block; background: {UT_ORANGE}; color: white;
    border-radius: 6px; padding: 2px 8px; font-weight: 600; font-size: 0.9em;
}}
/* Phone layout: let Streamlit columns wrap instead of squeezing.
   Board cards go 2-up on phones; paired form fields stack full-width. */
@media (max-width: 640px) {{
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        min-width: calc(50% - 0.5rem); flex: 1 1 calc(50% - 0.5rem);
    }}
    .block-container {{ padding-left: 1rem; padding-right: 1rem; padding-top: 2.5rem; }}
    h1 {{ font-size: 1.5rem; }}
    h2 {{ font-size: 1.25rem; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
