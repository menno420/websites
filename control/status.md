# websites · status
updated: 2026-07-11T13:29:00Z
phase: CONTINUOUS MODE (manager Q-0265): 13:19Z nudge — slice 27 landed: #130 (route-level clock freeze, the designated pick — the #114 time guard's remaining blind half): app/clock.py is the app's SINGLE wall-clock read (NOW_OVERRIDE, None in prod — zero production change); all age-measuring fallbacks in fleet (4 sites), orders (3) and activity's feed timestamp route through clock.now(); tests/test_clock_freeze.py (+4) pins the override, renders a WHOLE /fleet.json request at a frozen instant (fixture lane exactly 1.0h old, deterministically, in any decade), freezes /orders.json, and adds a source guard: app/*.py may not call datetime.now()/utcnow() outside clock.py (a new module cannot silently reopen the blind spot). JSON contracts untouched. Sibling this window: #129 (kit v1.11.0, third wave today, absorbed cleanly). Wake running total: 27 work slices (#64→#130) + 3 rescues.
health: green (main HEAD 77b5a34 at write; app suite 191 passed, full three-service suite 249 passed; bootstrap check --strict green under kit v1.11.0)
kit: v1.11.0 · check: green · engaged: yes
last-shipped: #130 — route-level clock freeze (backlog → Built). Sibling: #129 kit v1.11.0. SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (relayed #124; next ~16:00Z — the ~16:0xZ nudge rituals right after it). Healthcheck cron: the 12:17Z slot STILL UNDELIVERED at 13:28Z (~71 min; the 06:17Z slot took ~2h, so within observed variance — watching, never gating; if the slot is still absent at the ~16:00Z wake, note it as the longest observed gap). send_later chain: →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125 →#127 →#130.
landing: all-merged — every branch this chain opened is squash-merged; five prune-candidate branches (claude/order008-wake-1205z-heartbeat — relayed via #124, safe; plus gen-1 claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 77b5a34 · verified 2026-07-11T13:27Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); /fleet.json live post-rewire (18 lanes, registry source).
rung: backlog
tooling: pr-capable
orders: acked=001-011 done=001-011
⚑ needs-owner: two asks — canonical list in docs/owner/OWNER-ACTIONS.md; click-level walkthrough + prune list mirrored in docs/retro/self-review-2026-07-11.md § 2 (ORDER 011).
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
notes: backlog: 4 buildable captured (order-ack latency line; nav-scan glob; inbox relay-order provenance advisory; cross-service clock pattern — dormant by design until botsite/dashboard grow age-measuring code, premise-checked: zero datetime.now in either today) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#130 borderline); (2) lanes.json ask; (3) meta.md convention ask. Q-0264 candidates: thirty-two in docs/ideas/backlog.md. Rungs this chain: …,rescue+3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
