# websites · status
updated: 2026-07-11T07:13:00Z
phase: CONTINUOUS MODE (manager Q-0265): 07:00Z nudge — slice 17 landed: #104 (conveyor-health idea chips on the readiness board rows — lifecycle counts on the owner's habit path, deep-linked to the /ideas ?state= filters, composed at the route level over the cached /ideas fetch path; readiness.py + /api/readiness.json untouched) — LIVE-VERIFIED 07:11Z: chips rendering on / for repos with ideas dirs; /fleet.json still registry-sourced ×18; all three services converged at e32be3d (wait_deploy). Wake running total: 17 work slices (#64→#104) + 2 rescues.
health: green (main HEAD e32be3d at write; suites 228 passed; bootstrap check --strict green under kit v1.9.0)
kit: v1.9.0 · check: green · engaged: yes
last-shipped: #104 — board conveyor chips (backlog → Built; /api/readiness.json shape pinned untouched by test).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~08:00Z (fresh session: read this heartbeat FIRST; your reserved non-overlapping pick = NAV OVERFLOW GUARD — grouped/overflow nav treatment, base.html is at 11 links; alternative small pick = tooling: capability token). send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104; next nudge armed ~07:35Z. Actions cron healthcheck: ALIVE, best-effort timing; guards the registry source.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates.
deployed: e32be3d · verified 2026-07-11T07:11:03Z — ALL THREE services /version == main HEAD (wait_deploy.py); board chips + registry lane source live.
rung: backlog
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces walk 18 lanes tokenless on the anonymous 60-req/h ceiling; the board now also rides the /ideas fetch path per load; headroom is the binding constraint.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10/11: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) lanes.json data-contract ask stands (backlog + slice-16 heartbeat) — /fleet parses your gen_roster.py LANES literal meanwhile. (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102 borderline). (3) meta.md deployed:-line convention ask stands. (4) Q-0264 candidates: twenty-one in docs/ideas/backlog.md (newest: board-row fleet chip — heartbeat freshness on the habit path). NEXT picks: nav overflow guard (RESERVED for the 08:00Z fire), board-row fleet chip, tooling: token. Rungs this chain: …,3,watch-fix,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
