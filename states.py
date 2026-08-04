"""Normalize messy hometown/state strings to two-letter state codes.

IFC sheets mix 'TN', 'Tennessee', typos ('Tennesee'), zip codes, and
truncations — the board filter and any state rollup should agree on one code.
"""
from __future__ import annotations

import difflib
import re

STATE_NAMES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
    "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
    "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
    "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
    "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN",
    "MISSISSIPPI": "MS", "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE",
    "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK", "OREGON": "OR",
    "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
    "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
}
CODES = set(STATE_NAMES.values()) | {"DC"}


def state_code(hometown: str | None) -> str | None:
    """Best-effort two-letter code from a hometown/state string, else None."""
    s = (hometown or "").strip()
    if not s:
        return None
    if "," in s:
        s = s.rsplit(",", 1)[1]
    s = re.sub(r"\d+", " ", s).strip().upper()  # drop zip codes
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None
    if len(s) == 2 and s in CODES:
        return s
    if s in STATE_NAMES:
        return STATE_NAMES[s]
    # Typos ('TENNESEE', 'VIRGINA', 'ILLNOIS') and near-misses.
    close = difflib.get_close_matches(s, STATE_NAMES.keys(), n=1, cutoff=0.8)
    if close:
        return STATE_NAMES[close[0]]
    return None
