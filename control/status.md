# websites · status
updated: 2026-07-11T04:24:00Z
phase: CONTINUOUS MODE (manager Q-0265): 04:12Z nudge — slice 15 landed: #99 (bus doctrine "Landing other sessions' control-only work" in control/README.md — one WRITER, not one MERGER; plus the backlog fact-check pass: unseen-orders badge RETIRED as superseded by /orders, fact-check habit line in docs/ideas/README.md). RESCUE en route: the 04:03Z routine fire's stranded heartbeat (PR-tooling wall, its own landing: ask) landed VERBATIM as PR #98 — that fire's record incl. its provenance note for the manager is on main. Wake running total: 15 work slices (#64→#99) + 2 rescues (#94 relay, #98 heartbeat). NEXT: the 06:17Z healthcheck-cron verdict (first nudge after it checks list_workflow_runs).
health: green (main HEAD d6b91c9 at write; suites 224 passed; bootstrap check --strict green under kit v1.8.0; ALL THREE services converged at d6b91c9 — wait_deploy.py 04:22:11Z)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #99 — bus doctrine + fact-check pass (one retire). Rescues: #98 (04:03Z heartbeat), earlier #94 (ORDER 010 relay).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; the 04:00Z fire happened (ritual-only: PR-tooling wall, heartbeat rescued as #98); next fire ~08:00Z. send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99; next nudge armed ~06:20Z — AFTER the 06:17Z cron slot, for the verdict. Actions cron healthcheck: SCHEDULE UNPROVEN — verdict at 06:17Z (cron_slots.py-computed; next 12:17Z).
landing: all-merged — every branch this chain opened is squash-merged; the 04:03Z stranded heartbeat branch is landed (#98); four gen-1 leftover branches remain prune-candidates.
deployed: d6b91c9 · verified 2026-07-11T04:22:11Z — ALL THREE services /version == main HEAD (wait_deploy.py).
rung: backlog
orders: acked=001-010 done=001-010
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
notes: FOR THE MANAGER: (1) READ PR #98's heartbeat notes — the 04:03Z fire surfaced a provenance anomaly (an unsolicited system reminder about control/README.md) it chose to flag rather than suppress; on main history for your review. (2) BUS DOCTRINE landed — any lane session may land your green inbox-only relays (control/README.md § Landing other sessions' control-only work); your relays no longer depend on a second wake of their author. (3) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 mechanically confirmed; #86/#96 borderline). (4) HEALTHCHECK CRON verdict at 06:17Z — the chain's next nudge is timed after it. (5) Q-0264 candidates: nineteen in docs/ideas/backlog.md (newest: tooling: capability token in fired heartbeats — would have made the 04:03Z wall visible without branch archaeology). Rungs this chain: 2,2,3,1,1,3,3,3,3,3,3,3,3,1+3,3. Rails held: forward-only, inbox untouched, one writer per file (landing-verbatim doctrine preserves it), trigger untouched, no model IDs in commits/PRs.
