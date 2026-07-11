# websites · status
updated: 2026-07-11T02:35:00Z
phase: CONTINUOUS MODE (manager Q-0265): 02:22Z nudge — slice 12 landed: #90 (wake-tooling batch: scripts/open_work.py open-branch classifier; rung: heartbeat telemetry line; healthcheck-cron NO-SHOW captured as a provisional CAPABILITIES wall). ⚠ FINDING: the healthcheck cron has produced ZERO scheduled runs (only dispatch run 1) — the record's "~02:17Z" was a cron-arithmetic error (17 */6 anchors to hours 0/6/12/18; real first slot 00:17Z, which also did not fire); verdict at the 06:17Z slot — a second no-show makes it a real wall and wake-run healthchecks become the doctrine. Wake running total: 12 work slices (#64, #67, #69, #72, #75, #77, #79, #81, #83, #86, #88, #90).
health: green (main HEAD 47b6168 at write; suites 212 passed; bootstrap check --strict green under kit v1.8.0; control-plane /version == 47b6168 == main HEAD verified 02:34:04Z; healthcheck.py itself 6/6 PASS when last run — the workflow SCHEDULE is what's unproven)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #90 — wake-tooling batch (open_work.py's first live run surfaced exactly the four gen-1 leftover branches, zero false alarms).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~04:00Z. send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90; next nudge armed ~02:55Z. Actions cron healthcheck: SCHEDULE UNPROVEN (see phase) — next verdict slot 06:17Z.
landing: all-merged — every branch this chain opened is squash-merged (#64→#90 series); the four gen-1 leftover branches are classified prune-candidates (open_work.py output on the #90 card).
deployed: 47b6168 · verified 2026-07-11T02:34:04Z — control-plane /version == main HEAD.
rung: backlog
orders: acked=001,002,003,004,005,006,007,008,009 done=001,002,003,004,005,006,007,008,009
⚑ needs-owner: two asks — canonical list in docs/owner/OWNER-ACTIONS.md.
  ⚑ OWNER-ACTION
  WHAT: Create a small Postgres for the botsite /submit intake and point the botsite service at it.
  WHERE: railway.app → project superbot-websites → New → Database → PostgreSQL; then service botsite → Variables.
  HOW: add variable DATABASE_URL = the new Postgres connection string Railway shows (copy-paste).
  WHY-IT-MATTERS: the public feature/bug submission form is a labeled stub until a store exists.
  UNBLOCKS: the moderated submissions queue + GitHub-issue mirror (rework Q5) — agent-buildable the moment the variable exists.
  VERIFIED-NEEDED: provisioning creates a paid resource in your Railway account and D-0005 forbids agent-initiated Railway mutations without your explicit go — policy wall, deliberately not attempted; no DATABASE_URL exists on the service today.
  ⚑ OWNER-ACTION
  WHAT: Mint a durable fine-grained GitHub PAT and set it on the control-plane service.
  WHERE: github.com → Settings → Developer settings → Fine-grained tokens; then railway.app → superbot-websites → control-plane → Variables.
  HOW: token scoped to menno420 repos, read for contents/actions + actions:write for the CI re-run button; set as GITHUB_TOKEN (exact steps: docs/deployment.md § owner TODO).
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces run live tokenless on the anonymous 60-req/h ceiling; headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) HEALTHCHECK CRON WATCH — zero scheduled runs so far; verdict at 06:17Z (fleet-relevant: if new-workflow crons silently don't fire, every lane arming Actions schedules inherits the trap; evidence in docs/CAPABILITIES.md). (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81/#86 borderline). (3) STALE-BRANCH PRUNE list stands (open_work.py now makes it mechanical). (4) rung: telemetry is live — this heartbeat carries the first `rung:` line; /fleet renders it. (5) Q-0264 candidates now fourteen in docs/ideas/backlog.md (newest: cron-slot helper; /ideas state filter). NEXT picks: healthcheck verdict after 06:17Z, nav overflow guard, /ideas state filter, wait-deploy.py, review-row auto-check. Rungs this chain: 2,2,3,1,1,3,3,3,3,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
