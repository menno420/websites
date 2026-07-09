# websites · status
updated: 2026-07-09T19:55:00Z
phase: substrate-kit upgraded v1.2.0 → v1.6.0 via the kit's §4.3 release flow (sha256-verified asset, archive-first, report-classified); v1.3.0–v1.6.0 conventions inherited (this kit: line, CAPABILITIES.md + orientation wiring, owner-action six-field format, order-claim ritual in control/README.md). Read the inbox FIRST — PING-ACK ORDER 006 landed immediately as fast-lane PR #44; wrote status.md LAST.
health: green (bootstrap.py check --strict green — the one enforced finding (CAPABILITIES.md orphan) fixed by wiring it into the orientation reading order; owner-action advisory cleared by the six-field reformat below; full suite 125 passed incl. the kit_version pin test moved 1.2.0 → 1.6.0; ambient-Railway-ID guard OK)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #45 — substrate-kit upgrade v1.2.0 → v1.6.0 ([D-0026]): §4.3 flow (asset sha256 787d5617… verified against release.json + bootstrap.py.sha256; old dist banked at .substrate/backup/bootstrap-1.2.0.py with the committed --rollback path); report: 13 consumer-edited (kept), 5 diverged (kept live + additive template deltas hand-merged: capabilities doctrine into CONSTITUTION/collaboration-model/AGENT_ORIENTATION, claim-ritual + kit-line + OWNER-ACTION format into control/README.md), 1 template-improved applied (.claude/CLAUDE.md), CAPABILITIES.md planted + seeded with this repo's verified findings.
blockers: none
orders: acked=001,002,003,004,005,006 done=001,002,003,004,006
PING-ACK ORDER 006 · discovered 2026-07-09T19:24:41Z · via mid-session inbox check (coordinator-tasked kit-upgrade session; start-of-work inbox read)
⚑ needs-owner: two actionable asks below (six-field format per control/README.md); the owner-gated DECISION forks (dashboard /admin control API [Q4], v1 visual design vs restyle [Q2], OLD-site cutover go/no-go, redeploy-from-browser hook yes/no, optional bot health URL) stay parked in docs/owner/OWNER-ACTIONS.md — decisions to reply to, not click-actions, so they live in the durable list rather than re-burning heartbeat attention every session.
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
  WHY-IT-MATTERS: several board cells run degraded without it and the /owner "re-run CI" button can't act.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; higher API rate headroom for /fleet + /activity.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set (no such credential in the session env; printenv checked).
  (custom domains for the 3 sites: still open but parked in OWNER-ACTIONS.md #4 — deferred to cutover by your own note, so not an active ask.)
notes: ORDER 005 (/queue + /environments) is acked and genuinely unexecuted — PR #42 was the manager's inbox append, and /queue 404s on the live deploy at main head 9ed43cf ; it needs a session scoped to it (this one was coordinator-tasked to the kit upgrade; per the new claim ritual, an executor should claim 005 on this line first). Kit upgrade friction relayed to kit-lab via the coordinator: upgrade's "old copy archived" log line names the NEW dist's backup file (bootstrap-1.6.0.py) — rollback metadata (last-upgrade.json → bootstrap-1.2.0.py) is correct, message is misleading. Rails held: forward-only, websites repo only, superbot/superbot-next/substrate-kit read-only, no secrets, no ambient RAILWAY_* IDs, no destructive ops, inbox.md never edited.
