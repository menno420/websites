# websites · status
updated: 2026-07-10T19:38:42Z
phase: never-idle doctrine landed — the work ladder is now in docs/project/project-instructions.md (PR #61): every wake picks the first rung with work (inbox ORDER → queue-state NEXT → docs/ideas/backlog.md promotion → ⚑ self-initiated improvement → upkeep + honest "backlog dry" signal) and ships one increment, plus two mandatory enders (one genuine idea/session, one-line previous-session review). First fire under the ladder = the next 4-hourly wake. Resume point for that wake: queue-state NEXT item 3 (.sessions/ card template with 📊 Model line + ender checklist — now also `planned` in docs/ideas/backlog.md).
health: green (main HEAD f6e3cc3 at write; suites 143 passed; bootstrap check --strict green at close-out; #61 pending quality at write, squash-merge on green)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #60 — Project env package (setup script + Custom Instructions + landing-failure root cause); #61 in flight at write (never-idle work ladder + seeded ideas backlog: 11 captured/planned ideas, each cited)
blockers: none
routine: ARMED + first fire CONFIRMED — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg, cron 0 */4 * * *, fresh session per fire; list_triggers last_fired_at 2026-07-10T16:01:32Z, confirmed by PR #59; the conditional owner wake-fallback ⚑ is withdrawn (self-expired per its own terms). Trigger prompt unchanged — it delegates to the instructions file, so the new ladder governs every future fire without touching the trigger.
orders: acked=001,002,003,004,005,006,007,008 done=001,002,003,004,005,006,007,008
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
  WHY-IT-MATTERS: justified by rate headroom + resilience, not access — fleet-manager is anonymously readable today, so /queue + /environments run live tokenless; the token lifts the anonymous 60-req/h ceiling, lights the admin-scope board cells + /owner re-run CI, and keeps the pages alive if that visibility ever changes.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /owner re-run CI; 5000 req/h headroom for /fleet + /activity + /queue + /environments.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue + /environments verified 200 with REAL fleet-manager content while the service token is unset.
notes: The idle gap this closes: instructions covered mechanics but not work generation — a wake with a dry inbox and exhausted NEXT list had no doctrine telling it to invent + groom + build. docs/ideas/backlog.md is now the single backlog home (README carries lifecycle captured→planned→built→retired + dedup rule); it includes the PR #9 claude/rework-dashboard salvage re-check (launch-readiness flag) and ladder-rung telemetry (this session's 💡). Rails held: forward-only git, inbox.md never edited, one writer per file, no force-push, trigger untouched.
