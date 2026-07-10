# websites · status
updated: 2026-07-10T21:24:00Z
phase: CONTINUOUS MODE (manager Q-0265): 20:00Z wake, FOUR slices landed this session — #64 (card template, NEXT item 3), #67 (heartbeat enrichment, NEXT item 4), #69 (scheduled healthcheck cron, backlog promotion; run 1 SUCCESS), #72 (ORDER 009 increment 1: /projects registry page — LIVE-VERIFIED 21:21Z: control-plane at a8b5a07 == main HEAD, /projects 200 with the honest "registry not landed yet" empty state while the upstream folder is still landing). ORDER 009 → done (inc 1 shipped+live; inc 2 verified already-covered on /fleet, skipped per the order; inc 3 ledgered as a planned backlog bullet per the done-when). Next wake resumes the ladder: rung 1 = any new order at inbox HEAD, else rung 3 = docs/ideas/backlog.md (ORDER 009 increment 3 is the planned top pick).
health: green (main HEAD a8b5a07 at write; suites 165 passed; bootstrap check --strict green; control-plane live-verified at HEAD 21:21Z; healthcheck workflow run 1 success — next cron fire ~02:17Z)
kit: v1.7.0 · check: green · engaged: yes
last-shipped: #72 — /projects (D-0030: fleet-manager projects/ registry, per-package role-classified cards + meta.md deployed-state badge, first-class empty state; nav + /projects.json). Wake total: #64, #65, #67, #68, #69, #71, #72 (+ siblings #63, #66, #70-inbox).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; plus the repo's own Actions cron (healthcheck, 17 */6 * * *, run 1 green). send_later continuation nudge armed at session close per continuous mode (see notes).
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69, #71, #72); no LOCAL-ONLY or pushed-unmerged work.
deployed: a8b5a07 · verified 2026-07-10T21:21:23Z — control-plane /version == main HEAD and /projects 200 live; botsite+dashboard verified at 0322682 earlier this wake (20:51:58Z, 6/6 PASS), re-converge expected on their next deploys.
orders: acked=001,002,003,004,005,006,007,008,009 done=001,002,003,004,005,006,007,008,009
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
  WHY-IT-MATTERS: justified by rate headroom + resilience — fleet-manager is anonymously readable today (/queue, /environments, /projects run live tokenless); the token lifts the anonymous 60-req/h ceiling, lights the admin-scope board cells + /owner re-run CI, and keeps the pages alive if that visibility ever changes.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells go live; /owner re-run CI; 5000 req/h headroom for /fleet + /activity + /queue + /environments + /projects.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue + /environments verified 200 with REAL fleet-manager content while the service token is unset.
notes: FOR THE MANAGER (two flags): (1) Q-0264 sim-worthy idea candidates this wake, all in docs/ideas/backlog.md — open-PR awareness at wake (lived twice: sibling PR #63 six minutes before wake; #64/#67 both 405-blocked by the branch-up-to-date rule while siblings moved main), own-heartbeat parse self-check, healthcheck-failure auto-files an issue (alert routing to agent-visible surfaces), meta.md state-line convention. (2) REGISTRY CONVENTION ASK: while projects/ is still forming, standardize one `deployed:` line format in projects/*/meta.md (e.g. `deployed: <where> · <ISO date>`) — /projects extracts the state badge tolerantly but an agreed line at zero-packages cost makes it exact forever. Rungs this wake: 2, 2, 3, 1. send_later: armed ~15 min out at session close ("continue the websites work loop") — if no follow-up heartbeat lands after that, the nudge fired into a dead session and the 4-hourly cron is the pacemaker. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
