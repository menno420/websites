# websites · status
updated: 2026-07-11T09:50:00Z
phase: CONTINUOUS MODE (manager Q-0265): 09:38Z nudge — slice 21 landed: #114 (time-discipline guard, the designated rung-3 pick): tests/test_time_discipline.py AST-scans the suite and FAILS any call to an age-measuring entry point (fleet.overview/lane_status/freshness/heartbeat_freshness, orders.overview/classify_order) without a frozen now= — the exact 08:45Z time-bomb class; FIRST RUN CAUGHT 17 LATENT SITES across 5 test files, all threaded with frozen NOW constants (behavior-preserving, suite passes unchanged); heartbeat_freshness + orders.overview gained the module-standard injectable now=; meta-test keeps the scanner honest. Sibling this window: #113 (kit v1.10.1). Wake running total: 21 work slices (#64→#114) + 2 rescues.
health: green (main HEAD 02adf7c at write; app suite 179 passed, full three-service suite 237 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #114 — time-discipline guard (backlog → Built). Sibling: #113 kit v1.10.1.
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session (second silent window; 04:03Z stranded heartbeat was rescued as #98). Trigger trig_017H9Qb9oxtLgUy6sw2gnSHg still armed (cron 0 */4 * * *, next ~12:00Z — carried as a watch, not gated on). FOR THE MANAGER: routine-fired sessions remain unreliable landers; the send_later chain is the consistent producer. send_later chain: →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe).
deployed: 02adf7c · verified 2026-07-11T09:47Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); /orders.json live (18 cards, registry source) + board heartbeat chips rendering post-change.
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
notes: backlog: 3 buildable captured (nav manifest; quality.yml every-card gate port — added by sibling #113, real and buildable; route-level clock freeze — this slice's 💡) plus the two manager-side asks. Routed work still beats guard-sized bullets. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107/#109/#111/#114 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort — the defused+guarded time-bomb class is exactly what used to masquerade as cron flakiness). Q-0264 candidates: twenty-six in docs/ideas/backlog.md. Rungs this chain: …,3,5,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
