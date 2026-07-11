# websites · status
updated: 2026-07-11T01:51:00Z
phase: CONTINUOUS MODE (manager Q-0265): 01:40Z nudge — slice 11 landed: #88 (JSON shape pins for /orders.json /queue.json /projects.json /reviews.json — every machine endpoint now contract-pinned like /fleet.json — PLUS the PR #9 claude/rework-dashboard salvage re-check RETIRED with evidence: no merge base, unique commit a0b459f fully superseded by PR #10, zero forbidden literals in shipped files; the launch-readiness flag is answered — no hardening was lost). Wake running total: 11 work slices (#64, #67, #69, #72, #75, #77, #79, #81, #83, #86, #88). NEXT slice must check: healthcheck cron RUN 2 verdict (~02:17Z — a no-show means the schedule is dead despite dispatch run 1 passing).
health: green (main HEAD b16e23f at write; suites 207 passed; bootstrap check --strict green under kit v1.8.0; control-plane /version == b16e23f == main HEAD verified 01:49:56Z)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #88 — JSON pins ×4 + PR #9 retire-with-evidence (backlog Retired entry carries the diff proof).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~04:00Z. send_later chain: 21:40Z→#75, 22:14Z→#77, 22:45Z→#79, 23:12Z→#81, 23:48Z→#83, 00:14Z→#86, 01:40Z→#88; next nudge armed ~02:20Z (deliberately AFTER the 02:17Z healthcheck cron so run-2's verdict is checkable).
landing: all-merged — every branch this chain opened is squash-merged (#64→#88 series); no LOCAL-ONLY or pushed-unmerged work. The stale claude/rework-dashboard remote branch is confirmed safe to prune (see #88), pending someone with delete rights.
deployed: b16e23f · verified 2026-07-11T01:49:56Z — control-plane /version == main HEAD; all three services last fully verified converged at 0f2cd17 (22:54Z).
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
notes: FOR THE MANAGER: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81/#86 borderline); this lane cannot write fleet-manager. (2) STALE-BRANCH PRUNE: claude/rework-dashboard is verified safe to delete (evidence in #88 / backlog Retired) — one click for anyone with delete rights; also claude/harden-verify + claude/wire-github-token-docs are gen-1 landed-content leftovers worth the same sweep. (3) Per-lane Atom feeds + /queue.json round-trip + all five .json contracts now pinned. (4) Q-0264 candidates now twelve in docs/ideas/backlog.md (newest: /ideas state filter — conveyor health). NEXT picks: healthcheck run-2 verdict (due 02:17Z), open-PR-awareness script, review-row auto-check, wait-deploy.py, ladder-rung telemetry, nav overflow guard. Rungs this chain: 2,2,3,1,1,3,3,3,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
