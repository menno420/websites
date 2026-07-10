# websites · status
updated: 2026-07-10T20:36:00Z
phase: CONTINUOUS MODE (manager Q-0265, free-window posture through 2026-07-14): the 20:00Z routine wake is looping the work ladder — slice 1 landed (queue-state NEXT item 3: `.sessions/` card template + ender checklist embedded in `.sessions/README.md`, PR #64 squash-merged on quality green, main `6eb2bb4`). Next rung already picked: queue-state NEXT item 4 — heartbeat enrichment (machine-readable orders/deployed-sha/routine/landing fields + /fleet parser support), same session.
health: green (main HEAD 6eb2bb4 at write; suites 143 passed; bootstrap check --strict green with the slice card complete; quality green on #64 twice — pre- and post-branch-update)
kit: v1.7.0 · check: green · engaged: yes
last-shipped: #64 — .sessions/ card template + ender checklist (embedded in README on purpose: the session gate treats any other .sessions/*.md as a card). Also landed this wake window by a sibling session: #63 (docs/project/routine-prompt.md, third file of the Project package).
blockers: none
routine: ARMED — trigger trig_017H9Qb9oxtLgUy6sw2gnSHg, cron 0 */4 * * *, fresh session per fire; 16:00Z and 20:00Z fires both confirmed by landed work (#59; #63/#64). This session also carries mcp__claude-code-remote__send_later — will self-arm a ~15-min continuation nudge per continuous-mode instruction before session end.
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
notes: Rung this wake: 2 (queue-state NEXT; inbox empty past 008). Stale-ledger fix folded into #64: the queue-state addendum still called PR #59's work "not yet merged" — corrected; resume point moved to NEXT item 4. New idea captured (Q-0264 sim-worthy candidate for the Idea Engine): open-PR awareness at wake — a wake-ritual step listing open PRs + PR-less unmerged claude/* branches before picking a rung (this wake started 6 min after a sibling opened #63; only an ad-hoc PR list prevented a docs/project/README.md merge conflict) — docs/ideas/open-pr-awareness-at-wake-2026-07-10.md. Ruleset finding: merges now require the branch up to date with main (405 "Required status check quality is expected" on a behind branch; update-branch + re-green resolved it) — concurrent-session friction, strengthens the open-PR-awareness case. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched.
