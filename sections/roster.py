"""Upload/preview/import a PNM roster from Excel; manual add-PNM form."""
from __future__ import annotations

import streamlit as st

import db
import excel_import
from sections.profile import PNM_ID_KEY


def render() -> None:
    # Belt-and-suspenders: navigation only shows this page to admins, but
    # guard here too in case the URL is hit directly.
    import auth

    if not auth.is_admin(st.session_state.get("member", {})):
        st.info("The roster import is admin-only. Ask an exec if something needs updating.")
        return

    st.markdown("## Roster / Import")

    st.markdown("#### Import from Excel")
    st.caption(
        "Upload a .xlsx roster. Column headers can be anything reasonable "
        "(Name/Full Name, Year/Class, Major, Hometown, High School, Notes) "
        "— re-uploading the same sheet updates existing PNMs by name instead "
        "of duplicating them."
    )
    file = st.file_uploader("Roster file", type=["xlsx"])
    if file:
        try:
            raw_df = excel_import.read_excel_bytes(file.getvalue())
        except Exception as e:
            st.error(f"Couldn't read that file: {e}")
            return

        parsed, error = excel_import.parse_roster(raw_df)
        if error:
            st.error(error)
            return

        st.success(f"Found {len(parsed)} PNM(s) in the sheet. Preview below.")
        st.dataframe(parsed.drop(columns=["full_name_norm"]), use_container_width=True)

        if st.button("Import into Rush Tracker", type="primary"):
            rows = parsed.to_dict(orient="records")
            n = db.upsert_pnms(rows)
            st.success(f"Imported {n} PNM(s).")
            st.rerun()

    st.divider()
    st.markdown("#### Add a PNM manually")
    with st.form("manual_add_pnm", clear_on_submit=True):
        c1, c2 = st.columns(2)
        full_name = c1.text_input("Full name")
        year = c2.text_input("Year")
        c3, c4 = st.columns(2)
        major = c3.text_input("Major")
        hometown = c4.text_input("Hometown")
        high_school = st.text_input("High school")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add PNM", type="primary")
    if submitted:
        if not full_name.strip():
            st.error("Name is required.")
        else:
            db.upsert_pnms([{
                "full_name": full_name.strip(),
                "full_name_norm": full_name.strip().lower(),
                "year": year or None,
                "major": major or None,
                "hometown": hometown or None,
                "high_school": high_school or None,
                "notes": notes or None,
                "extra": {},
            }])
            st.success(f"Added {full_name}.")
            st.rerun()

    st.divider()
    st.markdown("#### Current roster")
    pnms = db.list_pnms()
    if not pnms:
        st.caption("No PNMs yet.")
        return
    st.caption(
        f"{len(pnms)} PNMs loaded. Open any PNM from the **Board** page "
        "(use search to jump straight to a name)."
    )
    import pandas as pd

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Name": p["full_name"],
                    "Year": p.get("year"),
                    "Hometown": p.get("hometown"),
                    "High school": p.get("high_school"),
                    "Status": p.get("status", "active").title(),
                }
                for p in pnms
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
