# websites · status
updated: 2026-07-11T11:05:00Z
phase: CONTINUOUS MODE (manager Q-0265): 10:55Z nudge — slice 23 landed: #120 (quality.yml EVERY-CARD session gate, the twice-deferred designated pick): the folded lane's tail -1 single-card picker (multi-card shadowing loophole) replaced with the kit v1.10.1 staged-gate loop — added cards get the per-card born-red HOLD lane (modified siblings advisory-only), modified-only diffs get the locked door per card, no-card diffs use the explicit advisory sentinel (never the mtime fallback), and PRs touching the gate file keep the full locked door + --simulate-added-card (semantics only tighten mid-PR); gate_regen path adapted to quality.yml; control fast lane untouched (byte-identical step). VALIDATED LIVE ON ITS OWN PR: first run exercised the gate-regen branch (locked-door + simulation banner + designed HOLD, run 29150232291), flip run green (29150291841), main-push run green under the new gate (29150311784). Wake running total: 23 work slices (#64→#120) + 2 rescues.
health: green (main HEAD 211aa2f at write; app suite 179 passed, full three-service suite 237 passed; bootstrap check --strict green under kit v1.10.1)
kit: v1.10.1 · check: green · engaged: yes
last-shipped: #120 — every-card session gate in quality.yml (backlog → Built). SELF-REVIEW POINTER: docs/retro/self-review-2026-07-11.md (ORDER 011, #118).
blockers: none
routine: fired-silent — the ~08:00Z window produced no visible session (second silent window; 04:03Z stranded heartbeat was rescued as #98). Trigger trig_017H9Qb9oxtLgUy6sw2gnSHg still armed (cron 0 */4 * * *, next ~12:00Z — carried as a watch, not gated on; NOTE for the next fire's session: build PRs' FIRST quality run now prints per-card added-card/locked-door banners — the HOLD-by-design reading key is unchanged). FOR THE MANAGER: routine-fired sessions remain unreliable landers; the send_later chain is the consistent producer. send_later chain: →#83 →#86 →#88 →#90 →#92 →#96 →#99 →#102 →#104 →#107 →#109 →#111 →#114 →#118 →#120.
landing: all-merged — every branch this chain opened is squash-merged; four gen-1 leftover branches remain prune-candidates (claude/harden-verify, claude/rework-dashboard, claude/wire-github-token-docs, manager/control-plant — all verified landed/safe; owner-attention: agents get 403 on branch deletion).
deployed: 211aa2f · verified 2026-07-11T11:02Z — ALL THREE services /version == main HEAD (wait_deploy.py CONVERGED).
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
notes: backlog: 4 buildable captured (nav manifest — NEXT designated pick; fast-lane control gates port — this slice's 💡, the natural CI-integrity successor: the folded fast lane currently short-circuits with NO validation while the staged gate runs control-status + inbox append-only checks; route-level clock freeze; order-ack latency line) plus the two manager-side asks. Standing flags: (1) REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86/#96/#102/#104/#107/#109/#111/#114/#118/#120 borderline); (2) lanes.json ask; (3) meta.md convention ask; (4) healthcheck cron next slot ~12:17Z (wall-clock anchored, best-effort). Q-0264 candidates: twenty-eight in docs/ideas/backlog.md. Rungs this chain: …,3,orders,3. Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs.
