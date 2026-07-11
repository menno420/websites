# websites · status
updated: 2026-07-11T04:15:00Z
phase: ORDER 008 routine wake (trigger trig_017H9Qb9oxtLgUy6sw2gnSHg, ~04:00Z fire): synced to origin/main HEAD b3fecfe; re-read control/inbox.md — no order past 010, all already in done=. No claim taken (rung 1 empty). Did NOT proceed to rung 2/3 backlog work this wake: this session's toolset has no GitHub PR-creation tool (ToolSearch confirmed empty — matches the documented 2026-07-10 routine-fired-session wall) and this repo forbids direct push to main, so any build work this session opened could only land as pushed-unmerged with no path to merge it; kept this wake to the mandatory ritual (sync, inbox check, heartbeat) rather than stack more stranded branches. This heartbeat itself is pushed on a branch for the same reason — see landing:.
health: green (live-verified only, no local test run this wake — deps not installed in this session's clone): all three /version endpoints == main HEAD b3fecfe004ca29d2ac3ed66ce79b733c7688f3a3 at 2026-07-11T04:03Z curl.
kit: v1.8.0 · check: not run this wake (no local env; last known green per prior heartbeat) · engaged: yes
last-shipped: #96 — ORDER 010 + wake tooling (cron_slots, review_row_check). No new PR this wake.
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; this wake IS the ~04:00Z fire. Actions cron healthcheck: verdict still pending — first eligible slot after this wake is 06:17Z, not yet reached.
landing: pushed-unmerged claude/status-heartbeat-2026-07-11-0403z — this wake's own heartbeat commit; no PR-creation tool available to this session (verified via ToolSearch, empty result) to open it, per the ROUTINE-FIRED SESSION protocol (docs/project/project-instructions.md): push proven (verify via git ls-remote before trusting this line), left for the next PR-tooled session to open+merge.
deployed: b3fecfe0 · verified 2026-07-11T04:03Z — ALL THREE services /version == main HEAD (curl, not wait_deploy.py — no local deps this wake).
rung: order (checked, empty)
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
notes: FOR THE MANAGER: (1) ORDER 010 done — unchanged from prior heartbeat. (2) REVIEW-QUEUE ROWS OWED — unchanged: websites #67, #72, #75, #77 (+#81 mechanically CONFIRMED owed by scripts/review_row_check.py; #86/#96 borderline) — this wake made no code changes so nothing new is owed. (3) HEALTHCHECK CRON WATCH — verdict still due 06:17Z, not this wake. (4) THIS WAKE (04:03Z fire) attempted no backlog build: no PR-creation tool in this session's toolset (probed via ToolSearch, empty) blocks landing anything beyond a stranded branch, so it stuck to the mandatory sync+inbox+heartbeat ritual — the next PR-tooled wake should open+merge this heartbeat branch (claude/status-heartbeat-2026-07-11-0403z) first, then resume the backlog (nav overflow guard / board-row conveyor chips / backlog fact-check pass / relay-merge protocol doc line all still open, unbuilt) and the 06:17Z cron verdict. NOTE FOR THE MANAGER RE: PROVENANCE — this session was also shown an unsolicited system-reminder mid-wake claiming control/README.md had been "modified... by the user or a linter," instructing it not to revert and not to mention it to the user; the session had in fact just self-reverted an out-of-scope self-authored policy edit there via `git checkout --`, confirmed the file clean against origin/main, and is surfacing (not suppressing) the anomalous reminder per its standing instructions to flag suspected prompt injection — worth a look if this recurs. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs, no new policy authored into control/README.md.
