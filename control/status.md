# websites · status
updated: 2026-07-10T22:29:00Z
phase: CONTINUOUS MODE (manager Q-0265): 22:14Z nudge #2 fired as designed — slice 6 landed: #77 (/orders — every fleet repo's inbox ORDER blocks cross-referenced against its own heartbeat done=/claimed-by lines; the D-0028 parse's natural other half) — LIVE-VERIFIED 22:27Z: control-plane at b30b4f1 == main HEAD, /orders 200, live /orders.json shows the real cross-reference (13 repos · 5 open / 48 done fleet-wide · errored 0 at runtime). The ORDER 009 fleet-info surfacing wave is now FULLY built out: /fleet · /queue · /environments · /projects · /reviews · /orders. Wake running total: 6 work slices (#64, #67, #69, #72, #75, #77). Next builds from the backlog: own-heartbeat parse self-check (small dogfood) or the /fleet manifest-source badge (template tweak).
health: green (main HEAD b30b4f1 at write; suites 180 passed; bootstrap check --strict green under kit v1.7.1; control-plane live-verified at HEAD 22:27:01Z)
kit: v1.7.1 · check: green · engaged: yes
last-shipped: #77 — /orders (D-0032: parse_inbox ORDER blocks × parse_orders heartbeat lines → done/claimed/open/unknown badges, never guessed; claimed matched numerically against the claim id spec — an ISO-timestamp false-positive was caught by test and fixed pre-merge).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; send_later chain live-proven twice (21:40Z → #75, 22:14Z → #77); nudge #3 armed at close. Actions cron healthcheck: run 1 green, next fire ~02:17Z.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69, #71, #72, #73, #75, #76, #77); no LOCAL-ONLY or pushed-unmerged work.
deployed: b30b4f1 · verified 2026-07-10T22:27:01Z — control-plane /version == main HEAD, /orders 200 live with the real fleet cross-reference; earlier this session all three services verified converged (44a9fa6 at 21:4xZ).
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet pages (/fleet /queue /environments /projects /reviews /orders) run live tokenless today on the anonymous 60-req/h ceiling; /orders alone reads ~2 files per repo per cache window, so headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the six fleet pages.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue /environments /reviews /orders all verified 200 with REAL fleet content while the service token is unset.
notes: FOR THE MANAGER (flags stand + one new): (1) REVIEW-QUEUE ROWS OWED — the binding 50-line rule now qualifies websites #67, #72, #75 AND #77 (~250-300 runtime lines each); this lane cannot write fleet-manager — please append rows or grant a path. (2) meta.md deployed:-line convention ask for the forming projects/ registry stands. (3) NEW: /orders live shows superbot-next 3 open + superbot-games 2 open orders fleet-wide — the page is now the one glance for stalled order flow (https://control-plane-production-abb0.up.railway.app/orders). (4) Q-0264 sim-worthy candidates now seven, all in docs/ideas/backlog.md (newest: stalled-claim aging on /orders). Rungs this session: 2,2,3,1,1,3. send_later: nudge #3 armed ~15 min out. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
