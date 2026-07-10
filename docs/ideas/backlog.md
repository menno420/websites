# websites — ideas backlog

> **Status:** `ideas` — the single backlog list (rung 3 of the work ladder,
> `docs/project/project-instructions.md`). One bullet per idea (or one file in
> this directory + a bullet here). Dedup before adding; states per `README.md`:
> `captured → planned → built → retired`. Seeded 2026-07-10 from the ideas
> already scattered across session cards, the queue-state NEXT list, and the
> retros — each with its source cited.

## Captured / planned (pick highest-value buildable first)

- **Heartbeat enrichment: machine-readable fields in `control/status.md`** ·
  `planned` — outstanding-orders + deployed-sha/last-verified-live per lane so
  `/fleet` computes "what's left" without diffing inbox vs status vs git.
  Fold in two sibling captures: a `routine:` line (`armed · cron · last-fired`,
  surfacing "armed but silently dead" wake clocks;
  `.sessions/2026-07-10-gen2-closeout-docs.md` 💡) and a `landing:` line
  (`all-merged | branch pushed-unmerged | LOCAL-ONLY`, the mechanical catch for
  the 16:01Z stranded-work incident;
  `.sessions/2026-07-10-rescue-landing-project-package.md` 💡). Sources:
  queue-state NEXT item 4 (retro G3).
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
- **Scheduled healthcheck workflow (standing liveness verification)** ·
  `captured` — Actions cron runs `scripts/healthcheck.py` every 6 h, fails
  loudly on non-200; closes the "liveness unverified at handover" class (retro
  F3: Actions cron is the one scheduler agents can arm themselves). File:
  [scheduled-healthcheck-workflow-2026-07-10.md](scheduled-healthcheck-workflow-2026-07-10.md).
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
