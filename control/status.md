# websites · status
updated: 2026-07-11T03:36:00Z
phase: CONTINUOUS MODE (manager Q-0265): 03:31Z nudge — ORDER 010 relay (PR #94, manager append) merged by this chain to unblock the bus; ORDER 010 CLAIMED (execution = slice 14, this session: template verification + this wake's card as the done-when proof + picks b/c). Previous: slice 13 landed: #92 (/ideas lifecycle-state surfacing: front-matter state badges + per-repo conveyor-health counts + ?state= filter that narrows the list never the counts; PLUS scripts/wait_deploy.py — the sha-convergence poller, which VERIFIED ITS OWN MERGE: "CONVERGED: all 3 services at 3f2ea621" — hand-curling /version is retired doctrine). Wake running total: 13 work slices (#64, #67, #69, #72, #75, #77, #79, #81, #83, #86, #88, #90, #92). STANDING WATCH: healthcheck cron verdict due after 06:17Z (zero scheduled runs so far — provisional wall in docs/CAPABILITIES.md).
health: green (main HEAD 3f2ea62 at write; suites 217 passed; bootstrap check --strict green under kit v1.8.0; ALL THREE services converged at 3f2ea62 == main HEAD — verified by wait_deploy.py 03:08Z)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #92 — /ideas conveyor health + wait_deploy poller (first live runs of both green).
blockers: none
routine: armed · cron 0 */4 * * * — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; next fire ~04:00Z (its fresh session: read this heartbeat, take non-overlapping backlog work — nav overflow guard or cron-slot helper are free; the 06:17Z cron verdict belongs to whichever session is awake then). send_later chain: →#75 →#77 →#79 →#81 →#83 →#86 →#88 →#90 →#92; next nudge armed ~03:30Z. Actions cron healthcheck: SCHEDULE UNPROVEN — verdict slot 06:17Z.
landing: all-merged — every branch this chain opened is squash-merged (#64→#92 series); four gen-1 leftover branches remain prune-candidates (open_work.py classifies them mechanically).
deployed: 3f2ea62 · verified 2026-07-11T03:08:13Z — ALL THREE services /version == main HEAD (wait_deploy.py, one poll).
rung: backlog
orders: acked=001-010 done=001-009 claimed-by: 010 websites-continuous-wake 2026-07-11T03:36Z
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces run live tokenless on the anonymous 60-req/h ceiling; /ideas now fetches up to 24 files per repo per cache window, so headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) HEALTHCHECK CRON WATCH stands — verdict 06:17Z. (2) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81/#86 borderline). (3) Conveyor health is live: /ideas shows per-repo captured/planned/built/retired counts + ?state= filter — the idea-flow conversion glance. (4) wait_deploy.py is the new merge-verification doctrine (deterministic PASS/FAIL, proven on its own merge). (5) Q-0264 candidates now sixteen in docs/ideas/backlog.md (newest: board-row conveyor chips). NEXT picks: 06:17Z cron verdict, nav overflow guard, cron-slot helper, review-row auto-check, board-row chips. Rungs this chain: 2,2,3,1,1,3,3,3,3,3,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
