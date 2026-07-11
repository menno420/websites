# websites — ideas backlog

> **Status:** `ideas` — the single backlog list (rung 3 of the work ladder,
> `docs/project/project-instructions.md`). One bullet per idea (or one file in
> this directory + a bullet here). Dedup before adding; states per `README.md`:
> `captured → planned → built → retired`. Seeded 2026-07-10 from the ideas
> already scattered across session cards, the queue-state NEXT list, and the
> retros — each with its source cited.

## Captured / planned (pick highest-value buildable first)

- **Nav overflow guard** · `captured` — the header nav now carries ten
  links and each fleet-info slice added one; on a phone the wrap costs
  multiple rows and usability decays one link at a time with nobody's slice
  feeling responsible. A grouped/overflow ("more ▾") treatment or a CSS
  audit at current width keeps the owner's phone glance usable. Source:
  `.sessions/2026-07-10-activity-repo-filter.md` 💡.
- **"Unseen orders?" badge on `/fleet`** · `captured` — flag a lane whose
  `inbox.md` last-commit is newer than its status `updated:` stamp. Sources:
  `.sessions/2026-07-09-kit-upgrade-v1.6.0.md` ⟲ review; queue-state NEXT
  item 5.
- **`scripts/wait-deploy.py` post-merge sha-convergence poller** · `captured` —
  poll all three `/version` endpoints until `sha` == a given commit or
  timeout; turns the manual "merge = deploy" verification loop into a
  deterministic PASS/FAIL. Source:
  `.sessions/2026-07-10-gen2-walking-skeleton.md` 💡.
- **Review-queue row auto-check for this repo's own PRs** · `captured` — a
  script / advisory quality step computing a merged PR's runtime changed-line
  count against the fleet review-queue's BINDING 50-line rule and printing
  "this PR needs a review-queue row" when it qualifies; the rule's
  enforcement is currently memory (116 merged PRs / zero rows was the
  documented failure state; this repo's #67 and #72 both qualified unflagged
  — row-appending is a fleet-manager write this lane can't do, but knowing a
  row is owed can be mechanical). Source:
  `.sessions/2026-07-10-order-009-reviews.md` 💡.
- **`meta.md` state-line convention in the fleet-manager projects/ registry**
  · `captured` — ask the manager to standardize ONE `deployed:` line format
  in `projects/*/meta.md` (e.g. `deployed: <where> · <ISO date>`) while the
  registry is still forming; `/projects` extracts the state badge with
  tolerant heuristics against an unborn format, and one line agreed at
  zero-packages cost makes the badge exact forever (routing half: flagged to
  the manager in the heartbeat notes). Source:
  `.sessions/2026-07-10-order-009-projects.md` 💡.
- **Ladder-rung telemetry in the heartbeat** · `captured` — one `rung:` token
  per wake (which work-ladder rung fired) so the manager sees at a glance
  whether a lane is living off orders or self-generated work, and backlog
  dryness becomes a trend, not a one-off line. Source:
  `.sessions/2026-07-10-never-idle-work-ladder.md` 💡 (this session).
- **Backlog fact-check pass before promoting a bullet** · `captured` — one
  grep/route-check against the codebase for what a bullet asks for BEFORE
  branching on it; a stale `captured` bullet costs a whole duplicate slice in
  continuous mode (the /fleet manifest-badge bullet outlived its own build —
  shipped as the PR #36 lane_source notice — by 12+ hours and nearly got
  rebuilt in slice 7). The dedup rule covers new ideas, not decayed old ones.
  Source: `.sessions/2026-07-10-own-heartbeat-selfcheck.md` 💡.
- **Open-PR awareness at wake (sibling-session collision check)** · `captured`
  — one wake-ritual step listing open PRs + PR-less unmerged `claude/*`
  branches before picking a work rung, so concurrent sessions stop duplicating
  builds / conflicting on shared files / raising false rescue alarms (the
  order-claim fix, applied to branches). Distinct from heartbeat enrichment's
  `landing:` line, which covers a session's OWN branch only. File:
  [open-pr-awareness-at-wake-2026-07-10.md](open-pr-awareness-at-wake-2026-07-10.md).

