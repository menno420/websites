# websites · status
updated: 2026-07-10T20:54:00Z
phase: CONTINUOUS MODE (manager Q-0265, free-window posture through 2026-07-14): the 20:00Z routine wake is looping the work ladder — slice 1 landed (#64, .sessions/ card template, queue-state NEXT item 3), slice 2 landed (#67, heartbeat enrichment, NEXT item 4: /fleet machine-reads orders + the new OPTIONAL routine:/landing:/deployed: lines this very heartbeat now writes — dogfood). Next rung: ladder rung 3 (backlog promotion) — the NEXT list items 1-4 are all DONE; taking the scheduled-healthcheck Actions cron from docs/ideas/backlog.md as slice 3, same session.
health: green (main HEAD 0322682 at write; suites 157 passed; bootstrap check --strict green; all three live services verified /version == 0322682 == main HEAD at 20:51:58Z)
kit: v1.7.0 · check: green · engaged: yes
last-shipped: #67 — heartbeat enrichment ([D-0028]: parse_orders outstanding=acked−done, routine:/landing:/deployed: lines parsed + badged + attention-sorted on /fleet, /fleet.json carries the structures; also fixes the live routine:-into-blockers parse leak). Earlier this wake: #64 (card template), #65 (heartbeat). Siblings same hour: #63 + #66 (routine-prompt v1 + v2, docs/project).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg, fresh session per fire; the 16:00Z and 20:00Z fires both produced landed work (#59; #64/#67). send_later is present in this toolset; a ~15-min continuation nudge will be armed at session end per continuous mode.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67); no LOCAL-ONLY or pushed-unmerged work.
deployed: 0322682 · verified 2026-07-10T20:51:58Z — all three services' /version == main HEAD (scripts/healthcheck.py 6/6 PASS + fleet-manifest live parse 13 lanes)
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
notes: Rungs this wake: slice 1+2 = rung 2 (queue-state NEXT, now exhausted — items 1-4 DONE, item 5 IS the backlog); slice 3 = rung 3 (backlog promotion). Ideas captured (Q-0264 sim-worthy candidates for the Idea Engine): open-PR awareness at wake (docs/ideas/open-pr-awareness-at-wake-2026-07-10.md — lived twice this hour: woke 6 min after sibling PR #63; both #64 and #67 blocked 405 "Required status check quality is expected" because the ruleset now ALSO requires branch-up-to-date and siblings kept moving main — update-branch + re-green resolved both) and own-heartbeat parse self-check in quality (backlog, dogfood pair to D-0028). Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
