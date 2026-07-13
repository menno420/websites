# 2026-07-13 — ORDER 026: Railway env-var placeholders — create nothing (findings landed)

> **Status:** `in-progress`

- **📊 Model:** Claude Fable 5 · worker · order-slice

**What this session was about:** ORDER 026 (`control/inbox.md`, owner
verbatim: "can you create the placeholders for me on railway") — pre-create
the missing env-var entries on the Railway services so the owner only pastes
values. Outcome of the discovery + one probe attempt: **create nothing**, for
two independent reasons; the order's own done-when ("envhub honesty
preserved" / "unwritable → exact denial recorded in docs/CAPABILITIES.md")
is satisfied by landing the findings instead.

## The decision — create nothing, two independent reasons

1. **Honesty guard.** The Railway variables read returns a name→value map,
   but `app/railway.py` `_names_only()` drops the values at the client
   boundary — envdrift (`app/envdrift.py`) and envhub badge any existing
   NAME as `set-live`. An empty placeholder is therefore indistinguishable
   from a real credential and permanently blinds the owner's only
   missing-vs-set signal on `/owner/environments`. Additionally, empty
   values would hard-crash control-plane/botsite/dashboard at import
   (`int("")` on the CACHE_TTL-style vars, e.g. `app/config.py:83`) and
   would silently blank URL-default vars (`GITHUB_API_BASE`,
   `SITE_JSON_URL`, …).
2. **Write wall.** The single probe attempt (a `variableUpsert` of
   `PLACEHOLDER_PROBE` on the dashboard service) was denied BEFORE reaching
   Railway by the agent session's permission classifier — verbatim denial
   quoted in the new `docs/CAPABILITIES.md` entry. This confirms the
   `docs/RAILWAY-SAFETY.md` policy wall at the harness level; capability
   against the Railway API itself remains UNTESTED.

## What was done

- `docs/CAPABILITIES.md` — new 2026-07-13 append-log entry: the verbatim
  harness denial (Railway never reached, API write capability UNTESTED),
  the `_names_only` honesty finding, and the empty-value crash hazard.
- `docs/owner/OWNER-ACTIONS.md` — Decided row N: placeholders deliberately
  NOT created; the owner pastes REAL values directly (the
  `/owner/environments` checklist lists exactly which names are missing per
  service: 11 control-plane / 16 botsite / 5 dashboard / 2 review). Plus a
  ground-truth flag on row K: the 2026-07-13 live names read (names only,
  never values) shows ANTHROPIC_API_KEY ABSENT on superbot-websites/botsite
  and an undocumented SITE_PASSWORD on dashboard (drift).
- Nothing was created, changed, or deleted on Railway. No code changes;
  `app/data/environments.json` untouched.