## Built

- **Same-shape contract tests for /orders.json, /queue.json, /projects.json,
  /reviews.json** — shipped 2026-07-11 (continuous-mode slice 11):
  `tests/test_json_contracts.py` pins every payload's key sets (cards/orders,
  items/sources/fleet_manager, packages/files, rows/links) with named-key
  drift messages and rendered-HTML-absence asserts; companion to the
  /fleet.json pin. Update the pinned sets in the same PR that changes a
  payload. Source: `.sessions/2026-07-10-fleet-json-contract.md` 💡.

- **Per-repo `?repo=` filter on the activity views** — shipped 2026-07-11
  (continuous-mode slice 10; decision stamped in `docs/site.md` § 2 + the
  decision ledger): /activity, /activity.json, /activity.xml narrow to one
  fleet repo (filtered case fetches only that repo; the Atom feed becomes a
  per-lane subscription with the repo in its title; unknown repo = honest
  empty state). File:
  [activity-per-repo-filter-2026-07-09.md](activity-per-repo-filter-2026-07-09.md).

- **`/fleet.json` shape-contract test** — shipped 2026-07-10 (continuous-mode
  slice 9): `tests/test_fleet_json_contract.py` pins the exact key sets of
  the /fleet.json payload (top level, summary incl. kit_versions, every lane
  incl. orders_info/routine_info/landing_info, and the degraded-lane
  same-shape guarantee) — any key add/remove/rename goes red BY NAME; update
  the pinned sets in the same PR that changes the payload. Source:
  `.sessions/2026-07-10-fleet-polish-batch.md` 💡.

