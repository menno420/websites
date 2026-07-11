# websites · status
updated: 2026-07-11T12:08:00Z
phase: ORDER 008 routine wake — the self-armed 4-hourly trigger (trig_017H9Qb9oxtLgUy6sw2gnSHg, cron 0 */4 * * *) fired ~12:05Z, exactly the slot the prior heartbeat flagged IMMINENT; this session IS that fire. Ran the standing per-session ritual: fetched + landed on origin/main HEAD (08ef404, unchanged since the last heartbeat — no commits landed between 11:40Z and this wake); read control/inbox.md at HEAD — highest order is still 011 and this lane's own done= already covers 001-011, so there was no `status: new` order to claim/execute this wake. Re-verified rather than assumed: full three-service suite 240 passed, `bootstrap.py check --strict` green, all three live services' `/version` == main HEAD 08ef404 (control-plane, dashboard, botsite). `git ls-remote --heads` shows no branches beyond the four already-documented gen-1 prune-candidates — nothing stranded to rescue.
health: green (main HEAD 08ef404 at write; full three-service suite 240 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #122 — nav manifest (unchanged; no new build this wake — no order/queue/backlog work fired, this was a pure ritual+verify wake). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z — CONFIRMED VISIBLE (resolves the prior fired-silent ~08:00Z note for THIS slot; trigger last_fired_at will show ~12:05Z on next list_triggers). FOR THE MANAGER: this fired session's own toolset exposed NO PR-creation tooling (ToolSearch for create/merge-PR tools found nothing — matches the 2026-07-10 CAPABILITIES.md wall finding for routine-fired sessions); repo-management + plain git push are present. This heartbeat is landing via that push-only path — see landing: below.
landing: pushed-unmerged claude/order008-wake-1205z-heartbeat — control-only (this file alone); pushed by this routine-fired session, which lacks PR-creation tooling this wake (see routine: line); needs an interactive/PR-capable session (or the send_later chain) to open+merge per the relay doctrine (control/README.md § Landing other sessions' control-only work) if it doesn't land before the next wake. Gen-1 leftover branches unchanged: claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion.
deployed: 08ef404 · verified 2026-07-11T12:07Z — ALL THREE services /version == main HEAD (curl-verified this wake).
rung: upkeep-dry
tooling: ritual-only
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
notes: backlog: 4 buildable captured (fast-lane control gates port — NEXT natural CI-integrity pick; route-level clock freeze; order-ack latency line; nav-scan glob — this slice's 💡) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#122 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort — next nudge checks the run result either way). Q-0264 candidates: twenty-nine in docs/ideas/backlog.md. Rungs this chain: …,orders,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
