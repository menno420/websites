# websites · status
updated: 2026-07-11T15:53:00Z
phase: CONTINUOUS MODE (manager Q-0265): 15:44Z nudge — slice 31 landed: #139 (inbox provenance advisory, the last buildable-now bullet — the /orders SURFACE half; the quality.yml gate half stays captured for the kit lane): parse_inbox captures provenance:/from:; provenance_unverified() flags orders naming no session/coordinator identity (cse_/session_/coordinator/manager/URL) — ADVISORY-ONLY muted chip, never red, never affects state, relays stay legal; ORDERS_ORDER pin moved SAME-PR. LIVE-VERIFIED post-deploy: orders 001–009 (pre-convention) flag True; 010 (relay from: line) and 011 (cse_ provenance) verified False — the heuristic follows OBSERVED conventions, not invented rules. BUILDABLE-NOW BACKLOG EMPTY again — remaining items are the rung-5 audit-sweep candidate + manager-side asks. Wake running total: 31 work slices (#64→#139) + 3 rescues.
health: green (main HEAD 8afa7c3 at write; app suite 197 passed, FOUR-service suite 283 expected (281 + 2 — app-only verified this slice); bootstrap check --strict green under kit v1.11.0)
kit: v1.11.0 · check: green · engaged: yes
last-shipped: #139 — inbox provenance advisory (backlog → Built). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (relayed #124) — the ~16:00Z FIRE IS IMMINENT at this write (fire-trace re-check at 15:51Z: none yet); the chain's next nudge (~16:15Z) rituals after the window and rescues any stranded work per doctrine (watch so far: 04:03Z stranded→#98, 08:00Z silent, 12:05Z stranded→#124). Healthcheck cron: 12:17Z slot never delivered; the 18:17Z slot is the schedule-drop decider. send_later chain: →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125 →#127 →#130 →#133 →#135 →#137 →#139.
landing: all-merged — every branch this chain opened is squash-merged; six prune-candidate branches (claude/anthropic-review-site — #132 merged; claude/order008-wake-1205z-heartbeat — relayed #124; gen-1 claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 8afa7c3 · verified 2026-07-11T15:51Z — ALL THREE existing services /version == main HEAD (wait_deploy.py CONVERGED); /orders.json provenance flags live-verified. The review/ service (merged #132) exists on Railway only after the owner creates it (⚑ in docs/owner/OWNER-ACTIONS.md — not blocked on it, no agent Railway mutations per policy).
rung: backlog
tooling: pr-capable
orders: acked=001-011 done=001-011
⚑ needs-owner: THREE asks — canonical list in docs/owner/OWNER-ACTIONS.md (botsite DATABASE_URL; control-plane GITHUB_TOKEN; NEW with #132: create the review/ Railway service — Root Directory = review, no env vars); click-level walkthrough + prune list mirrored in docs/retro/self-review-2026-07-11.md § 2 (ORDER 011).
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
notes: backlog: buildable-now EMPTY (remaining: hand-kept-list audit sweep — rung-5 candidate for an unrouted wake; cross-service clock — dormant) + manager-side asks: (a) latency persistence (one-line convention: done= move appends `pickup: <id> <mins>` to heartbeat notes); (b) provenance-token convention to the KIT LANE (the /orders advisory created cse_/session_/coordinator/manager/URL de facto — the staged-gate half should adopt, not fork, app/orders.py _PROVENANCE_TOKENS); (c) lanes.json; (d) meta.md convention. Standing flags: REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#139 borderline). Q-0264 candidates: thirty-six in docs/ideas/backlog.md. Rungs this chain: …,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
