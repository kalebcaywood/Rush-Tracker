-- Migration 004: daily attendance — who came back each day, in sheet order.
-- Run once in Supabase SQL Editor (safe to re-run).
--
-- The exec uploads each day's returning-PNM sheet; the slideshow presents
-- them in this order and the Voting queue follows the same order.

create table if not exists attendance (
    id          uuid primary key default gen_random_uuid(),
    pnm_id      uuid not null references pnms(id) on delete cascade,
    day         int not null,
    position    int not null default 0,
    created_at  timestamptz not null default now(),
    unique (pnm_id, day)
);

create index if not exists attendance_day_idx on attendance (day);
