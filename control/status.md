# websites · status
updated: 2026-07-10T02:20:00Z
phase: gen-2 booted (first operator session) — walking skeleton through the landing path (born-red card → READY PR → quality green → squash-merge → /version check); ORDER 005 dossier gathered for the follow-up session, which claims + builds /queue + /environments. ORDER 005 deliberately NOT claimed yet — claim lands immediately before build, per control/README.md.
health: green (all checks green; three services verified post-merge this session)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #51 — gen-2 walking skeleton: landing-path proof + coordinator scheduler-gap OWNER-ACTION (docs-only)
blockers: none
orders: acked=001,002,003,004,005,006,007 done=001,002,003,004,006
⚑ needs-owner: three actionable asks — canonical list (now incl. the new coordinator wake-trigger ask, six fields) lives in docs/owner/OWNER-ACTIONS.md; the two standing six-field asks below are unchanged from gen-1 and still active.
  ⚑ OWNER-ACTION
  WHAT: Arm an external 4-hourly wake trigger for the fleet coordinator — it cannot schedule its own wakes.
  WHERE: claude.ai console → coordinator Project → routines/scheduling UI (agents cannot create routines).
  HOW: recurring 4-hourly routine that opens/resumes the coordinator session with its standing wake prompt (click-only).
  WHY-IT-MATTERS: without it no Class B wake ever fires — the fleet only moves when you manually start a session.
  UNBLOCKS: unattended fleet operation (4-hourly Class B wakes). Fleet operates self-terminal until then.
  VERIFIED-NEEDED: coordinator has NO scheduler primitive (no send_later tool exposed; probe error: "target session could not be verified; retry send_message shortly").
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
  WHY-IT-MATTERS: several board cells run degraded without it, the /owner "re-run CI" button can't act, and ORDER 005's /queue page cannot read menno420/fleet-manager docs/owner-queue.md at runtime (it will ship with an honest-degradation banner until set).
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /queue's fleet-manager half; higher API rate headroom for /fleet + /activity.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set (no such credential in the session env; printenv checked by gen-1).
notes: Gen-2 lane is live. Boot followed docs/succession/next-boot-2026-07-09.md; queue-state + gen-1 status reconciled against live GitHub at HEAD (5f49e3a at boot — zero open PRs before this session's #51; gen-1 done= line carried forward verbatim). ORDER 007 in progress: steps 1–2 (boot + skeleton) this session; steps 3–5 (ORDER 005 build, env-setup.sh wrapper, ledger flips) next session, which starts by CLAIMING 005 on this status line via a control-only fast-lane PR. Rails held: forward-only git, no ambient RAILWAY_* IDs, inbox.md never edited, no destructive ops.
