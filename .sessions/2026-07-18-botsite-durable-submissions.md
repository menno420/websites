# 2026-07-18 — botsite durable /submit storage (ORDER 034)

> **Status:** `in-progress` — branch `claude/botsite-durable-submissions`;
> flips to `complete` + PR number as the deliberate LAST code step.

**Order:** ORDER 034 · **Ask:** ASK-0004 · **Date:** 2026-07-18
**Branch:** `claude/botsite-durable-submissions`
**Provenance:** LIVE OWNER ORDER 2026-07-18 — "for #5, that's a job for you" (#5 = the botsite submissions Postgres / DATABASE_URL owner item), delegated to the seat in the coordinator chat.

## Goal
Make the public `/submit` intake persist durably. Wire it to a real database selected by `DATABASE_URL` (PostgreSQL in production once Railway provisions it; SQLite for CI/local), fail-soft to the current "intake not live" behavior when `DATABASE_URL` is unset. Provision the Postgres DB in the `superbot-websites` Railway project and set `DATABASE_URL` on the `botsite` service (`botsite-production-cfd7`).

## Plan
- New `botsite/submissions_store.py`: DATABASE_URL-keyed store (Postgres via psycopg / SQLite), per-call connect, idempotent table create, `is_live()` / `create_submission()` / `list_submissions()`.
- `/submit` POST: same-origin guard (CSRF floor) + read form (kind/title/body) + persist when live + `intake_live`/`accepted` flags.
- `submit.html`: success branch when a submission is accepted.
- Owner-authed `GET /submit/queue.json` read-back (moderation-queue seed).
- Pin `psycopg[binary]` in `botsite/requirements.txt`.
- Tests exercise the SQLite path (network-free), mirroring `test_testing.py`.

## Verify
`python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q` and `python3 bootstrap.py check --strict`; live probe of `/submit` on `botsite-production-cfd7` after DATABASE_URL is set.

## Notes
- Deferred (flagged): porting the 979-line `/testing` SQLite store to Postgres — larger, higher-risk; a mechanical follow-up once DATABASE_URL exists.
