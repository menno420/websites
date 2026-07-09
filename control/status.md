# websites · status
updated: 2026-07-09T20:22:09Z
phase: wind-down complete — ready for archive + fresh session. Gen-1 is fully handed over: queue state committed (#46), succession pack landed (#47 — final retro, next-boot guide, proposed gen-2 Custom Instructions, environment spec, gen-2 blueprint feedback, scripts/setup-env.sh, all linked from docs/AGENT_ORIENTATION.md § Succession). The fresh (gen-2) session's entry point is docs/succession/next-boot-2026-07-09.md. Read the inbox FIRST (done — ORDER 005 remains the only outstanding order, acked + unexecuted + unclaimed); wrote status.md LAST.
health: green (all checks green at wind-down; three services live and in sync at last verification; no open PRs, no stranded branches)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #47 — gen-1 wind-down: succession docs pack (docs + setup script; docs-only + tooling, no runtime change)
blockers: none
orders: acked=001,002,003,004,005,006 done=001,002,003,004,006
⚑ needs-owner: two actionable asks below (six-field format per control/README.md); the canonical owner list — 2 actionable clicks + 6 decision forks — is docs/owner/OWNER-ACTIONS.md (dashboard /admin control API [Q4], botsite /submit provision-vs-stub [Q5], redeploy-from-browser hook yes/no, custom domains [owner-deferred to cutover], v1 visual design vs restyle [Q2], OLD-site cutover go/no-go) — decisions to reply to, not click-actions.
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
notes: GEN-2 HANDOVER — wind-down complete; this lane is ready for archive + a fresh session. The fresh Project boots from main alone: START at docs/succession/next-boot-2026-07-09.md (read order, the ORDER-005 trap, every known wall with verbatim errors), then docs/planning/queue-state-2026-07-09-winddown.md for the prioritized queue; the environment setup script is scripts/setup-env.sh and its spec is docs/succession/environment-spec-2026-07-09.md; proposed gen-2 Custom Instructions are docs/succession/proposed-custom-instructions-2026-07-09.md; owner ⚑ actions stay canonical in docs/owner/OWNER-ACTIONS.md. ORDER 005 (/queue + /environments) is genuinely unexecuted — claim it per control/README.md before building (orders stay `status: new` forever; diff inbox against this file's done= line, never infer execution from a PR title). Rails held: forward-only, websites repo only, superbot/superbot-next/substrate-kit read-only, no secrets, no ambient RAILWAY_* IDs, no destructive ops, inbox.md never edited.
