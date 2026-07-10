# websites — ideas backlog

> **Status:** `ideas` — the single backlog list (rung 3 of the work ladder,
> `docs/project/project-instructions.md`). One bullet per idea (or one file in
> this directory + a bullet here). Dedup before adding; states per `README.md`:
> `captured → planned → built → retired`. Seeded 2026-07-10 from the ideas
> already scattered across session cards, the queue-state NEXT list, and the
> retros — each with its source cited.

## Captured / planned (pick highest-value buildable first)

- **`/fleet` badge: "manifest live parse: last verified \<age\>"** · `captured`
  — `resolve_lanes()` already returns `lane_source`; surface manifest-sourced
  vs fallback on the page itself so the owner sees it without knowing
  `scripts/healthcheck.py` exists. Likely a template tweak. Source:
  `.sessions/2026-07-10-order008-first-fire-manifest-smoke.md` 💡.
- **Re-check closed-unmerged PR #9 branch `claude/rework-dashboard` for lost
  hardening work** · `captured` — #9 was closed superseded in the
  parallel-checkout churn (`docs/retro/self-review-2026-07-09.md` A4) but the
  branch is still live on the remote (`docs/CAPABILITIES.md` append log
  2026-07-10 `list_branches`); the launch-readiness flag (coordinator dispatch,
  2026-07-10) asks whether hardening in it never landed via #10. Diff it
  against `main`, salvage or retire explicitly.
- **Per-repo `?repo=` filter on the activity views** · `captured` — narrow
  `/activity`, `/activity.json`, `/activity.xml` to one repo so a reader
  subscribes to a single lane's feed; reuses the cached timeline. File:
  [activity-per-repo-filter-2026-07-09.md](activity-per-repo-filter-2026-07-09.md).
- **kit-version rollup on `/fleet`** · `captured` — summary header
  (`kit: 4×v1.6.0, 2×v1.2.0, 3×none`) + per-card badge over the
  already-parsed `kit:` line; pure presentation, zero new fetch. Sources:
  `.sessions/2026-07-09-kit-upgrade-v1.6.0.md` 💡; queue-state NEXT item 5.
- **"Unseen orders?" badge on `/fleet`** · `captured` — flag a lane whose
  `inbox.md` last-commit is newer than its status `updated:` stamp. Sources:
  `.sessions/2026-07-09-kit-upgrade-v1.6.0.md` ⟲ review; queue-state NEXT
  item 5.
- **`/queue.json` + manager round-trip check** · `captured` — JSON variant of
  the owner queue so the manager can machine-verify a filed ask actually
  surfaces (write → poll → confirm); ~10 lines over the existing `overview()`
  dict. Source: `.sessions/2026-07-10-order-005-queue-environments.md` 💡.
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
- **"Stalled claim" aging on `/orders`** · `captured` — badge a claimed
  order whose `claimed-by:` ISO stamp is older than ~24h with `claim stale?`
  (the claim ritual's own expiry rule — a dead lane must never deadlock an
  order); `/orders` makes claims visible but not their age, and the claim
  line already carries the timestamp, so this is pure presentation (needs
  `parse_orders` to also extract the claim timestamp). Source:
  `.sessions/2026-07-10-orders-visibility.md` 💡.
- **`meta.md` state-line convention in the fleet-manager projects/ registry**
  · `captured` — ask the manager to standardize ONE `deployed:` line format
  in `projects/*/meta.md` (e.g. `deployed: <where> · <ISO date>`) while the
  registry is still forming; `/projects` extracts the state badge with
  tolerant heuristics against an unborn format, and one line agreed at
  zero-packages cost makes the badge exact forever (routing half: flagged to
  the manager in the heartbeat notes). Source:
  `.sessions/2026-07-10-order-009-projects.md` 💡.
- **Own-heartbeat parse self-check in `quality`** · `captured` — a small test
  that runs this repo's own `control/status.md` through the `/fleet` parsers
  (`parse_status` → `parse_orders` / `classify_routine` / `classify_landing`)
  and asserts the machine-readable lines actually parse (orders `ok=True`,
  known keys don't leak into `blockers:` as continuations), so a malformed
  heartbeat is caught at PR time instead of rendering wrong on the live fleet
  page (before the enrichment decision the `routine:` line leaked into
  `blockers:` for hours — exactly this class). Dogfood pair to the heartbeat
  enrichment shipped below. Source:
  `.sessions/2026-07-10-heartbeat-enrichment.md` 💡.
- **Ladder-rung telemetry in the heartbeat** · `captured` — one `rung:` token
  per wake (which work-ladder rung fired) so the manager sees at a glance
  whether a lane is living off orders or self-generated work, and backlog
  dryness becomes a trend, not a one-off line. Source:
  `.sessions/2026-07-10-never-idle-work-ladder.md` 💡 (this session).
- **Open-PR awareness at wake (sibling-session collision check)** · `captured`
  — one wake-ritual step listing open PRs + PR-less unmerged `claude/*`
  branches before picking a work rung, so concurrent sessions stop duplicating
  builds / conflicting on shared files / raising false rescue alarms (the
  order-claim fix, applied to branches). Distinct from heartbeat enrichment's
  `landing:` line, which covers a session's OWN branch only. File:
  [open-pr-awareness-at-wake-2026-07-10.md](open-pr-awareness-at-wake-2026-07-10.md).

## Built

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

(None yet — retire with one line of why, never delete silently.)
