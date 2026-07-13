# 2026-07-12 — Env-hub manifest completeness diff (set-live / missing-live / unknown)

> **Status:** `complete` — PR #216, branch `claude/envhub-completeness-diff`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · websites worker · backlog promotion

**What this session was about:** Merge the slice-1 live Railway variable-NAME
read (`app/railway.py`, project-scoped token, names never values) into the
slice-2 manifest page (`/owner/environments-hub/manifest/{group}`,
`app/envhub.py`) so each env-var schema row is badged **set-live** /
**missing-live**, with an honest **unknown** state when Railway is
unreachable — turning the manifest into the owner's "what's left to finish
this environment" checklist. Rung: backlog promotion — the slice-2 session
card's captured 💡 idea ("Manifest completeness diff") promoted by the
coordinator; NOT the ORDER 021 Discord-auth remainder (rides the existing
HTTP Basic /owner gate unchanged).

## What was done

- **Diff layer** `app/envhub.py`: `annotate_completeness(manifest_data,
  live)` badges every schema row against the `railway.live_overview`
  snapshot (the slice-1 read — values dropped at the client boundary in
  `railway._names_only`, never present here). Honesty rules, pinned in the
  docstring and tests: token unset / read failed / per-service fetch error
  / group outside the token's scope → `unknown` with the exact reason,
  never a fabricated green/red; a service absent from a SUCCESSFUL live
  project read is honestly `missing-live` ("not created yet" — exactly the
  checklist's job); otherwise per-name set-live/missing-live. Group-level
  `completeness` summary (set/known/unknown/total). The copyable plan
  blocks (`commands_text` / `manifest_json`) stay pure committed-registry
  output — completeness is a page annotation, never part of the plan.
- **Route** `app/owner.py` `owner_envhub_manifest`: annotates after
  generation via the EXISTING read-only client (`railway.live_overview`,
  `?refresh=1` honored) — still a read-only GET behind the same
  `require_owner` gate, no new state-changing surface, CSRF untouched.
- **Template** `owner_envhub_manifest.html`: new "live" column on the
  env-var schema table — `set live` (green `b ok`) / `missing live` (red
  `b bad`) / `unknown` (dim `b unknown`); summary line "X/Y set live · Z
  unknown · fetched HH:MM"; when nothing is comparable, a single honest
  "live status unknown — <reason>" line; per-service notes (not created
  yet / read failed) as full-width table rows; "refresh live" headright
  link. Server-rendered, no new JS.
- **Tests** `tests/test_envhub_manifest_completeness.py` (16, fully
  offline, `railway._graphql` mocked): all-present / mixed / absent-service
  / unreachable / token-missing / out-of-scope-group badge states; the
  NAMES-NEVER-VALUES rail (sentinel live values never reach the page or
  the annotated data; `railway._names_only` pinned as the names-only client
  boundary); plan blocks unchanged by annotation; /owner gate pinned
  (401 without/wrong creds, 503 fail-closed).
- **Backlog** `docs/ideas/backlog.md`: the source bullet flipped
  `captured → built` (PR #216) with the shipped shape recorded; the sibling
  `/owner/environments` documented-vs-live drift-check bullet left
  `captured` untouched — it needs its own page/template/data plumbing
  (`railway.SERVICES` vs live, different page), so it shares the concept
  but not most of this build.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 806 passed; `python3 bootstrap.py check --strict` —
  green apart from this card's own designed born-red HOLD (flipped by this
  commit) and pre-existing advisories not owned here
  (`owner-action-fields` on control/status.md).

⚑ Self-initiated: no — coordinator-assigned promotion of the slice-2 card's
captured idea (see `docs/ideas/backlog.md` completeness-diff bullet).

## 💡 Session idea

**Completeness chip on the environments-hub group headers** — reuse
`envhub.annotate_completeness` to render each group's "X/Y set live" (or
"live status unknown") as a chip next to the hub's per-group manifest link.
Worth having because the checklist is one click deep per group — the hub
index is where the owner decides where the next console visit goes, and
today it gives no hint which environment is unfinished. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT baton: nothing touches
hub-level summaries (the projects-registry completeness bullet is a
different page and data source). Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The arcade live-URL drift probe (#214) did well — fail-soft per-URL probing
with `httpx.MockTransport` tests and honest "not probed" for unavailable
entries; it missed the claims README's close-out step: its
`control/claims/arcade-url-drift-probe.md` is still on main, which tripped
a `claims-duplicate` advisory against this session's claim until this
claim's file-area token was narrowed.
