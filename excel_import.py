"""Flexible Excel roster parsing — PNM spreadsheets rarely use standardized
headers, so map by alias set (same pattern as portfolio_input.py's
_find_column in the Equity Screener app) instead of requiring exact names.
Any column that doesn't match a known field is kept in `extra` so nothing
from the sheet is silently dropped.

Handles real IFC exports: a title row above the true header row, quote
characters embedded in header names, split Firstname/Lastname columns, and
split city/state columns.
"""
from __future__ import annotations

import io
import re
from typing import Iterable

import pandas as pd

NAME_ALIASES = {"name", "fullname", "full_name", "pnm", "pnmname", "pnm_name", "student"}
FIRST_ALIASES = {"firstname", "first", "fname", "givenname"}
LAST_ALIASES = {"lastname", "last", "lname", "surname", "familyname"}
YEAR_ALIASES = {"year", "class", "classyear", "grade", "classification", "yearincollege", "yearinschool"}
MAJOR_ALIASES = {"major", "fieldofstudy", "study"}
HOMETOWN_ALIASES = {"hometown", "city", "hometowncity", "from", "permanentaddresscity"}
STATE_ALIASES = {"state", "hometownstate", "permanentaddressstate"}
HIGH_SCHOOL_ALIASES = {"highschool", "hs", "high_school", "highschoolname"}
NOTES_ALIASES = {"notes", "comments", "note", "remarks", "involvement", "involvements", "about", "bio"}
# Columns dropped entirely on import (internal IDs nobody needs in the app).
IGNORED_ALIASES = {"techniphiid", "techniphi"}

KNOWN_FIELDS: dict[str, set[str]] = {
    "full_name": NAME_ALIASES,
    "first_name": FIRST_ALIASES,
    "last_name": LAST_ALIASES,
    "year": YEAR_ALIASES,
    "major": MAJOR_ALIASES,
    "hometown": HOMETOWN_ALIASES,
    "state": STATE_ALIASES,
    "high_school": HIGH_SCHOOL_ALIASES,
    "notes": NOTES_ALIASES,
}


def _norm_colname(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _find_column(columns: Iterable[str], aliases: set[str]) -> str | None:
    norm_aliases = {_norm_colname(a) for a in aliases}
    for c in columns:
        if _norm_colname(c) in norm_aliases:
            return c
    return None


def read_excel_bytes(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes))
    # Exports often put a title in the first row and the real headers below it;
    # pandas then names most columns "Unnamed: N". Promote the first data row.
    unnamed = sum(1 for c in df.columns if str(c).startswith("Unnamed:"))
    if len(df.columns) and unnamed > len(df.columns) / 2 and len(df):
        df.columns = [str(v).strip() for v in df.iloc[0]]
        df = df.iloc[1:].reset_index(drop=True)
    # Strip stray quotes/whitespace some exports embed in header names.
    df.columns = [re.sub(r'^[\s"\']+|[\s"\']+$', "", str(c)) for c in df.columns]
    return df


def parse_roster(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Map an arbitrary roster DataFrame to Rush Tracker's PNM fields.

    Returns (parsed_df, error). parsed_df has columns:
    full_name, full_name_norm, year, major, hometown, high_school, notes, extra
    """
    columns = list(df.columns)
    col_map = {
        field: _find_column(columns, aliases) for field, aliases in KNOWN_FIELDS.items()
    }

    have_split_name = col_map["first_name"] and col_map["last_name"]
    if not col_map["full_name"] and not have_split_name:
        return pd.DataFrame(), (
            "Couldn't find a name column. Expected a header like "
            "'Name'/'Full Name', or 'Firstname' + 'Lastname' columns."
        )

    mapped_source_cols = {c for c in col_map.values() if c}
    extra_cols = [
        c for c in columns
        if c not in mapped_source_cols and _norm_colname(c) not in IGNORED_ALIASES
    ]

    rows = []
    for _, r in df.iterrows():
        if col_map["full_name"]:
            full_name = _clean(r, col_map["full_name"]) or ""
        else:
            first = _clean(r, col_map["first_name"]) or ""
            last = _clean(r, col_map["last_name"]) or ""
            full_name = f"{first} {last}".strip()
        if not full_name:
            continue

        hometown = _clean(r, col_map["hometown"])
        state = _clean(r, col_map["state"])
        if hometown and state:
            hometown = f"{hometown}, {state}"
        elif state and not hometown:
            hometown = state

        row = {
            "full_name": full_name,
            "full_name_norm": full_name.lower(),
            "year": _clean(r, col_map["year"]),
            "major": _clean(r, col_map["major"]),
            "hometown": hometown,
            "high_school": _clean(r, col_map["high_school"]),
            "notes": _clean(r, col_map["notes"]),
            "extra": {
                str(c): _clean(r, c) for c in extra_cols if _clean(r, c) is not None
            },
        }
        rows.append(row)

    if not rows:
        return pd.DataFrame(), "No rows with a name were found in the sheet."

    return pd.DataFrame(rows), None


def _clean(row: pd.Series, col: str | None):
    if not col:
        return None
    val = row[col]
    if pd.isna(val):
        return None
    val = str(val).strip()
    return val or None
