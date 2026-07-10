# websites · status
updated: 2026-07-10T23:57:00Z
phase: CONTINUOUS MODE (manager Q-0265): 23:48Z nudge fired — slice 9 landed: #83 (/fleet.json shape-contract test: pinned key sets for every machine consumer, degraded-lane same-shape guarantee; a key rename now reds BY NAME). Wake running total: 9 work slices (#64, #67, #69, #72, #75, #77, #79, #81, #83). ⚠ 00:00Z 4-HOURLY FIRE IS IMMINENT — collision rule for that fresh session: this chain is ALIVE (this stamp proves it); take the RESERVED non-overlapping pick = PR #9 claude/rework-dashboard salvage re-check (investigation; diff the live remote branch against main, salvage or retire explicitly — backlog bullet has the sources). This chain's next pick: ?repo= filter on the activity views.
health: green (main HEAD a201b46 at write; suites 197 passed; bootstrap check --strict green under kit v1.7.1; control-plane /version == a201b46 == main HEAD verified 23:56:18Z)
kit: v1.7.1 · check: green · engaged: yes
last-shipped: #83 — /fleet.json shape-contract pin (+3 tests, 197; contract-change protocol: update the pinned sets in the same PR that changes the payload).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~00:00Z (see collision rule in phase). send_later chain: 21:40Z→#75, 22:14Z→#77, 22:45Z→#79, 23:12Z→#81, 23:48Z→#83; next nudge armed ~00:12Z. Actions cron healthcheck: next fire ~02:17Z.
landing: all-merged — every branch this session opened is squash-merged (#64→#83 series); no LOCAL-ONLY or pushed-unmerged work.
deployed: a201b46 · verified 2026-07-10T23:56:18Z — control-plane /version == main HEAD; all three services last fully verified converged at 0f2cd17 (22:54Z), botsite+dashboard re-converge on their next deploys.
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces (/fleet /queue+json /environments /projects /reviews /orders) run live tokenless on the anonymous 60-req/h ceiling; /orders alone reads ~2 files per repo per cache window, so headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 borderline); this lane cannot write fleet-manager. (2) /queue.json live (your round-trip works); kit adoption live on /fleet (4×v1.7.1 · 1×v1.7.0 · 1×v1.6.0 · 5×none at 23:29Z). (3) meta.md deployed:-line convention ask stands. (4) Q-0264 candidates now ten in docs/ideas/backlog.md (newest: same-shape contract tests for the other four machine endpoints). Rungs this session: 2,2,3,1,1,3,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
