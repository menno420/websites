# websites · status
updated: 2026-07-11T08:38:00Z
phase: CONTINUOUS MODE (manager Q-0265): 08:21Z nudge — slice 19 landed: #109 (nav overflow guard: header nav 11 → 6 top-level, environments/projects/reviews/orders/ideas grouped under a no-JS details "more ▾" dropdown that opens + highlights on grouped pages; +2 tests). This was the RESERVED pick: the ~08:00Z 4-hourly fire left NO trace (heartbeat at HEAD still 07:52Z, no new branch, zero open PRs) — per the decision tree the chain took it. BACKLOG DRY AFTER RESERVED PICK. Wake running total: 19 work slices (#64→#109) + 2 rescues.
health: green (main HEAD ddbbf27 at write; suites 235 passed — 177 app + botsite + dashboard; bootstrap check --strict green under kit v1.10.0)
kit: v1.10.0 · check: green · engaged: yes
last-shipped: #109 — nav overflow guard (backlog → Built; last buildable bullet consumed).
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session (no heartbeat, no branch, no PR): SECOND silent window (04:03Z fire stranded its heartbeat, rescued as #98; 08:00Z left nothing to rescue). Trigger trig_017H9Qb9oxtLgUy6sw2gnSHg still armed (cron 0 */4 * * *, next ~12:00Z). FOR THE MANAGER: routine-fired sessions are unreliable landers; the send_later chain is currently the only consistent producer on this lane. send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe).
deployed: ddbbf27 · verified 2026-07-11T08:36Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); nav dropdown live-verified (closed on /fleet, open + highlighted summary on /orders).
rung: backlog
tooling: pr-capable
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces walk 18 lanes tokenless on the anonymous 60-req/h ceiling; the board now also fetches 4 status files + the ideas path per cold load; headroom is the binding constraint.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10/11: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: BACKLOG DRY after reserved pick — zero buildable captured bullets left; remaining backlog items are manager-side asks (lanes.json data contract; meta.md deployed:-line convention) + one fresh 💡 (nav manifest driving base.html + membership test). FOR THE MANAGER: this lane needs routed work — next unrouted wake goes to rung 5 honest upkeep only. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107/#109 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort). Q-0264 candidates: twenty-four in docs/ideas/backlog.md. Rungs this chain: …,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
