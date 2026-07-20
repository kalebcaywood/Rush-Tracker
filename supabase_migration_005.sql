-- Migration 005: rounds within a rush day.
-- Run once in Supabase SQL Editor (safe to re-run).
--
-- PNMs visit the house in scheduled rounds (time slots) each day; the paper
-- sheet says who comes in which round. Attendance rows now carry the round
-- so the slideshow can present round by round.

alter table attendance add column if not exists round int not null default 1;
