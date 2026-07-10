# websites · status
updated: 2026-07-10T22:56:00Z
phase: CONTINUOUS MODE (manager Q-0265): 22:45Z nudge #3 fired as designed — slice 7 landed: #79 (own-heartbeat parse self-check: tests/test_own_heartbeat.py runs THIS file through the /fleet parsers every suite run — required fields parse, orders machine-readable, enriched lines classify, nothing leaks into blockers; plus backlog hygiene: the /fleet manifest-badge bullet RETIRED as already-shipped since PR #36 — fact-check beat rebuild). Wake running total: 7 work slices (#64, #67, #69, #72, #75, #77, #79). Next builds from the backlog: stalled-claim aging on /orders (extend parse_orders with the claim timestamp), /queue.json round-trip, kit-version rollup on /fleet.
health: green (main HEAD 0f2cd17 at write; suites 185 passed; bootstrap check --strict green under kit v1.7.1; ALL THREE services /version == 0f2cd17 == main HEAD verified 22:54:11Z)
kit: v1.7.1 · check: green · engaged: yes
last-shipped: #79 — own-heartbeat parse self-check (+5 tests, 185 total; honest scope: control-only PRs skip pytest, so a malformed heartbeat reds the NEXT non-control PR — standing floor) + manifest-badge bullet retired-with-why.
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; send_later chain live-proven three times (21:40Z → #75, 22:14Z → #77, 22:45Z → #79); nudge #4 armed at close. Actions cron healthcheck: run 1 green, next fire ~02:17Z. NOTE: the 4-hourly trigger's next fire ~00:00Z will overlap the send_later chain — the fresh session should read this heartbeat first and continue the backlog, not redo the ladder from scratch.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69, #71, #72, #73, #75, #76, #77, #78, #79); no LOCAL-ONLY or pushed-unmerged work.
deployed: 0f2cd17 · verified 2026-07-10T22:54:11Z — ALL THREE services /version == main HEAD (control-plane, botsite, dashboard).
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
  WHY-IT-MATTERS: rate headroom + resilience — the six fleet pages (/fleet /queue /environments /projects /reviews /orders) run live tokenless on the anonymous 60-req/h ceiling; /orders alone reads ~2 files per repo per cache window, so headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the six fleet pages.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue /environments /reviews /orders all verified 200 with REAL fleet content while the service token is unset.
notes: FOR THE MANAGER (standing flags): (1) REVIEW-QUEUE ROWS OWED for websites #67, #72, #75, #77 (>50 runtime lines each; this lane cannot write fleet-manager). (2) meta.md deployed:-line convention ask for the forming projects/ registry. (3) /orders live = the stalled-order glance (5 open fleet-wide at 22:27Z: superbot-next 3, superbot-games 2). (4) Q-0264 sim-worthy candidates now eight in docs/ideas/backlog.md (newest: backlog fact-check pass before promoting a bullet — pick (b) this slice was already shipped and nearly got rebuilt). Rungs this session: 2,2,3,1,1,3,3. send_later: nudge #4 armed ~15 min out. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
