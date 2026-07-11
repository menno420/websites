# websites · status
updated: 2026-07-11T09:12:00Z
phase: CONTINUOUS MODE (manager Q-0265): 08:57Z nudge — slice 20 landed: #111 (rung 5 HONEST upkeep with the backlog dry): (a) docs/current-state.md truth sweep — four stale claims corrected (kit said v1.6.0/is v1.10.0; "PAT is set" vs live token-UNSET finding; PR #36 manifest entry marked superseded by the gen_roster.py registry; 17-slice gap closed with one consolidated chain entry; Next steps re-pointed at backlog/inbox); (b) LIVE CATCH: a time-bomb test defused — test_overview_sorts_stranded… began failing at 08:45Z on an untouched tree (fixture updated: stamps crossed FLEET_STALE_HOURS against real now inside fleet.overview()); overview() gains the module-standard injectable now=, test pins frozen NOW; audited all other fixed-stamp tests: no other bombs. Wake running total: 20 work slices (#64→#111) + 2 rescues.
health: green (main HEAD 13554fc at write; full three-service suite 235 passed DETERMINISTICALLY — was 1 failed pre-defuse; bootstrap check --strict green under kit v1.10.0)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #111 — current-state truth sweep + fleet sort-test time-bomb defuse.
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session (second silent window; 04:03Z stranded heartbeat was rescued as #98). Trigger trig_017H9Qb9oxtLgUy6sw2gnSHg still armed (cron 0 */4 * * *, next ~12:00Z). FOR THE MANAGER: routine-fired sessions remain unreliable landers; the send_later chain is the consistent producer. NOTE: the defused time-bomb is exactly the failure class that detonates inside unattended fired sessions — it would have shown as a mystery-red quality run on any PR after 08:45Z. send_later chain: →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe).
deployed: 13554fc · verified 2026-07-11T09:10Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); /fleet.json live: 18 lanes, lane_source=registry.
rung: upkeep
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
notes: backlog: refilled to 2 buildable captured (was dry at #110; slice enders added two small guards — nav manifest; test time-discipline guard) plus the two manager-side asks. Still FOR THE MANAGER: routed work beats guard-sized bullets — this lane can absorb a real order. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107/#109/#111 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort). Q-0264 candidates: twenty-five in docs/ideas/backlog.md. Rungs this chain: …,3,3,5. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