- **Fleet polish batch: stalled-claim aging on `/orders` + `/queue.json` +
  kit-version rollup on `/fleet`** — shipped 2026-07-10 (continuous-mode
  slice 8; decision stamped in the decision ledger; details in
  `docs/site.md` §§ 3a/3f/Routes). Three captures closed in one batch, zero
  new fetches: `parse_orders` extracts `claimed_at` and claimed orders badge
  `claim stale?` past 24h (the ritual's expiry rule); `/queue.json` gives
  the manager the file-an-ask → poll → confirm round-trip; `/fleet` header
  shows "kit adoption: N×vX.Y.Z · M×none" over readable heartbeats.

- **Own-heartbeat parse self-check in `quality`** — shipped 2026-07-10
  (continuous-mode slice 7): `tests/test_own_heartbeat.py` runs the REAL
  committed `control/status.md` through the `/fleet` parsers every suite run
  — required fields present, `updated:` parses, `health:` classifies,
  `orders:` machine-readable, optional `routine:`/`landing:` lines classify,
  and no enriched key leaks into `blockers:` as a continuation (the
  pre-enrichment failure class). Honest scope: heartbeat-only PRs ride the
  control fast lane and skip pytest, so a bad heartbeat reds the NEXT
  non-control PR — a standing floor, not same-PR enforcement. Source:
  `.sessions/2026-07-10-heartbeat-enrichment.md` 💡.

- **Per-repo inbox ORDER visibility on the site** — shipped 2026-07-10
  (continuous-mode slice 6; decision stamped in `docs/site.md` § 3f + the
  decision ledger): `/orders` (+ `.json`) parses every fleet repo's
  `control/inbox.md` ORDER blocks and cross-references each id against the
  repo's own heartbeat `done=`/`claimed-by:` lines (one parser — the
  heartbeat enrichment's `parse_orders`) into done / claimed / open /
  unknown badges, attention-sorted with fleet-wide roll-ups. Source at
  capture: `control/inbox.md` ORDER 009 audit.
- **ORDER 009 increment (3): review-queue rows + findings links** — shipped
  2026-07-10 (continuous-mode slice 5; decision stamped in `docs/site.md`
  § 3e + the decision ledger): `/reviews` (+ `.json`) renders the
  fleet-manager post-merge review-queue ledger — open rows as cards with
  `repo#N` deep-linked, struck rows classified reviewed, findings/records
  links extracted from the doc itself (never hardcoded), full ledger
  rendered below; empty/not-configured/unavailable degradation. Increment
  (1) `/projects` shipped earlier the same day; increment (2) verified
  already-covered on `/fleet`. Source: `control/inbox.md` ORDER 009.

- **Scheduled healthcheck workflow (standing liveness verification)** —
  shipped 2026-07-10 (backlog promotion, 20:00Z continuous-mode wake slice 3;
  retro F3): `.github/workflows/healthcheck.yml`, cron every 6 h (minute-17
  offset) + `workflow_dispatch`, runs `scripts/healthcheck.py` (three live
  services `/healthz` + `/` 200, plus the `/fleet` manifest live-parse smoke
  check); read-only, no secret, NOT a required check — failure notifies via
  the failed-workflow email. File:
  [scheduled-healthcheck-workflow-2026-07-10.md](scheduled-healthcheck-workflow-2026-07-10.md).
- **Heartbeat enrichment: machine-readable fields in `control/status.md`** —
  shipped 2026-07-10 (decision stamped in `docs/site.md` § 3a + the decision
  ledger; queue-state NEXT item 4, retro G3): `/fleet`
  parses `orders:` (outstanding = acked minus done, ranges expanded,
  `claimed-by:` captured) + the new OPTIONAL `routine:` / `landing:` /
  `deployed:` lines (documented in `control/README.md`); armed-but-silently-dead
  routines and stranded (`LOCAL-ONLY` / pushed-unmerged) landings badge and
  sort attention-first; `/fleet.json` carries the parsed structures. Folded in
  both sibling captures (`routine:` — `.sessions/2026-07-10-gen2-closeout-docs.md`
  💡; `landing:` — `.sessions/2026-07-10-rescue-landing-project-package.md` 💡).
- **`.sessions/` card template with `📊 Model:` line + ender checklist** —
  shipped 2026-07-10 (queue-state NEXT item 3): copy-paste template + ender
  checklist embedded in `.sessions/README.md` (embedded there on purpose — the
  session gate treats any other `.sessions/*.md` as a card, so a standalone
  TEMPLATE.md would itself go born-red). The 💡 section carries the required
  one-line "worth having because" prompt. Sources at capture:
  `docs/planning/queue-state-2026-07-09-winddown.md` NEXT item 3;
  `.sessions/2026-07-10-gen2-walking-skeleton.md` ⟲ review.
- **`/activity.xml` Atom feed** — shipped; see the decision ledger +
  `docs/site.md`. File:
  [activity-atom-feed-2026-07-09.md](activity-atom-feed-2026-07-09.md).

## Retired

- **Re-check closed-unmerged PR #9 branch `claude/rework-dashboard` for lost
  hardening work** — retired 2026-07-11 (slice 11 investigation, nothing to
  salvage): the branch shares NO merge base with main (parallel-checkout
  root); its only unique hardening commit `a0b459f` ("drop literal
  control-API env-var name from served HTML; extend denylist test to
  templates") is fully superseded on main by PR #10 — verified by diff:
  main's `dashboard/tests/test_dashboard.py::test_no_control_api_token_or_url_anywhere`
  scans `*.py` AND `*.html` with the same denylist, and a repo-wide grep
  finds ZERO forbidden literals in shipped dashboard files. The branch's
  other commits are the superseded parallel dashboard build PR #8 replaced.
  Branch stays on the remote (branch deletion is a documented 403 wall,
  `docs/CAPABILITIES.md`) — safe to prune whenever someone with delete
  rights sweeps; nothing on it is needed.

- **`/fleet` badge: "manifest live parse: last verified \<age\>"** — retired
  2026-07-10 (slice 7 fact-check): already shipped — `fleet.html` has
  rendered `lane_source` on the page since the PR #36 manifest work ("lane
  set: live from manifest — N lanes parsed" vs the fallback banner), which is
  exactly the surfacing this capture asked for; verified in the template +
  covered by `test_fleet_overview_is_manifest_sourced`. Nothing to build.
