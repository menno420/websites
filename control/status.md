# websites · status
updated: 2026-07-10T13:56:12Z
phase: gen-2 close-out complete — idle until next wake (self-armed routine, first fire due 2026-07-10T16:00Z). Session chain: #51 skeleton → #52 claim 005 → #53 build (/queue + /environments) → #54 status → #55 ORDER 008 inbox → #56 claim 008 → #57 close-out docs sweep → this heartbeat. Next session resume point: docs/planning/queue-state-2026-07-09-winddown.md § Gen-2 close-out addendum (NEXT item 2, /fleet manifest-parse smoke check).
health: green (main HEAD 4339bd5 at write; scripts/healthcheck.py exit 0 — 6/6 PASS, all three services /healthz + / → 200; suites 140 passed; quality green on #56/#57; coordinator independently verified /version ×3 + /queue + /environments at 330f9b4, ~02:50Z)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #57 — gen-2 close-out docs sweep (CAPABILITIES corrections: fleet-manager anonymously readable + routines self-armable from worker surface; wake-⚑ resolved to conditional fallback; next-session brief; journal gotchas)
blockers: none
routine: ARMED, first fire unconfirmed — ORDER 008 executed 2026-07-10T13:49:36Z via the worker-session scheduler primitive mcp__claude-code-remote__create_trigger (exact mechanism; no UI path involved): trigger trig_017H9Qb9oxtLgUy6sw2gnSHg, cron 0 */4 * * *, enabled, fresh session per fire, prompt = the standing inbox ritual, next_run_at 2026-07-10T16:00:31Z. First successful fire NOT yet observed (due after this session ends) — the first routine-woken heartbeat overwrite is the confirmation; conditional owner fallback filed below per the order's failure branch. Historical (still true for the coordinator surface): the coordinator toolset exposes no send_later/scheduling tool at all; its probe error verbatim: "target session could not be verified; retry send_message shortly".
orders: acked=001,002,003,004,005,006,007,008 done=001,002,003,004,005,006,007,008
⚑ needs-owner: three asks — canonical list in docs/owner/OWNER-ACTIONS.md; wake-trigger ask is now CONDITIONAL only (self-armed per ORDER 008).
  ⚑ OWNER-ACTION (CONDITIONAL — only if the self-armed routine proves dead)
  WHAT: Arm an external 4-hourly wake trigger for this lane ONLY IF no fresh websites heartbeat appears by 2026-07-11 (first self-armed fires will have been due).
  WHERE: claude.ai console → websites Project → routines/scheduling UI.
  HOW: recurring 4-hourly routine with the standing wake prompt "Read control/inbox.md at HEAD and run the standing ritual from your instructions." (click-only).
  WHY-IT-MATTERS: if the self-armed trigger silently fails, no session wakes to re-file this ask — the lane goes dark unwatched.
  UNBLOCKS: nothing today (routine armed: trig_017H9Qb9oxtLgUy6sw2gnSHg, cron 0 */4 * * *, next fire 2026-07-10T16:00Z); self-expires the moment a routine-woken heartbeat lands.
  VERIFIED-NEEDED: armed 13:49Z but first fire is due 16:00Z, after this session ends — armed-but-unconfirmed is not the same fact as working; the failure branch of ORDER 008's done-when requires this fallback to exist.
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
  WHY-IT-MATTERS: justified by rate headroom + resilience, not access — fleet-manager is anonymously readable today (verified via the app's own runtime fetch path), so /queue + /environments run live tokenless; the token lifts the anonymous 60-req/h ceiling, lights the admin-scope board cells + /owner re-run CI, and keeps the pages alive if that visibility ever changes.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /owner re-run CI; 5000 req/h headroom for /fleet + /activity + /queue + /environments.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set (no such credential in the session env; printenv checked by gen-1). Live finding 2026-07-10: /queue + /environments verified 200 with REAL fleet-manager content while the service token is unset.
notes: ORDER 008 done-when met on the success branch as written ("routine armed and mechanism documented in status") — with the honest caveat above that first-fire confirmation is structurally impossible in the arming session; the conditional fallback covers the failure branch. Claim #56 dropped from the orders line per protocol. Fleet-manager anonymous-readability correction + routine-creation capability are durable in docs/CAPABILITIES.md (append log, 2026-07-10); next-session brief in docs/planning/queue-state-2026-07-09-winddown.md § Gen-2 close-out addendum. Rails held: forward-only git, no ambient RAILWAY_* IDs, inbox.md never edited, no destructive ops, one writer per file, no force-push.
