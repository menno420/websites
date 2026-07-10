# websites · status
updated: 2026-07-10T02:44:17Z
phase: ORDER 005 shipped + live-verified (claim PR #52 → build PR #53 → all three services at main HEAD 74d6c97 within ~2 min of merge; live /queue + /environments both 200). ORDER 007 complete (boot #51, skeleton #51, ORDER 005 #52/#53, env-setup.sh wrapper #53, ledgers flipped #53). Standing default next: queue-state NEXT list top-to-bottom (item 2: /fleet manifest-parse smoke check).
health: green (quality green on #52/#53; suites 140 passed; healthcheck 6/6 PASS; /version == main HEAD on all three services)
kit: v1.6.0 · check: green · engaged: yes
last-shipped: #53 — ORDER 005: /queue owner to-do surface + /environments registry view (+ env-setup.sh wrapper; decision stamped in docs/site.md + the decision ledger)
blockers: none
orders: acked=001,002,003,004,005,006,007,008 done=001,002,003,004,005,006,007 claimed-by: 008 gen2-closeout 2026-07-10T13:48Z
⚑ needs-owner: three actionable asks — canonical list lives in docs/owner/OWNER-ACTIONS.md; six-field blocks below (PAT ask updated with a live finding: fleet-manager is anonymously readable today, so /queue + /environments run LIVE tokenless — the token ask stands for rate headroom, admin-scope cells, and resilience, no longer as the only path to fleet-manager).
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
  WHY-IT-MATTERS: several board cells run degraded without it, the /owner "re-run CI" button can't act, and every GitHub read rides the anonymous 60-req/h rate limit; /queue + /environments happen to run live tokenless today ONLY because fleet-manager is publicly readable — the token keeps them alive if that changes and lifts the rate ceiling.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /owner re-run CI; 5000 req/h headroom for /fleet + /activity + /queue + /environments.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set (no such credential in the session env; printenv checked by gen-1). Live finding 2026-07-10: /queue + /environments verified 200 with REAL fleet-manager content while the service token is unset (anonymous raw + contents API on a public repo).
notes: ORDER 005 done-when met and exceeded: /queue and /environments live at main HEAD 74d6c97 and verified against the running deploy — both 200; expected honest-degradation state did NOT occur because menno420/fleet-manager is anonymously readable (a corrected assumption — the "private, runtime-token-only" claim in the handoff dossier was an inference, not a verified wall; both pages still carry tested not-configured/unavailable degradation for the failure cases). ORDER 007 fully complete (all five steps + done-when). Claim dropped from the orders line per protocol. Rails held: forward-only git, no ambient RAILWAY_* IDs, inbox.md never edited, no destructive ops, one writer per file. Next session default: docs/planning/queue-state-2026-07-09-winddown.md NEXT list item 2 onward.
