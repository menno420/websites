# websites · status
updated: 2026-07-09T20:00:21Z
phase: gen-1 wind-down — lane handing over gen-1 → gen-2. Open PRs settled (zero found open); the DONE / IN-FLIGHT / NEXT queue snapshot committed to docs/planning/queue-state-2026-07-09-winddown.md so a fresh Project boots from main alone. Read the inbox FIRST (done — ORDER 005 remains the only outstanding order, acked + unexecuted + unclaimed); wrote status.md LAST.
health: green (all checks green at wind-down; three services live and in sync at last verification; no open PRs, no stranded branches)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #46 — gen-1 wind-down: queue state committed (DONE / IN-FLIGHT / NEXT handover ledger for gen-2; docs-only)
blockers: none
orders: acked=001,002,003,004,005,006 done=001,002,003,004,006
⚑ needs-owner: two actionable asks below (six-field format per control/README.md); the owner-gated DECISION forks (dashboard /admin control API [Q4], v1 visual design vs restyle [Q2], OLD-site cutover go/no-go, redeploy-from-browser hook yes/no, optional bot health URL) stay parked in docs/owner/OWNER-ACTIONS.md — decisions to reply to, not click-actions.
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
notes: GEN-2 HANDOVER — the next session in this lane is a fresh Project: boot from .claude/CLAUDE.md → docs/current-state.md → docs/CAPABILITIES.md → docs/AGENT_ORIENTATION.md, then docs/planning/queue-state-2026-07-09-winddown.md for the prioritized queue. ORDER 005 (/queue + /environments) is genuinely unexecuted — claim it per control/README.md before building (orders stay `status: new` forever; diff inbox against this file's done= line, never infer execution from a PR title). Gen-1's lived friction is in docs/retro/self-review-2026-07-09.md + docs/retro/project-review-2026-07-09.md. Rails held: forward-only, websites repo only, superbot/superbot-next/substrate-kit read-only, no secrets, no ambient RAILWAY_* IDs, no destructive ops, inbox.md never edited.
