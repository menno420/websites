# websites · status
updated: 2026-07-11T11:40:00Z
phase: CONTINUOUS MODE (manager Q-0265): 11:30Z nudge — slice 24 landed: #122 (nav manifest, the designated pick): app/nav.py is the single (href,label,key) source for the header nav — base.html iterates it via Jinja globals, the overflow tests import it, and tests/test_nav_manifest.py holds every route's active key to it (membership + uniqueness + no-dead-entries; page 12 physically cannot skip the overflow guard). Presentation only, contracts untouched. LIVE-VERIFIED: manifest-driven dropdown open + highlighted on /orders post-deploy. Premise-check win: the "port to dashboard" idea died on a 30-second source check (dashboard nav already iterates a manifest). Wake running total: 24 work slices (#64→#122) + 2 rescues.
health: green (main HEAD e56d0a2 at write; app suite 182 passed, full three-service suite 240 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #122 — nav manifest (backlog → Built). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session; the ~12:00Z fire is IMMINENT at this write (trigger trig_017H9Qb9oxtLgUy6sw2gnSHg armed, cron 0 */4 * * *) — the chain's next nudge (~12:05Z) rituals right after the window and will rescue/land any stranded work per doctrine. Reading key for the fired session: build PRs' FIRST quality run prints per-card added-card banners + HOLD-by-design (the #120 every-card gate). FOR THE MANAGER: routine-fired sessions remain unreliable landers; the send_later chain is the consistent producer. send_later chain: →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120 →#122.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: e56d0a2 · verified 2026-07-11T11:38Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED); manifest nav live on /orders.
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
notes: backlog: 4 buildable captured (fast-lane control gates port — NEXT natural CI-integrity pick; route-level clock freeze; order-ack latency line; nav-scan glob — this slice's 💡) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#122 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort — next nudge checks the run result either way). Q-0264 candidates: twenty-nine in docs/ideas/backlog.md. Rungs this chain: …,orders,3,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
