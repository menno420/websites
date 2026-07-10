# websites · status
updated: 2026-07-10T21:07:00Z
phase: CONTINUOUS MODE (manager Q-0265): 20:00Z wake, three slices landed — #64 (card template, NEXT item 3), #67 (heartbeat enrichment, NEXT item 4), #69 (scheduled healthcheck workflow, backlog promotion; first run VERIFIED — workflow_dispatch run 29123498090 concluded SUCCESS 21:04:01Z, next cron fire ~02:17Z). NOW CLAIMING ORDER 009 (landed mid-slice-3 via inbox PR #70): increment (1) /projects registry page is slice 4, this session.
health: green (main HEAD fc8354e at write; suites 157 passed; bootstrap check --strict green; healthcheck workflow run 1 success on main)
kit: v1.7.0 · check: green · engaged: yes
last-shipped: #69 — scheduled healthcheck workflow (D-0029: 6-hourly cron + dispatch, read-only, non-required; three live services + manifest live-parse; first run green). Earlier this wake: #64, #65, #67, #68.
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; 16:00Z + 20:00Z fires both produced landed work. The repo now ALSO has its own Actions cron (healthcheck, 17 */6 * * *) — two independent clocks.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69); no LOCAL-ONLY or pushed-unmerged work.
deployed: 0322682 · verified 2026-07-10T20:51:58Z — all three services' /version == then-main HEAD (healthcheck.py 6/6 PASS + manifest 13 lanes); #69's merge (fc8354e) is workflow-only, deploy convergence expected but not yet re-verified.
orders: acked=001,002,003,004,005,006,007,008,009 done=001,002,003,004,005,006,007,008 claimed-by: 009 websites-continuous-wake 2026-07-10T21:07Z
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
  WHY-IT-MATTERS: justified by rate headroom + resilience, not access — fleet-manager is anonymously readable today, so /queue + /environments run live tokenless; the token lifts the anonymous 60-req/h ceiling, lights the admin-scope board cells + /owner re-run CI, and keeps the pages alive if that visibility ever changes.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /owner re-run CI; 5000 req/h headroom for /fleet + /activity + /queue + /environments + /projects.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue + /environments verified 200 with REAL fleet-manager content while the service token is unset.
notes: ORDER 009 claim rationale: this session IS the active wake ("ship increment (1) on your next wake" — continuous mode makes this the wake); bus re-read at HEAD fc8354e before claiming, no sibling claim visible. Rungs so far: slices 1-2 rung 2 (NEXT list, now exhausted), slice 3 rung 3 (backlog), slice 4 rung 1 (ORDER 009). Ideas captured this wake (Q-0264 sim-worthy candidates): open-PR awareness at wake; own-heartbeat parse self-check; healthcheck-failure auto-files a GitHub issue (alert routing to agent-visible surfaces, not just the owner's inbox). Rails held: forward-only, inbox untouched, one writer per file, trigger untouched.
