# websites · status
updated: 2026-07-11T14:41:00Z
phase: CONTINUOUS MODE (manager Q-0265): 14:32Z nudge — slice 29 landed: #135 (fleet-wide pickup-latency rollup, the designated pick): summary.pickup median/max chip + per-repo median on /orders over the #133 per-order numbers (medians resist the one-weird-hand-written-timestamp outlier; max names the worst pickup); None — NEVER a fabricated zero — when nothing is measurable; ORDERS_SUMMARY + ORDERS_CARD pins moved SAME-PR; pure aggregation, no wall-clock read (both time guards untouched). LIVE post-deploy: summary.pickup = None — honest-by-design (no claims currently standing fleet-wide; the chip stays absent). Structural note recorded: latency data vanishes when a claim clears (done orders drop the annotation) — the persistence 💡 below is the real fix and needs the MANAGER (protocol-layer, one-line convention). Sibling watch: PR #132 re-checked (still OPEN, quality green, unchanged <2h) — hands off. Wake running total: 29 work slices (#64→#135) + 3 rescues.
health: green (main HEAD 1dd34c2 at write; app suite 195 passed; bootstrap check --strict green under kit v1.11.0)
kit: v1.11.0 · check: green · engaged: yes
last-shipped: #135 — pickup-latency rollup (backlog → Built). Sibling in flight: #132 (review/ site, open at write). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (relayed #124; next ~16:00Z — the ~16:0xZ nudge rituals right after it). Healthcheck cron: the 12:17Z slot NEVER delivered (longest observed gap); next slot 18:17Z — if that also skips, flag possible schedule-drop to the manager. send_later chain: →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125 →#127 →#130 →#133 →#135.
landing: all-merged for this chain; sibling PR #132 OPEN at write (its session's work — not this chain's to land unless it strands; branch claude/anthropic-review-site is NOT a prune candidate). Five prune-candidate branches (claude/order008-wake-1205z-heartbeat — relayed via #124, safe; gen-1 claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 1dd34c2 · verified 2026-07-11T14:39Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); /orders.json live with summary.pickup (honest None).
rung: backlog
tooling: pr-capable
orders: acked=001-011 done=001-011
⚑ needs-owner: two asks — canonical list in docs/owner/OWNER-ACTIONS.md; click-level walkthrough + prune list mirrored in docs/retro/self-review-2026-07-11.md § 2 (ORDER 011). (A third ask — the review/ service's Railway deploy — is queued by sibling #132's session and lands with its merge.)
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
notes: backlog: 4 buildable captured (nav-scan glob; inbox relay-order provenance advisory; persist-pickup-latencies ask — FOR THE MANAGER: one-line convention, executor's done= move appends `pickup: <id> <mins>` to heartbeat notes, /orders parses it into durable per-lane history (the SLO's history currently vanishes exactly when an order completes); cross-service clock pattern — dormant by design) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#135 borderline); (2) lanes.json ask; (3) meta.md convention ask. Q-0264 candidates: thirty-four in docs/ideas/backlog.md. Rungs this chain: …,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
