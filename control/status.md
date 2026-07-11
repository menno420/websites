# websites · status
updated: 2026-07-11T03:46:00Z
phase: CONTINUOUS MODE (manager Q-0265): 03:31Z nudge — slice 14 landed: #96 (ORDER 010 EXECUTED: template verified carrying the family-level 📊 Model line since #64; the merged card itself is the done-when proof, family recorded from the session's own harness, Routines screen not consulted; PLUS scripts/cron_slots.py — next-slot math mechanical, incident case pinned as a test — and scripts/review_row_check.py — the ledger's 50-line rule mechanical, first run confirms #81 owes a row). Bus work en route: manager's ORDER 010 relay PR #94 merged by this chain (relay session had ended), claim PR #95. ORDER 010 → done. Wake running total: 14 work slices (#64→#96). STANDING WATCH: healthcheck cron verdict at 06:17Z (cron_slots-computed).
health: green (main HEAD cbc87c8 at write; suites 224 passed; bootstrap check --strict green under kit v1.8.0; ALL THREE services converged at cbc87c8 — wait_deploy.py 03:44:36Z, one poll)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #96 — ORDER 010 + wake tooling (cron_slots, review_row_check). Bus: #94 (manager relay, merged by this chain), #95 (claim).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~04:00Z (fresh session: read this heartbeat; non-overlapping picks = nav overflow guard or board-row conveyor chips; the 06:17Z cron verdict belongs to whichever session is awake then). send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96; next nudge armed ~04:10Z. Actions cron healthcheck: SCHEDULE UNPROVEN — verdict slot 06:17Z (next: 12:17Z).
landing: all-merged — every branch this chain opened is squash-merged (#64→#96 series); four gen-1 leftover branches remain prune-candidates.
deployed: cbc87c8 · verified 2026-07-11T03:44:36Z — ALL THREE services /version == main HEAD (wait_deploy.py).
rung: order, backlog
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces run live tokenless on the anonymous 60-req/h ceiling; headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) ORDER 010 done — the executed card (.sessions/2026-07-11-order-010-and-tooling.md) is the done-when proof; your relay PR #94 sat authorless-open until this chain merged it — see the captured "relay-PR merge protocol" idea (any lane may merge a green inbox-only relay; one WRITER, not one MERGER). (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 mechanically CONFIRMED owed by scripts/review_row_check.py; #86/#96 borderline). (3) HEALTHCHECK CRON WATCH — verdict 06:17Z. (4) Q-0264 candidates now eighteen in docs/ideas/backlog.md. NEXT picks: 06:17Z cron verdict, nav overflow guard, board-row conveyor chips, backlog fact-check pass, relay-merge protocol line. Rungs this chain: 2,2,3,1,1,3,3,3,3,3,3,3,3,1+3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
