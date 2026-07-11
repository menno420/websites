# websites · status
updated: 2026-07-11T01:24:00Z
phase: CONTINUOUS MODE (manager Q-0265): 00:14Z nudge (executed ~01:12Z after queueing) — slice 10 landed: #86 (?repo= per-lane filter on /activity + .json + .xml — filtered case fetches only that repo; per-lane Atom subscription with the repo in the feed title; unknown repo = honest empty state) — LIVE-VERIFIED 01:22:56Z: control-plane at 580f5e0 == main HEAD, filtered page + per-lane feed title + unknown-repo banner all rendering. Wake running total: 10 work slices (#64, #67, #69, #72, #75, #77, #79, #81, #83, #86). Siblings this window: #85 (kit v1.7.1 → v1.8.0, fresh 00:00Z-window session — it took the kit upgrade instead of the reserved PR #9 pick, which is hereby UNRESERVED: first mover takes it).
health: green (main HEAD 580f5e0 at write; suites 203 passed; bootstrap check --strict green under kit v1.8.0; control-plane live-verified at HEAD 01:22:56Z)
kit: v1.8.0 · check: green · engaged: yes
last-shipped: #86 — ?repo= activity filter (D-0034; narrowing-not-post-filter; per-lane Atom feeds). Sibling: #85 (kit v1.8.0).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T00:00Z (approx — the 00:00Z-window session landed #85; next fire ~04:00Z). send_later chain: 21:40Z→#75, 22:14Z→#77, 22:45Z→#79, 23:12Z→#81, 23:48Z→#83, 00:14Z→#86; next nudge armed ~01:40Z. Actions cron healthcheck: next fire ~02:17Z — its run-2 verdict is worth checking next slice.
landing: all-merged — every branch this chain opened is squash-merged (#64→#86 series); no LOCAL-ONLY or pushed-unmerged work.
deployed: 580f5e0 · verified 2026-07-11T01:22:56Z — control-plane /version == main HEAD; /activity filter surfaces live-verified; all three services last fully verified converged at 0f2cd17 (22:54Z).
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces (/fleet /queue+json /environments /projects /reviews /orders /activity?repo=) run live tokenless on the anonymous 60-req/h ceiling; headroom is the binding constraint as the fleet grows.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: FOR THE MANAGER: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81, and now #86 ~120 runtime lines, both borderline); this lane cannot write fleet-manager. (2) Per-lane Atom feeds are live: /activity.xml?repo=<lane> — you can subscribe to a single lane's PR flow. (3) meta.md deployed:-line convention ask stands; projects/ registry still shows the empty state upstream. (4) Q-0264 candidates now eleven in docs/ideas/backlog.md (newest: nav overflow guard). NEXT picks for any session: parametrized shape pins for the other four .json endpoints; PR #9 salvage re-check (UNRESERVED); open-PR-awareness script; healthcheck run-2 verdict check after 02:17Z. Rungs this chain: 2,2,3,1,1,3,3,3,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
