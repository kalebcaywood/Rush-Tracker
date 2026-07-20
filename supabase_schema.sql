-- Rush Tracker schema. Paste this into the Supabase project's SQL editor
-- (Database > SQL Editor > New query) and run it once.
--
-- After running this, also create a Storage bucket named "pnm-photos":
--   Storage > New bucket > name "pnm-photos" > Public bucket: OFF (private).
-- The app uses the service_role key server-side and generates short-lived
-- signed URLs to display photos, so the bucket does not need to be public
-- and no Storage RLS policies are required for the service_role key.

create extension if not exists "pgcrypto";

create table if not exists members (
    id          uuid primary key default gen_random_uuid(),
    name        text not null unique,
    pin_hash    text not null,
    role        text not null default 'brother' check (role in ('admin', 'brother')),
    created_at  timestamptz not null default now()
);

create table if not exists pnms (
    id              uuid primary key default gen_random_uuid(),
    full_name       text not null,
    full_name_norm  text generated always as (lower(trim(full_name))) stored,
    year            text,
    major           text,
    hometown        text,
    high_school     text,
    notes           text,
    extra           jsonb not null default '{}'::jsonb,
    status          text not null default 'active' check (status in ('active', 'cut', 'bid')),
    created_at      timestamptz not null default now()
);

create unique index if not exists pnms_full_name_norm_idx on pnms (full_name_norm);

create table if not exists pnm_photos (
    id             uuid primary key default gen_random_uuid(),
    pnm_id         uuid not null references pnms(id) on delete cascade,
    storage_path   text not null,
    day            date not null default current_date,
    caption        text,
    uploaded_by    uuid references members(id) on delete set null,
    created_at     timestamptz not null default now()
);

create index if not exists pnm_photos_pnm_id_idx on pnm_photos (pnm_id);

create table if not exists comments (
    id          uuid primary key default gen_random_uuid(),
    pnm_id      uuid not null references pnms(id) on delete cascade,
    member_id   uuid not null references members(id) on delete cascade,
    body        text not null,
    flag        text check (flag in ('red', 'green')),
    created_at  timestamptz not null default now()
);

create index if not exists comments_pnm_id_idx on comments (pnm_id);

create table if not exists votes (
    id          uuid primary key default gen_random_uuid(),
    pnm_id      uuid not null references pnms(id) on delete cascade,
    member_id   uuid not null references members(id) on delete cascade,
    score       int not null check (score between 1 and 5),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    unique (pnm_id, member_id)
);

create index if not exists votes_pnm_id_idx on votes (pnm_id);
