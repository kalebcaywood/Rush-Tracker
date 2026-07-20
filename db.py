"""Supabase client + all CRUD for Rush Tracker.

Every call runs server-side inside the Streamlit process using the
service_role key (never sent to the browser). The app's login gate is the
only access-control boundary — same trust model as a single-password-gated
internal tool.
"""
from __future__ import annotations

import hashlib
import os
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st
from supabase import Client, create_client

PHOTO_BUCKET = "pnm-photos"


def _secret(key: str) -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return os.environ.get(key, "").strip()


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL / SUPABASE_SERVICE_KEY. Add them to "
            ".streamlit/secrets.toml (see secrets.toml.example)."
        )
    return create_client(url, key)


def is_configured() -> bool:
    try:
        get_client()
        return True
    except Exception:
        return False


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.strip().encode()).hexdigest()


# ─── Members ──────────────────────────────────────────────────────────────
def list_members() -> list[dict]:
    res = get_client().table("members").select("*").order("name").execute()
    return res.data or []


def has_any_members() -> bool:
    res = get_client().table("members").select("id").limit(1).execute()
    return bool(res.data)


def get_member_by_name(name: str) -> dict | None:
    res = (
        get_client()
        .table("members")
        .select("*")
        .eq("name", name)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_member(name: str, pin: str, role: str = "brother") -> dict:
    row = {"name": name.strip(), "pin_hash": hash_pin(pin), "role": role}
    res = get_client().table("members").insert(row).execute()
    return res.data[0]


def update_member_pin(member_id: str, pin: str) -> None:
    get_client().table("members").update({"pin_hash": hash_pin(pin)}).eq(
        "id", member_id
    ).execute()


def delete_member(member_id: str) -> None:
    get_client().table("members").delete().eq("id", member_id).execute()


# ─── PNMs ─────────────────────────────────────────────────────────────────
def list_pnms() -> list[dict]:
    res = get_client().table("pnms").select("*").order("full_name").execute()
    return res.data or []


def get_pnm(pnm_id: str) -> dict | None:
    res = get_client().table("pnms").select("*").eq("id", pnm_id).limit(1).execute()
    return res.data[0] if res.data else None


def create_pnm(fields: dict) -> dict:
    res = get_client().table("pnms").insert(fields).execute()
    return res.data[0]


def update_pnm(pnm_id: str, fields: dict) -> None:
    get_client().table("pnms").update(fields).eq("id", pnm_id).execute()


def delete_pnm(pnm_id: str) -> None:
    get_client().table("pnms").delete().eq("id", pnm_id).execute()


PNM_STATUSES = ["active", "cut", "bid"]


def set_pnm_status(pnm_id: str, status: str) -> None:
    if status not in PNM_STATUSES:
        raise ValueError(f"Bad status: {status}")
    get_client().table("pnms").update({"status": status}).eq("id", pnm_id).execute()


def upsert_pnms(rows: list[dict]) -> int:
    """Insert new PNMs / update existing ones, matched by normalized full_name.

    Returns the number of rows written.
    """
    if not rows:
        return 0
    res = (
        get_client()
        .table("pnms")
        .upsert(rows, on_conflict="full_name_norm")
        .execute()
    )
    return len(res.data or [])


# ─── Photos ───────────────────────────────────────────────────────────────
def upload_photo(
    pnm_id: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    uploaded_by: str,
    day: date | None = None,
    caption: str | None = None,
) -> dict:
    day = day or date.today()
    storage_path = f"{pnm_id}/{day.isoformat()}_{filename}"
    get_client().storage.from_(PHOTO_BUCKET).upload(
        storage_path,
        file_bytes,
        {"content-type": content_type, "upsert": "true"},
    )
    row = {
        "pnm_id": pnm_id,
        "storage_path": storage_path,
        "day": day.isoformat(),
        "caption": caption,
        "uploaded_by": uploaded_by,
    }
    res = get_client().table("pnm_photos").insert(row).execute()
    return res.data[0]


def list_photos(pnm_id: str) -> list[dict]:
    res = (
        get_client()
        .table("pnm_photos")
        .select("*")
        .eq("pnm_id", pnm_id)
        .order("day", desc=True)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


@st.cache_data(ttl=1800, show_spinner=False)
def signed_url(storage_path: str) -> str | None:
    try:
        res = (
            get_client()
            .storage.from_(PHOTO_BUCKET)
            .create_signed_url(storage_path, 3600)
        )
        return res.get("signedURL") or res.get("signedUrl")
    except Exception:
        return None


def most_recent_photo(pnm_id: str) -> dict | None:
    photos = list_photos(pnm_id)
    return photos[0] if photos else None


# ─── Comments ─────────────────────────────────────────────────────────────
def add_comment(
    pnm_id: str, member_id: str, body: str, flag: str | None = None
) -> dict:
    row = {"pnm_id": pnm_id, "member_id": member_id, "body": body.strip()}
    if flag in ("red", "green"):
        row["flag"] = flag
    res = get_client().table("comments").insert(row).execute()
    return res.data[0]


def set_comment_flag(comment_id: str, flag: str | None) -> None:
    get_client().table("comments").update({"flag": flag}).eq("id", comment_id).execute()


def flag_counts() -> dict[str, dict[str, int]]:
    """pnm_id -> {'red': n, 'green': n} across all flagged comments."""
    try:
        rows = get_client().table("comments").select("pnm_id, flag").execute().data or []
    except Exception:
        return {}  # flag column not migrated yet — degrade gracefully
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.get("flag") in ("red", "green"):
            counts = out.setdefault(r["pnm_id"], {"red": 0, "green": 0})
            counts[r["flag"]] += 1
    return out


def list_comments(pnm_id: str) -> list[dict]:
    res = (
        get_client()
        .table("comments")
        .select("*, members(name)")
        .eq("pnm_id", pnm_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


# ─── Votes ────────────────────────────────────────────────────────────────
def upsert_vote(pnm_id: str, member_id: str, score: int) -> None:
    row = {
        "pnm_id": pnm_id,
        "member_id": member_id,
        "score": score,
        "updated_at": pd.Timestamp.utcnow().isoformat(),
    }
    get_client().table("votes").upsert(row, on_conflict="pnm_id,member_id").execute()


def get_my_vote(pnm_id: str, member_id: str) -> dict | None:
    res = (
        get_client()
        .table("votes")
        .select("*")
        .eq("pnm_id", pnm_id)
        .eq("member_id", member_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def list_votes(pnm_id: str) -> list[dict]:
    res = (
        get_client()
        .table("votes")
        .select("*, members(name)")
        .eq("pnm_id", pnm_id)
        .execute()
    )
    return res.data or []


def my_voted_pnm_ids(member_id: str) -> set[str]:
    res = (
        get_client().table("votes").select("pnm_id").eq("member_id", member_id).execute()
    )
    return {r["pnm_id"] for r in (res.data or [])}


def all_votes() -> list[dict]:
    res = get_client().table("votes").select("pnm_id, member_id, score").execute()
    return res.data or []


# ─── Aggregates (computed client-side — dataset is small enough) ─────────
def leaderboard_df() -> pd.DataFrame:
    client = get_client()
    pnms = list_pnms()
    if not pnms:
        return pd.DataFrame(
            columns=["PNM", "Status", "Avg Score", "# Votes", "# Comments",
                     "🚩", "✅", "Last Activity"]
        )

    votes = client.table("votes").select("pnm_id, score, updated_at").execute().data or []
    comments = (
        client.table("comments").select("pnm_id, created_at").execute().data or []
    )
    flags = flag_counts()

    votes_df = pd.DataFrame(votes)
    comments_df = pd.DataFrame(comments)

    rows = []
    for p in pnms:
        pv = votes_df[votes_df["pnm_id"] == p["id"]] if not votes_df.empty else votes_df
        pc = (
            comments_df[comments_df["pnm_id"] == p["id"]]
            if not comments_df.empty
            else comments_df
        )
        last_vote = pv["updated_at"].max() if not pv.empty else None
        last_comment = pc["created_at"].max() if not pc.empty else None
        last_activity = max([t for t in [last_vote, last_comment] if t], default=None)
        pf = flags.get(p["id"], {})
        rows.append(
            {
                "PNM": p["full_name"],
                "Status": p.get("status", "active").title(),
                "Avg Score": round(pv["score"].mean(), 2) if not pv.empty else None,
                "# Votes": len(pv),
                "# Comments": len(pc),
                "🚩": pf.get("red", 0),
                "✅": pf.get("green", 0),
                "Last Activity": last_activity,
            }
        )

    df = pd.DataFrame(rows)
    return df.sort_values("Avg Score", ascending=False, na_position="last").reset_index(
        drop=True
    )


def export_all_csv() -> dict[str, bytes]:
    """Return a dict of filename -> CSV bytes for every table, for manual backup."""
    client = get_client()
    out = {}
    for table in ["members", "pnms", "pnm_photos", "comments", "votes"]:
        data = client.table(table).select("*").execute().data or []
        df = pd.DataFrame(data)
        out[f"{table}.csv"] = df.to_csv(index=False).encode("utf-8")
    return out
