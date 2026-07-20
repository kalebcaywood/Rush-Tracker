-- Migration 002: bid-list workflow + comment flags.
-- Run once in Supabase SQL Editor (safe to re-run).
--
-- Adds:
--   pnms.status      — 'active' (default) | 'cut' | 'bid'
--   comments.flag    — null | 'red' | 'green'

alter table pnms
    add column if not exists status text not null default 'active'
        check (status in ('active', 'cut', 'bid'));

alter table comments
    add column if not exists flag text
        check (flag in ('red', 'green'));
