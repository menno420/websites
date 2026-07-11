# websites — ideas backlog

> **Status:** `ideas` — the single backlog list (rung 3 of the work ladder,
> `docs/project/project-instructions.md`). One bullet per idea (or one file in
> this directory + a bullet here). Dedup before adding; states per `README.md`:
> `captured → planned → built → retired`. Seeded 2026-07-10 from the ideas
> already scattered across session cards, the queue-state NEXT list, and the
> retros — each with its source cited.

## Captured / planned (pick highest-value buildable first)

- **Flag to kit lane: `upgrade --apply-docs` rewrites `.substrate/upgrade-report.md`
  without the Carve-out scan section** · `retired` (fixed upstream in kit #176;
  verified live on this repo's v1.10.0 upgrade, PR #105 — `--apply-docs` rode
  the upgrade invocation and the carve-out section survived natively) —
  originally verified live on the v1.9.0 upgrade (this repo, PR #101): the
  main upgrade pass wrote the #156-mandated explicit carve-out section, then
  the post-hoc `--apply-docs` pass regenerated the report with only the docs
  table + an "Applied" section, silently dropping the carve-out audit record
  (hand-restored here). Source: `.sessions/2026-07-11-kit-upgrade-v1.9.0.md` 💡.

- **Flag to kit lane: model-doctrine idempotence phrase-match should be
  emphasis-insensitive** · `retired` (fixed upstream in kit #187, shipped in
  v1.10.1; verified live on this repo's v1.10.1 upgrade, PR #113 —
  `.sessions/README.md` byte-identical across the upgrade, no new append) —
  originally verified live on the v1.10.0 upgrade
  (this repo, PR #105): websites' `.sessions/README.md` already carried the
  hand-merged doctrine from #101, but with bold markers inside the sentence
  (`family-level model name **your own harness/environment reports this
  session**`), so `_merge_model_doctrine`'s exact-substring detection phrase
  missed it and appended a second, near-duplicate doctrine paragraph
  (harmless — append-only + provenance-marked — but noise on every adopter
  that hand-merged before the retroactive pass). The detector should
  normalize markdown emphasis (`*`/`_`) away before phrase matching. Source:
  `.sessions/2026-07-11-kit-upgrade-v1.10.0.md` 💡.

- **Apply the HANDOFF read-first line to the live `.claude/CLAUDE.md` via
  `upgrade --apply-docs`** · `captured` — the v1.11.0 upgrade report (PR
  #129) classes the live working agreement as "consumer-untouched + template
  improved — safe to apply with `upgrade --apply-docs`": one flag-run adopts
  the staged orientation change (read boot-generated `HANDOFF.md` before
  re-deriving history from `git log`) into the file agents actually boot
  from. The v1.11.0 HANDOFF composer only pays off once sessions are told to
  read it — the live orientation list still routes agents straight to
  `current-state.md`. Out of the distribution lane's scope (live CLAUDE.md is
  host-owned); a websites session should run it deliberately and diff-review.
  Source: `.sessions/2026-07-11-kit-upgrade-v1.11.0.md` 💡.

- **Ask the manager for a generated `lanes.json`** · `captured` — /fleet
  now parses the LANES literal out of fleet-manager's gen_roster.py source
  (honest but coupled to a script's internals); one generated
  docs/lanes.json (repo, lane, disposition) from the same roster run makes
  the registry a real API and the next migration a non-event (the
  manifest→roster move broke this site once already, caught by the cron).
  Routing half: flagged to the manager in the heartbeat. Source:
  `.sessions/2026-07-11-lane-source-registry.md` 💡.
- **Backlog low-water signal in the heartbeat** · `captured` — when the
  captured+planned count drops below ~3, the heartbeat notes carry
  `backlog: low (N left)` so the manager routes work BEFORE a lane hits
  upkeep-dry (routing latency beats idle wakes); rung telemetry records
  which rung fired, not depth. Source:
  `.sessions/2026-07-11-fleet-chip-tooling-token.md` 💡.
- **`meta.md` state-line convention in the fleet-manager projects/ registry**
  · `captured` — ask the manager to standardize ONE `deployed:` line format
  in `projects/*/meta.md` (e.g. `deployed: <where> · <ISO date>`) while the
  registry is still forming; `/projects` extracts the state badge with
  tolerant heuristics against an unborn format, and one line agreed at
  zero-packages cost makes the badge exact forever (routing half: flagged to
  the manager in the heartbeat notes). Source:
  `.sessions/2026-07-10-order-009-projects.md` 💡.
- **Order-ack latency line in the heartbeat** · `captured` — ORDER 011
  sat 17 minutes between filing (09:59Z) and claim (10:16Z) purely
  because a send_later nudge happened to fire; an
  `orders-latency: <id> filed→claimed <mins>` heartbeat line (or /orders
  surfacing per-repo filed→claimed deltas from the two files it already
  parses) would let the manager MEASURE each lane's order-pickup latency
  instead of inferring it across control/inbox.md and control/status.md
  timestamps. Worth having because pickup latency is the fleet's real
  routing SLO and today it is invisible. Source:
  `.sessions/2026-07-11-order-011-self-review.md` 💡.
- **Inbox relay-order provenance check** · `captured` — the inbox
  grammar gate now enforces SHAPE (append-only + well-formed ORDER
  blocks) but not SOURCE: any green-lane PR author can append a
  well-formed ORDER and it reads as manager-issued (ORDER blocks carry
  a provenance: field, but nothing validates it against the relay/PR
  author). A cheap next rung: the gate warns (advisory, not red) when
  an appended ORDER's provenance: line names no session/coordinator id
  — keeps the order-of-record honest without blocking legitimate
  relays. Worth having because the gates just made the inbox TRUSTED
  input, and trusted input attracts spoofing. Source:
  `.sessions/2026-07-11-control-gate-tests.md` 💡.
- **Port the clock-freeze pattern to botsite/dashboard if they grow
  age-measuring code** · `captured` — premise-checked: TODAY neither
  botsite/app.py nor dashboard/app.py measures ages against the wall
  clock (no datetime.now in either — verified by grep this slice), so
  there is nothing to port YET; this bullet exists so the first
  age-measuring feature in either service starts from app/clock.py's
  pattern instead of re-learning the 08:45Z lesson. Worth having
  because the failure class is service-agnostic and the fix is one
  small module. Source: `.sessions/2026-07-11-route-clock-freeze.md` 💡.
- **Nav membership scan should glob `app/*.py`, not a hand list** ·
  `captured` — `tests/test_nav_manifest.py` scans a hand-kept
  `ROUTE_SOURCES = [app/main.py, app/owner.py]` for `active` keys: the
  guard against hand-kept nav lists itself contains a hand-kept module
  list, so splitting routes into a new module silently exits the scan.
  Glob `app/*.py` (cheap, source-text scan) or enumerate `app.routes`.
  Worth having because self-maintaining guards should not have the
  exact failure mode they guard against. Source:
  `.sessions/2026-07-11-nav-manifest.md` 💡.
- **Control-gate suite tests** — shipped 2026-07-11 (continuous-mode
  slice 26): tests/test_control_gates.py drives the real
  `check --strict --status-only [--inbox-base]` CLI against a synthetic
  fixture install, pinning FIVE lanes (clean 0 / broken heartbeat 1 /
  inbox rewrite 1 / pure append 0 / malformed append 1 — the grammar
  lane was found while prototyping). Source:
  `.sessions/2026-07-11-fastlane-control-gates.md` 💡.

- **Fast-lane control gates in quality.yml** — shipped 2026-07-11
  (continuous-mode slice 25): the control fast lane no longer
  short-circuits green unvalidated — a control-status gate runs ON the
  fast lane (stdlib-only --status-only; heartbeat PRs stay fast and
  card-free) and an inbox append-only + ORDER-grammar gate runs on BOTH
  lanes (--inbox-base vs merge-base; self-skips when the inbox is
  untouched). All four lane behaviors validated locally pre-push.
  Source: `.sessions/2026-07-11-quality-every-card-gate.md` 💡.

- **Nav manifest** — shipped 2026-07-11 (continuous-mode slice 24):
  `app/nav.py` is the single `(href, label, key)` source for the header
  nav; base.html iterates it via Jinja globals, the overflow tests
  import it, and `tests/test_nav_manifest.py` holds every route's
  `active` key to it (membership + uniqueness + no-dead-entries) — page
  12 physically cannot skip the overflow guard. Source:
  `.sessions/2026-07-11-nav-overflow-guard.md` 💡.

- **quality.yml every-card session gate** — shipped 2026-07-11
  (continuous-mode slice 23): the folded lane's `tail -1` single-card
  picker (multi-card shadowing loophole) replaced with the staged
  substrate-gate.yml every-card loop — added cards get the per-card
  born-red HOLD lane (siblings advisory), modified-only diffs get the
  locked door per card, no-card diffs use the explicit advisory
  sentinel, and PRs touching the gate file keep the full locked door +
  --simulate-added-card (semantics only tighten mid-PR); gate_regen
  path adapted to quality.yml; validated live on the port PR's own
  runs. Source: `.sessions/2026-07-11-kit-upgrade-v1.10.1.md` 💡.

- **Time-discipline guard for tests** — shipped 2026-07-11
  (continuous-mode slice 21): `tests/test_time_discipline.py` AST-scans
  the suite and fails any call to an age-measuring entry point
  (`fleet.overview`/`lane_status`/`freshness`/`heartbeat_freshness`,
  `orders.overview`/`classify_order`) without a frozen `now=`; first run
  caught 17 latent sites across 5 files, all threaded with frozen NOW
  constants; `heartbeat_freshness` + `orders.overview` gained the
  module-standard injectable `now=`. Source:
  `.sessions/2026-07-11-current-state-truth-sweep.md` 💡.

- **Nav overflow guard** — shipped 2026-07-11 (continuous-mode slice 19, the
  last buildable captured bullet): secondary pages (environments, projects,
  reviews, orders, ideas) grouped under a no-JS `<details>` "more ▾" nav
  dropdown — top-level links 11 → 6; every page stays reachable; a grouped
  page's active state opens the group and highlights the summary; pure
  HTML/CSS, no dependency. Source:
  `.sessions/2026-07-11-activity-repo-filter.md` 💡.

- **Board-row fleet chip (heartbeat freshness on the habit path)** — shipped
  2026-07-11 (continuous-mode slice 18): each board repo row shows its
  lane's heartbeat age/stale badge via `fleet.heartbeat_freshness` (only the
  board repos' status.md files over the TTL cache — deliberately not the
  18-lane overview fan-out); no readable/parseable heartbeat → no chip,
  never a guessed age. Source:
  `.sessions/2026-07-11-board-conveyor-chips.md` 💡.
- **`tooling:` capability token in fired heartbeats** — shipped 2026-07-11
  (slice 18): optional `tooling: pr-capable | ritual-only` status line
  (control/README.md + fleet.KNOWN_KEYS leak-guard + /fleet row flagging
  ritual-only as "cannot land work"); this repo's heartbeat writes it from
  this wake on. Source:
  `.sessions/2026-07-11-relay-doctrine-backlog-factcheck.md` 💡.

- **Conveyor-health chips on the readiness board rows** — shipped 2026-07-11
  (continuous-mode slice 17): each board row with a readable ideas dir shows
  lifecycle count chips (deep-linked to the /ideas ?state= filters), reusing
  the exact TTL-cached /ideas fetch path; a repo with no/unreadable ideas
  shows no chip (the board stays a readiness surface — /ideas holds the
  honest absence); /api/readiness.json untouched (pinned by test). Source:
  `.sessions/2026-07-11-ideas-states-waitdeploy.md` 💡.

- **Relay-PR merge protocol on the bus** — shipped 2026-07-11 (continuous-mode
  slice 15): doctrine section "Landing other sessions' control-only work" in
  `control/README.md` — any session may land a green control-only relay or
  stranded heartbeat verbatim (one WRITER, not one MERGER); generalized from
  two same-night incidents (relay PR #94; 04:03Z heartbeat rescued as PR #98).
  Source: `.sessions/2026-07-11-order-010-and-tooling.md` 💡.
- **Backlog fact-check pass before promoting a bullet** — shipped 2026-07-11
  (slice 15): the habit line lives in `docs/ideas/README.md` § Lifecycle
  ("fact-check before promoting"), and the first full pass was executed the
  same slice (verdicts: unseen-orders badge retired as superseded; nav guard
  + board chips + meta.md convention confirmed still-live). Source:
  `.sessions/2026-07-10-own-heartbeat-selfcheck.md` 💡.

- **Cron-slot helper** — shipped 2026-07-11 (continuous-mode slice 14) as
  `scripts/cron_slots.py`: 5-field cron → next wall-clock UTC fire slots
  (loud on malformed, never a guess); the incident case (`17 */6 * * *`
  after 21:03Z → 00:17Z, not "+6h") is a pinned test. Source:
  `.sessions/2026-07-11-open-work-rung-cronfinding.md` 💡.
- **Review-queue row auto-check** — shipped 2026-07-11 (slice 14) as
  `scripts/review_row_check.py`: sums runtime/product changed lines over a
  git range with the ledger's exact exclusions (docs/, control/,
  .sessions/, tests, markdown; binary counts 0) and prints ROW OWED past
  the binding 50-line threshold; first live run confirmed #81's squash owes
  a row. Row-appending stays a fleet-manager write — flag to the manager.
  Source: `.sessions/2026-07-10-order-009-reviews.md` 💡.

- **`/ideas` state filter (conveyor health)** — shipped 2026-07-11
  (continuous-mode slice 13): each idea's front-matter `state:` surfaces as
  a badge, per-repo captured/planned/built/retired/unstated counts (honest
  scope: the newest enriched files), and a `?state=` filter that narrows the
  list but never the counts; unknown states flag, never guess. Source:
  `.sessions/2026-07-11-json-contracts-pr9-retire.md` 💡.
- **`scripts/wait-deploy.py` post-merge sha-convergence poller** — shipped
  2026-07-11 (slice 13) as `scripts/wait_deploy.py`: poll all three
  `/version` endpoints until sha == a given commit or timeout — one
  deterministic PASS/FAIL instead of hand-curling (first live run:
  CONVERGED in one poll at 7f948445). Source:
  `.sessions/2026-07-10-gen2-walking-skeleton.md` 💡.

- **Open-PR awareness at wake** — shipped 2026-07-11 (continuous-mode slice
  12): `scripts/open_work.py` classifies every remote `claude/*`/`manager/*`
  branch as PR-OPEN (leave to its session) / PR-LESS (rescue candidate) /
  MERGED-STALE (prune candidate) / PR-UNKNOWN (api wall — labeled, never
  guessed); run at session start before picking a rung. First live run
  surfaced exactly the four gen-1 leftover branches. File:
  [open-pr-awareness-at-wake-2026-07-10.md](open-pr-awareness-at-wake-2026-07-10.md).
- **Ladder-rung telemetry in the heartbeat** — shipped 2026-07-11 (slice 12):
  optional `rung:` status line (documented in `control/README.md`, in
  `fleet.KNOWN_KEYS` so it can never leak into the previous field — the
  routine:-line incident class — and rendered as a /fleet row when present);
  this repo's heartbeat writes it from this wake on. Source:
  `.sessions/2026-07-10-never-idle-work-ladder.md` 💡.

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

- **"Unseen orders?" badge on `/fleet`** — retired 2026-07-11 (slice 15
  fact-check pass): superseded by `/orders` (decision home `docs/site.md`
  § 3f) — the badge would have flagged "inbox commit newer than status
  updated:" as a heuristic; /orders now computes the actual outstanding
  orders per repo (done/claimed/open/unknown badges + fleet-wide roll-up),
  strictly stronger than the commit-time proxy. Nothing left to build.

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
