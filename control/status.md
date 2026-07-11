# websites · status
updated: 2026-07-11T10:28:00Z
phase: CONTINUOUS MODE (manager Q-0265): 10:15Z nudge — slice 22: **ORDER 011 DONE** (P1, owner-directed ~24h self-review): claimed first (#117), review shipped as docs/retro/self-review-2026-07-11.md (#118, merged 1ff77e4) — went-wrong citation-tied (own mistakes first: PR-number mispredict #67, cron arithmetic 5× #96, claim-matcher boundary FP caught pre-merge #77, suite-scope overclaim #109, doc-truth drift #111; breakages: 08:45Z time-bomb + 17 latent sites #111/#114, registry supersession caught by cron #102, unreliable fired sessions #98; walls per CAPABILITIES), owner items click-level (mirrored below), health one-liner. Lane report convention: dated reviews live in docs/retro/ because this heartbeat is overwritten every wake. The designated quality.yml gate-port pick deferred one slice by the order. Wake running total: 22 work slices (#64→#118) + 2 rescues.
health: green (main HEAD 1ff77e4 at write; app suite 179 passed, full three-service suite 237 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #118 — ORDER 011 self-review (claim #117). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md.
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session (second silent window; 04:03Z stranded heartbeat was rescued as #98). Trigger trig_017H9Qb9oxtLgUy6sw2gnSHg still armed (cron 0 */4 * * *, next ~12:00Z — carried as a watch, not gated on). FOR THE MANAGER: routine-fired sessions remain unreliable landers; the send_later chain is the consistent producer (order pickup latency 011: filed 09:59Z → claimed 10:18Z, ~19 min, nudge-driven). send_later chain: →#81 →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 1ff77e4 · verified 2026-07-11T10:26Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED), /healthz 200.
rung: orders
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
notes: backlog: 4 buildable captured (quality.yml every-card gate port — NEXT designated pick, deferred by ORDER 011; nav manifest; route-level clock freeze; order-ack latency line — this slice's 💡) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107/#109/#111/#114/#118 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort). CI-flag triage this slice: run 29149230736 red on #118 was the born-red hold + two REAL doc findings (invalid badge token, orphan read-path) — both fixed in the flip; NOT a fast-lane or quality.yml issue (quality.yml untouched today). Q-0264 candidates: twenty-seven in docs/ideas/backlog.md. Rungs this chain: …,5,3,orders. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
