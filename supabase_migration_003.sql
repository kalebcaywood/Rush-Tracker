-- Migration 003: round-based voting for the 5-day rush schedule.
-- Run once in Supabase SQL Editor (safe to re-run).
--
-- Day 1: meet the PNMs, no voting. Days 2-4: cut votes. Day 5: bid vote.
-- Votes are now unique per (pnm, brother, day) so each day is a fresh round.

create table if not exists app_settings (
    key   text primary key,
    value text not null
);

insert into app_settings (key, value) values ('current_day', '1')
    on conflict (key) do nothing;
insert into app_settings (key, value) values ('voting_open', 'false')
    on conflict (key) do nothing;

alter table votes add column if not exists day int not null default 2;

alter table votes drop constraint if exists votes_pnm_id_member_id_key;
do $$ begin
    alter table votes add constraint votes_pnm_member_day_key
        unique (pnm_id, member_id, day);
exception when duplicate_table or duplicate_object then null;
end $$;
