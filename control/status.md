# websites · status
updated: 2026-07-11T12:54:00Z
phase: CONTINUOUS MODE (manager Q-0265): 12:45Z nudge — slice 26 landed: #127 (control-gate suite tests, the designated pick): tests/test_control_gates.py drives the REAL check --strict --status-only [--inbox-base] CLI via subprocess against a synthetic fixture install (the born-red-gate test pattern), pinning FIVE lanes — clean heartbeat 0; broken heartbeat 1 [status-no-heartbeat]; inbox rewrite vs base 1 [inbox-not-append]; pure ORDER append 0; malformed append 1 [inbox-order-grammar] (the FIFTH lane was found while prototyping in the scratchpad — the hand-validation at port time had missed it; pin what the CLI actually does, not what the port PR said). Gate-behavior changes now require changing these tests in the same PR (the JSON-contract-pin protocol). Wake running total: 26 work slices (#64→#127) + 3 rescues.
health: green (main HEAD 85c3be6 at write; app suite 187 passed, full three-service suite 245 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #127 — control-gate suite tests (backlog → Built). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (heartbeat relayed as #124; next ~16:00Z — the ~16:05Z nudge rituals right after it per doctrine). Healthcheck cron: the 12:17Z slot still UNDELIVERED at 12:54Z (~37 min late so far; the 06:17Z slot delivered ~2h late, so within observed variance — best-effort confirmed, keep watching, never gate). send_later chain: →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125 →#127.
landing: all-merged — every branch this chain opened is squash-merged; five prune-candidate branches (claude/order008-wake-1205z-heartbeat — relayed via #124, safe; plus gen-1 claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 85c3be6 · verified 2026-07-11T12:53Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED).
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
notes: backlog: 4 buildable captured (route-level clock freeze; order-ack latency line; nav-scan glob; inbox relay-order provenance advisory — this slice's 💡: the gates just made the inbox TRUSTED input, and trusted input attracts spoofing) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#127 borderline); (2) lanes.json ask; (3) meta.md convention ask. Q-0264 candidates: thirty-one in docs/ideas/backlog.md. Rungs this chain: …,3,rescue+3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
