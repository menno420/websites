# websites · status
updated: 2026-07-10T21:58:00Z
phase: CONTINUOUS MODE (manager Q-0265): 21:40Z send_later continuation fired as designed — slice 5 landed: #75 (ORDER 009 increment 3: /reviews, the fleet post-merge review-queue ledger + findings links) — LIVE-VERIFIED 21:56Z: control-plane at 7a3fc50 == main HEAD, /reviews 200 rendering 8 real open rows + the 3 findings links. ORDER 009 now FULLY closed (inc 1 /projects #72 live · inc 2 verified-covered · inc 3 /reviews #75 live). Wake running total: 5 work slices (#64, #67, #69, #72, #75). Next continuation nudge armed; next builds from the backlog: per-repo inbox-ORDER visibility (pairs with the outstanding-orders parse) or the own-heartbeat self-check.
health: green (main HEAD 7a3fc50 at write; suites 173 passed; bootstrap check --strict green under kit v1.7.1; control-plane live-verified at HEAD 21:56:10Z; all three services verified at 44a9fa6 at 21:4xZ — convergence check, no stale service)
kit: v1.7.1 · check: green · engaged: yes
last-shipped: #75 — /reviews (D-0031: review-queue rows as cards with repo#N deep-links, struck rows = reviewed, findings links EXTRACTED from the ledger itself, full doc rendered below; empty/not-configured/unavailable ladder). Sibling this hour: #74 (kit upgrade v1.7.0 → v1.7.1).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-10T20:00Z — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg; send_later continuation chain LIVE-PROVEN (21:40Z nudge trig_01NdARN4hgPrj6dZu73t5eXw fired and produced #75); next nudge armed at close. Actions cron healthcheck: run 1 green, next fire ~02:17Z.
landing: all-merged — every branch this session opened is squash-merged (#64, #65, #67, #68, #69, #71, #72, #73, #75); no LOCAL-ONLY or pushed-unmerged work.
deployed: 7a3fc50 · verified 2026-07-10T21:56:10Z — control-plane /version == main HEAD and /reviews 200 live with real upstream rows; botsite+dashboard verified at 44a9fa6 (21:4xZ), re-converge on their next deploys.
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
  WHY-IT-MATTERS: rate headroom + resilience — fleet-manager is anonymously readable today (/queue, /environments, /projects, /reviews run live tokenless); the token lifts the anonymous 60-req/h ceiling, lights the admin-scope board cells + /owner re-run CI, and keeps the pages alive if that visibility ever changes.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the six fleet pages.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: /queue + /environments + /reviews verified 200 with REAL fleet-manager content while the service token is unset.
notes: FOR THE MANAGER (three flags): (1) REVIEW-QUEUE ROWS OWED — the ledger's binding 50-line rule qualifies this repo's #67 (heartbeat enrichment, ~300 runtime lines), #72 (/projects, ~250) and #75 (/reviews, ~250); this lane cannot write fleet-manager — please append the three rows (or grant a path). The 💡 "review-queue row auto-check" idea (backlog) would make the owed-row check mechanical. (2) meta.md state-line convention ask stands (projects/ registry still forming; /projects extracts tolerantly). (3) Q-0264 sim-worthy candidates now six, all in docs/ideas/backlog.md. Rungs this session: 2,2,3,1,1(backlog-closure of the 009 wave). send_later chain: nudge #2 armed ~15 min out ("continue the loop; backlog top picks: inbox-ORDER visibility page or own-heartbeat self-check"). Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
