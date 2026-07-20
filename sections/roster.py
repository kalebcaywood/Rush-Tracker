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
    st.markdown("#### Daily attendance (who came back today)")
    st.caption(
        "Upload the day's returning-PNM sheet. The order of the sheet becomes "
        "the slideshow order, and the Voting queue follows the same order — "
        "brothers only vote on PNMs who actually came through that day."
    )
    day = db.current_day()
    att_day = st.selectbox(
        "Attendance for", [1, 2, 3, 4, 5],
        index=day - 1 if 1 <= day <= 5 else 0,
        format_func=lambda d: db.DAY_LABELS.get(d, f"Day {d}"),
    )
    existing = db.attendance_pnm_ids(att_day)
    if existing:
        st.caption(f"{len(existing)} PNMs currently marked as attending Day {att_day}. Re-uploading replaces the list.")
    upload_tab, paste_tab = st.tabs(["Upload .xlsx", "Paste names (from the paper sheet)"])

    with upload_tab:
        att_file = st.file_uploader("Day's returning PNMs (.xlsx)", type=["xlsx"], key="att_upload")
        if att_file:
            try:
                att_raw = excel_import.read_excel_bytes(att_file.getvalue())
            except Exception as e:
                st.error(f"Couldn't read that file: {e}")
                att_raw = None
            if att_raw is not None:
                att_parsed, att_err = excel_import.parse_roster(att_raw)
                if att_err:
                    st.error(att_err)
                else:
                    index = excel_import.build_name_index(db.list_pnms())
                    matched, unmatched = [], []
                    for _, r in att_parsed.iterrows():
                        p = excel_import.match_name(r["full_name"], index)
                        (matched.append(p) if p else unmatched.append(r["full_name"]))
                    st.success(f"Matched {len(matched)} PNMs against the roster.")
                    if unmatched:
                        with st.expander(f"{len(unmatched)} name(s) not matched — they'll be skipped"):
                            st.write(", ".join(unmatched))
                    if matched and st.button(
                        f"Save Day {att_day} attendance ({len(matched)} PNMs)", type="primary"
                    ):
                        n = db.set_attendance(att_day, [p["id"] for p in matched])
                        st.success(f"Saved: {n} PNMs attending Day {att_day}, in sheet order.")
                        st.rerun()

    with paste_tab:
        st.caption(
            "Type or paste the names from the paper sheet, one per line, in "
            "order. Start each group with a line like 'Round 2'. Middle names "
            "aren't needed — 'Aaren Quintavalle' finds 'Aaren Michael Quintavalle'."
        )
        pasted = st.text_area(
            "Names", key="att_paste", height=220,
            placeholder="Round 1\nAaren Quintavalle\nBrady Smith\n\nRound 2\nCarson Lee",
            label_visibility="collapsed",
        )
        if pasted.strip():
            import re as _re

            index = excel_import.build_name_index(db.list_pnms())
            entries, unmatched = [], []
            rnd = 1
            for line in pasted.splitlines():
                s = line.strip().strip(",;")
                if not s:
                    continue
                m = _re.match(r"(?i)^round\s*#?\s*(\d+)\b", s)
                if m:
                    rnd = int(m.group(1))
                    continue
                p = excel_import.match_name(s, index)
                (entries.append((p["id"], rnd)) if p else unmatched.append(s))
            rounds = sorted({r for _, r in entries})
            st.success(
                f"Matched {len(entries)} PNMs"
                + (f" across rounds {', '.join(map(str, rounds))}" if len(rounds) > 1 else "")
                + "."
            )
            if unmatched:
                with st.expander(f"{len(unmatched)} name(s) not matched — fix spelling or skip"):
                    st.write(", ".join(unmatched))
            if entries and st.button(
                f"Save Day {att_day} attendance ({len(entries)} PNMs)",
                type="primary", key="save_paste",
            ):
                n = db.set_attendance(att_day, entries)
                st.success(f"Saved: {n} PNMs attending Day {att_day}.")
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
