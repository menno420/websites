# 2026-07-09 — Hardening + verification batch (P0-verify · P1a/b/c · P2-verify · OWNER-ACTIONS)

> **Status:** `in-progress` — born-red first commit. Verifies #16's
> definition-of-done, adds an enforcing guard against the ambient production
> Railway IDs, a reusable 3-URL healthcheck, strengthens the stub labels, and
> seeds the OWNER-ACTIONS living doc. Flip to `complete` last.

## About to do

- **P0** — verify #16 DoD on live main (session_count, UNRENDERED banners in the
  8 binding docs, `quality.yml` green). Report DONE/remainder.
- **P1a** — `scripts/check_no_ambient_railway_ids.py` enforcing guard + test,
  wired into `quality.yml`; loud `docs/RAILWAY-SAFETY.md` + deployment warning.
- **P1b** — verify + strengthen the two stub labels (`/admin`, `/submit`).
- **P1c** — `scripts/healthcheck.py` (3 live URLs) + run it + document.
- **P2** — verify the readiness board renders live signals for all four repos.
- **OWNER-ACTIONS** — `docs/owner/OWNER-ACTIONS.md` living decision list.
- `[D-0015]` hardening-pass decision; `current-state.md` update.
