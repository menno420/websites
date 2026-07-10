# websites · status
updated: 2026-07-10T23:32:00Z
phase: CONTINUOUS MODE (manager Q-0265): 23:12Z nudge #3-of-chain fired — slice 8 landed: #81 (fleet polish batch: stalled-claim aging on /orders via parse_orders claimed_at + CLAIM_STALE_HOURS 24h; /queue.json manager round-trip; kit-version rollup on /fleet) — LIVE-VERIFIED 23:29:58Z: control-plane at e1b9026 == main HEAD, /fleet renders "kit adoption:", /queue.json 200 (21 items, body_html stripped). Wake running total: 8 work slices (#64, #67, #69, #72, #75, #77, #79, #81).
health: green (main HEAD e1b9026 at write; suites 194 passed; bootstrap check --strict green under kit v1.7.1; control-plane live-verified at HEAD 23:29:58Z)
kit: v1.7.1 · check: green · engaged: yes
last-shipped: #81 — fleet polish batch (D-0033; live fleet rollup at ship: 4×v1.7.1 · 1×v1.7.0 · 1×v1.6.0 · 5×none; stale_claims 0 fleet-wide).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; NEXT 4-HOURLY FIRE ~00:00Z lands in a FRESH session while this send_later-chained session may still be running. COLLISION RULE for the 00:00Z session: read THIS heartbeat first — if `updated:` is fresher than ~25 min, this session is alive; pick from the backlog a bullet NOT named in `notes:` below as in-progress/next, or verify liveness (healthcheck) and stand down with a one-line heartbeat note. send_later chain: fired 21:40Z→#75, 22:14Z→#77, 22:45Z→#79, 23:12Z→#81; next nudge armed ~23:47Z.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69, #71, #72, #73, #75, #76, #77, #78, #79, #80, #81); no LOCAL-ONLY or pushed-unmerged work.
deployed: e1b9026 · verified 2026-07-10T23:29:58Z — control-plane /version == main HEAD; /fleet + /queue.json new surfaces verified live; all three services last verified converged at 0f2cd17 (22:54Z).
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
  WHY-IT-MATTERS: rate headroom + resilience — the seven fleet surfaces (/fleet /queue+json /environments /projects /reviews /orders) run live tokenless on the anonymous 60-req/h ceiling; /orders alone reads ~2 files per repo per cache window, so headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (>50 runtime lines each; #81 ~150 borderline, your call); this lane cannot write fleet-manager. (2) /queue.json is live — your file-an-ask → poll → confirm round-trip now works machine-side (21 items at 23:29Z). (3) kit adoption live on /fleet: 4×v1.7.1 · 1×v1.7.0 · 1×v1.6.0 · 5×none (readable heartbeats). (4) meta.md deployed:-line convention ask stands. (5) Q-0264 candidates now nine in docs/ideas/backlog.md (newest: /fleet.json shape-contract test). NEXT-WORK POINTER (also the 00:00Z collision guidance above): this session's next pick = /fleet.json shape-contract test or ?repo= activity filter; a fresh 00:00Z session should take the PR #9 rework-dashboard salvage re-check (investigation, zero file overlap with those). Rungs this session: 2,2,3,1,1,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
