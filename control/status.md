# websites · status
updated: 2026-07-11T14:05:00Z
phase: CONTINUOUS MODE (manager Q-0265): 13:56Z nudge — slice 28 landed: #133 (order pickup latency, the designated pick): orders.pickup_latency subtracts the two stamps /orders already parsed (ORDER header filed ts; lane claim ISO) — claimed orders render a "picked up in X" chip, /orders.json carries pickup_latency_mins/_human (ORDERS_ORDER contract pins moved SAME-PR), honest None on unparseable/absent/negative stamps (both are hand-written). Frozen-clock discipline held (pure timestamp subtraction; tests under now=NOW; both #114/#130 guards untouched). Rider: HANDOFF.md gitignored (kit v1.11.0 regenerates it untracked by design; check-ignore exited 1 before). LIVE FINDING post-deploy: ORDER 011 shows latency None — CORRECT: done orders drop their claimed-by annotation per doctrine, so latency is only visible while a claim stands (strengthens the rollup idea: capture the number before the claim clears). Ritual note: NEW sibling branch claude/anthropic-review-site checked FIRST — its PR #132 is OPEN and active (owner-directed review/ fourth service, opened 13:37Z), NOT stranded, hands off. Wake running total: 28 work slices (#64→#133) + 3 rescues.
health: green (main HEAD f648452 at write; app suite 193 passed; bootstrap check --strict green under kit v1.11.0)
kit: v1.11.0 · check: green · engaged: yes
last-shipped: #133 — order pickup latency (backlog → Built). Sibling in flight: #132 (review/ site, open at write). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (relayed #124; next ~16:00Z — the ~16:0xZ nudge rituals right after it). Healthcheck cron: the 12:17Z slot NEVER DELIVERED (absent at 14:03Z, ~106 min past — the longest observed gap; the 18:17Z slot is next; still best-effort-consistent per CAPABILITIES, never gated on — but if 18:17Z also skips, flag a possible schedule-drop to the manager). send_later chain: →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125 →#127 →#130 →#133.
landing: all-merged for this chain; sibling PR #132 OPEN at write (its session's own work — not this chain's to land unless it strands). Five prune-candidate branches (claude/order008-wake-1205z-heartbeat — relayed via #124, safe; gen-1 claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion). claude/anthropic-review-site belongs to open PR #132 — NOT a prune candidate.
deployed: f648452 · verified 2026-07-11T14:03Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); /orders.json live with the latency keys.
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
notes: backlog: 4 buildable captured (fleet-wide pickup-latency rollup — this slice's 💡; nav-scan glob; inbox relay-order provenance advisory; cross-service clock pattern — dormant by design) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#133 borderline); (2) lanes.json ask; (3) meta.md convention ask. Q-0264 candidates: thirty-three in docs/ideas/backlog.md. Rungs this chain: …,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
