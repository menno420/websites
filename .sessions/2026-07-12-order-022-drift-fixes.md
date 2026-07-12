# 2026-07-12 — ORDER 022 drift fixes: mineverse live card + Railway query verification + ledger reconcile

> **Status:** `complete` — PR branch `claude/order-022-drift-fixes`, parks
> READY + green for the auto-merge enabler (build worker; merge is
> deliberately not this session's call).

- **📊 Model:** claude-fable-5 · build worker · order

**What this session was about:** ORDER 022 items 1, 2 and 4 (ledger part)
(fleet-manager `control/inbox.md` @ `1bb53f9`): the mineverse arcade card
still said "Not deployed yet" while the game is live; `app/railway.py`'s
GraphQL shapes were still marked UNVERIFIED although RAILWAY_TOKEN now
exists; and `docs/owner/OWNER-ACTIONS.md` carried satisfied asks
(RAILWAY_TOKEN, ANTHROPIC_API_KEY) as open/pending.

## What was done

- **Arcade card flipped honest-LIVE** — `botsite/data/arcade.json`
  mineverse: `availability` → `live`, `url` →
  `https://web-production-97636.up.railway.app` (the loader appends
  `?ref=fleet-arcade`), description/status_note rewritten to the truthful
  "read-only demo — player sign-in launching". Cold-verified today:
  HTTP 200, title "Mineverse — mining economy viewer". Tests adjusted +
  a new `test_arcade_mineverse_live_link` asserting the playable link with
  the attribution ref; the other two cards' honest labels untouched.
- **Railway GraphQL shapes verified live, verdict already-correct** — ran
  the three `app/railway.py` queries against the real
  backboard.railway.app/graphql/v2 schema: `projectToken` exposes
  `projectId`/`environmentId`; `project(id:)` returns
  `name` + `services.edges[].node{id,name}` (four services);
  `variables(projectId:,environmentId:,serviceId:)` returns a flat
  name→value map (names kept, values dropped in `_names_only`). Updated
  the stale UNVERIFIED docstring + the stale "owner errand pending"
  RAILWAY_TOKEN purpose string; added
  `test_query_shapes_match_verified_live_schema` pinning the verified
  shapes against a real-shaped fixture (names only, fake values).
- **Ledger reconcile** — `docs/owner/OWNER-ACTIONS.md`: RAILWAY_TOKEN ask
  and ANTHROPIC_API_KEY ask struck to Decided rows L/K (ask text kept
  verbatim, per the row-J pattern); row J re-confirmed with today's
  `/healthz` 200 + readiness deploy-drift all-four-`in_sync` at
  `e25d7d58`; review-service ask found already fully struck — no change.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — all passed; `python3 bootstrap.py check --strict` —
  all checks passed.

⚑ Self-initiated: no — ORDER 022 (fleet-manager `control/inbox.md` @
`1bb53f9`); the one extra touch (the stale RAILWAY_TOKEN purpose string in
`app/railway.py`) is the same drift class the order targets, one string,
reversible.

## 💡 Session idea

**Arcade live-URL drift probe** — a tiny network-marked test or CI cron
step that cold-fetches every `availability: live` URL in
`botsite/data/arcade.json` and fails/flags when one stops returning 200,
so a dead game link can never quietly outlive its card. Worth having
because the arcade's honesty doctrine currently depends on manual
reconciles like ORDER 022 noticing drift by hand. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: no existing bullet
covers arcade URL liveness. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The 16:49Z records reconcile did the review-service strike cleanly (row J
with verbatim text kept — the pattern this session reused), but left the
ANTHROPIC_API_KEY ask half-closed ("reported RESOLVED" pending a
verification nobody was assigned) — this session closed it.
