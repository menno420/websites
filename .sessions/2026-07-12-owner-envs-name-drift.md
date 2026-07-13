# 2026-07-12 — /owner/environments documented-vs-live variable NAME drift check

> **Status:** `complete` — PR #218, branch `claude/owner-envs-name-drift`;
> lands via the auto-merge-enabler on green.

- **📊 Model:** Claude Fable 5 · worker · feature-slice

**What this session was about:** the gated /owner/environments page holds
both halves of a diff it does not compute — the COMMITTED documented env-var
names per service (`app/railway.py` SERVICES) and the LIVE variable NAMES
Railway reports (`railway.live_overview`, project-scoped token, names never
values). This session builds the comparison: per-service and per-variable
documented-but-missing-live / live-but-undocumented badges, plus an honest
"drift unknown" state with the exact reason whenever Railway is unreachable —
never fabricated. Backlog promotion rung; executes the captured bullet
"/owner/environments drift check: documented vs live variable names"
(`docs/ideas/backlog.md`, source
`.sessions/2026-07-12-order-015-owner-environments.md` 💡). Plumbing follows
PR #216's `envhub.annotate_completeness` annotate/unknown-with-reason idiom;
rendering follows the #213/#217 chip idioms.

## What was done

- **Drift layer** `app/envdrift.py` (new): `annotate(data)` — a pure,
  no-network annotate pass over the `railway.overview()` payload (the #216
  in-place-annotate idiom). Per service: `drift` block with `state`
  (`ok`/`drift`/`unknown`), named `missing_live` / `undocumented` /
  `railway_provided` lists, and a reason on every unknown; per documented
  variable: `live_state` (`set-live`/`missing-live`/`runtime-injected`/
  `unknown`); page-level `drift` rollup with per-direction totals, drifted
  service names, and live services the repo documents nothing about
  (service-level drift). Honesty rules pinned in the docstring + tests:
  live read not `ok` → everything unknown WITH the live reason; a
  per-service variables fetch error → that service unknown, the rest still
  compared; a documented service absent from a SUCCESSFUL read → honest
  drift (not created yet), never unknown. Signal over noise, declared:
  Railway-provided `RAILWAY_*` live names are informational, never drift
  (`RAILWAY_TOKEN` excepted — owner-set, so real drift), and documented
  `PORT` is `runtime-injected`, never missing-live.
- **Route** `app/owner.py` `owner_environments`: one added
  `envdrift.annotate(data)` call after the existing read — GET-rendering
  only, no new routes, CSRF floor untouched.
- **Template** `app/templates/owner_environments.html`: page-level rollup
  chip in the header card (`b ok` "no name drift (N services compared)" /
  `b warn` "name drift" with per-direction counts + drifted/undocumented
  service names / `b unknown` "drift unknown" carrying the reason), a new
  per-variable "live (Railway)?" badge column, and a per-service drift line
  naming the actual variables with fix pointers (set it in the console /
  document it in `app/railway.py` SERVICES) — the #213/#217 chip idioms.
- **Tests** `tests/test_owner_env_drift.py` (16, fully offline — GraphQL
  monkeypatched): all five drift states (no drift / missing-live /
  undocumented / both / unreachable→unknown-with-reason, incl. the no-token
  owner-errand reason), absent-service-is-drift, undocumented live service,
  partial per-service unknown, NAMES-NEVER-VALUES pinned twice (sentinel
  live values asserted absent from the rendered HTML and from the annotated
  payload repr), the /owner gate re-pinned for this page (401 without/wrong
  creds, 503 with SITE_PASSWORD unset), and unit tests for the honesty
  rules (reason carried, RAILWAY_* informational, RAILWAY_TOKEN exception,
  PORT exemption, all-errored → unknown overall).
- **Backlog** `docs/ideas/backlog.md`: the source bullet flipped
  `captured → built` (PR #218); claim file deleted at close.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 835 passed (+16 new), 0 failed, 1 warning;
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  `owner-action-fields` advisory on control/status.md (never
  exit-affecting, not owned here).

**Decisions made:** drift computed in a NEW module `app/envdrift.py` rather
than inside `app/railway.py` — the read layer stays the one place values are
dropped, and the diff logic stays pure/unit-testable (mirrors #216's split:
read in railway, annotate in the consumer); Railway-provided names and PORT
classified informationally rather than reported raw — a drift detector that
always cries drift on Railway's own injected names would train the owner to
ignore it (the exemptions are explicit module constants, not heuristics).

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

**Committed-inventory consistency pin: `railway.SERVICES` vs the envhub
registry** — the repo now hand-keeps TWO committed inventories of the same
four services' variable names (`app/railway.py` SERVICES and
`app/data/environments.json`'s superbot-websites group), and they have
ALREADY drifted: the registry documents `ANTHROPIC_API_KEY` for botsite
while SERVICES does not (verified this session). One zero-network suite test
asserting the two name sets agree per service (or a declared-exceptions
list) would catch repo-internal doc drift the new live check can't see —
the live diff compares each source against Railway, never against each
other. Worth having because both surfaces claim to document the same truth
and their silent divergence makes one of them lie to the owner. Deduped
against `docs/ideas/backlog.md` + the queue-state NEXT list: nothing pins
the two committed inventories to each other. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The /fleet coverage-chip session (#217) did well — its "never a fabricated
zero" honesty ladder (unlistable seats block a green even when everything
listed is complete) is exactly the right strictness, and its card's
"N passed (+M new)" convention made this session's baseline check a
subtraction instead of a re-run; one miss: its rollup chip names incomplete
seats inline but gives no per-lane placement, which it honestly parked as
its own 💡 rather than scope-creeping — nothing it missed affects this lane.
