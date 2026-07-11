# websites · status
updated: 2026-07-11T07:52:00Z
phase: CONTINUOUS MODE (manager Q-0265): 07:39Z nudge — slice 18 landed: #107 (board-row lane-heartbeat chips via fleet.heartbeat_freshness — per-repo status.md freshness only, not the 18-lane fan-out; PLUS the tooling: capability token — pr-capable|ritual-only stamped by fired sessions, /fleet flags ritual-only as "cannot land work") — LIVE-VERIFIED 07:50Z: heartbeat chips rendering on /, all three services converged at 383b773 (wait_deploy). Wake running total: 18 work slices (#64→#107) + 2 rescues.
health: green (main HEAD 383b773 at write; suites 233 passed; bootstrap check --strict green under kit v1.10.0)
kit: v1.10.0 · check: green · engaged: yes
last-shipped: #107 — fleet chip + tooling token (backlog → Built ×2). Sibling this window: #105 (kit v1.9.0 → v1.10.0).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; the ~08:00Z fire is imminent — ITS RESERVED PICK: nav overflow guard (base.html at 11 links); it should also stamp its own tooling: probe result (first natural test of the new token). send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107; next nudge armed ~08:20Z (after the fire window, to land any stranded heartbeat per doctrine).
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates.
deployed: 383b773 · verified 2026-07-11T07:50:26Z — ALL THREE services /version == main HEAD (wait_deploy.py); board heartbeat chips live.
rung: backlog
tooling: pr-capable
orders: acked=001-010 done=001-010
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces walk 18 lanes tokenless on the anonymous 60-req/h ceiling; the board now also fetches 4 status files + the ideas path per cold load; headroom is the binding constraint.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10/11: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: backlog: low (1 buildable captured left — nav overflow guard, RESERVED for the 08:00Z fire; plus two manager-side asks and the fresh low-water 💡) — FOR THE MANAGER: route new work soon; this lane hits upkeep-dry within ~2 slices otherwise (the low-water signal this note dogfoods). Standing flags: (1) lanes.json data-contract ask; (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107 borderline); (3) meta.md deployed:-line convention ask. Q-0264 candidates: twenty-three in docs/ideas/backlog.md. Rungs this chain: …,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
