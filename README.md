# Rush Tracker

A rush program for the chapter: import the PNM roster from Excel, upload
daily photos, and let every brother comment and vote — all in one place,
accessible from anyone's phone.

## What it is

- **Board** — grid of every PNM with their latest photo and live average score.
- **PNM Profile** — a PNM's info, daily photo gallery, comment feed, and a
  1–5 star vote (one per brother, visible to everyone).
- **Leaderboard** — sortable ranking across all PNMs for building the bid list.
- **Roster / Import** — upload an Excel sheet to bulk-load PNMs (re-uploading
  the same sheet updates existing entries instead of duplicating them), or
  add one manually.
- **Admin** (president/rush chairs only) — add/remove brothers, reset PINs,
  delete PNMs, and export everything to CSV as a manual backup.

## One-time setup

### 1. Create a free Supabase project

Go to [supabase.com](https://supabase.com), create a free project, then:

1. Open **SQL Editor** → New query → paste the contents of
   [`supabase_schema.sql`](supabase_schema.sql) → Run.
2. Open **Storage** → New bucket → name it exactly `pnm-photos` → leave
   **Public bucket** OFF.
3. Open **Settings → API** and copy the **Project URL** and the
   **service_role** secret key (not the `anon` key).

### 2. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill
in the two values from step 1. This file is gitignored — never commit it.

### 3. Install & run locally

```
pip install -r requirements.txt
streamlit run app.py
```

The first person to open the app creates the initial admin account
(that should be you, the president). Add the rest of the chapter from the
**Admin** page — each brother gets a name + PIN they'll use to log in.

## Deploying to Streamlit Community Cloud

1. Push this repo to a new GitHub repository.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app
   pointing at that repo, branch `main`, main file `app.py`.
3. In the app's **Settings → Secrets**, paste the same two keys as your
   local `secrets.toml`.
4. Share the resulting `*.streamlit.app` URL with the chapter — works from
   any phone browser, no install needed.

## Notes

- Every brother's vote and comment is attributed and visible to everyone —
  there's no anonymous mode.
- Photos and data live in Supabase (Postgres + Storage), not on Streamlit's
  local disk, so they survive app restarts/redeploys during rush week.
- The **Admin → Backup** button exports every table to CSV at any time as
  an extra safety net.
