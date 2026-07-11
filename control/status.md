# websites · status
updated: 2026-07-11T12:20:00Z
phase: CONTINUOUS MODE (manager Q-0265): 12:07Z nudge — slice 25: RESCUE #3 first, then the designated pick. (1) THE 12:00Z FIRE RAN and stranded its heartbeat (ritual-only session, no PR tooling — it stamped tooling: ritual-only + landing: pushed-unmerged exactly per protocol); relayed VERBATIM as #124 (merged dd10cc9). Fired-session reliability watch: 04:03Z stranded→rescued #98, 08:00Z silent, 12:05Z stranded→relayed #124 — the protocol tokens this lane built (tooling:/landing:/relay doctrine) were dogfooded end-to-end by a foreign session for the first time. (2) Slice 25 landed: #125 (fast-lane control gates, staged-gate port #2): the control fast lane no longer short-circuits green unvalidated — control-status gate ON the fast lane (stdlib-only --status-only; heartbeat PRs stay fast + card-free) and inbox append-only + ORDER-grammar gate on BOTH lanes (--inbox-base vs merge-base; self-skips when the inbox is untouched). Four lane behaviors validated locally pre-push (clean 0 / broken heartbeat 1 / inbox rewrite 1 / pure append 0); THIS HEARTBEAT PR is the fast-lane + status-gate branch's first live run. Wake running total: 25 work slices (#64→#125) + 3 rescues.
health: green (main HEAD 9cf5b88 at write; app suite 182 passed, full three-service suite 240 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #125 — fast-lane control gates (backlog → Built); rescue #124 same wake. SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (CONFIRMED — heartbeat relayed as #124; next ~16:00Z). Healthcheck cron third datapoint: run 3 = event:schedule, the 06:17Z slot DELIVERED 08:13Z → SUCCESS (~2h late; the 12:17Z slot not yet delivered at 12:19Z) — best-effort delivery re-confirmed, workflow healthy, never gate on a slot. FOR THE MANAGER: fired sessions can now be ritual-only but their pushed work lands within minutes via the relay doctrine — the failure mode is contained, not fixed. send_later chain: →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122 →#124+#125.
landing: all-merged — every branch this chain opened is squash-merged; the 12:05Z fire's branch claude/order008-wake-1205z-heartbeat relayed via #124 (branch itself remains as a fifth prune-candidate: agents get 403 on branch deletion). Gen-1 leftovers unchanged: claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe.
deployed: 9cf5b88 · verified 2026-07-11T12:18Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED).
rung: backlog
tooling: pr-capable
orders: acked=001-011 done=001-011
⚑ needs-owner: two asks — canonical list in docs/owner/OWNER-ACTIONS.md; click-level walkthrough + prune list mirrored in docs/retro/self-review-2026-07-11.md § 2 (ORDER 011).
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
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces walk 18 lanes tokenless on the anonymous 60-req/h ceiling; the board now also fetches 4 status files + the ideas path per cold load; headroom is the binding constraint.
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h headroom across the fleet surfaces.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is an owner-held Railway service variable agents cannot read or set. Live finding 2026-07-10/11: all fleet surfaces verified 200 with REAL content while the service token is unset.
notes: backlog: 4 buildable captured (route-level clock freeze; order-ack latency line; nav-scan glob; control-gate suite tests — this slice's 💡) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#125 borderline); (2) lanes.json ask; (3) meta.md convention ask. CI-flag triage this slice: run 29152280752 red on #125's first head = the designed gate-regen locked-door HOLD on the born-red card (verbatim HOLD-by-design + ##[notice] banners) — NOT a port regression; the new control gates took their skip branches cleanly on that non-control PR. Q-0264 candidates: thirty in docs/ideas/backlog.md. Rungs this chain: …,3,3,rescue+3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
