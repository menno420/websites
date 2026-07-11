# websites · status
updated: 2026-07-11T16:20:00Z
phase: OWNER EXPANSION DIRECTIVE executed (review-site expansion, PR #141 open pending merge): the review/ service grew from a one-shot report into the continuous review channel — /fleet (+detail +json) from a baked fleet-manager registry mirror (19 seats = 18 repo-backed + 1 registry-only, counts rendered AS FOUND, unreadable lanes labeled), scheduled review-bake workflow (daily cron + dispatch → regenerates snapshot/fleet/stats, lands data-only diff via push→auto-merge-PR→open-PR cascade), /reviews editions + valid Atom feed (edition #1 seeded from the ORDER 011 retro; ritual in review/README.md), /questionnaire (12 evidence-cited answers) + /questions ledger, prefilled-issue ask links on every page (read-only interaction). Claim: this session claimed the review-expansion scope born-red on branch claude/review-site-expansion (scope verified unclaimed at fc8087c, zero open PRs at start).
health: green (main HEAD fc8087c at write; PR #141 head 754d710: full FOUR-service suite 322 passed (review 28→67); bootstrap check --strict green after card flip; the head-971e967 quality red was the DESIGNED born-red hold, verbatim-verified in the job log)
kit: v1.11.0 · check: green · engaged: yes
last-shipped: PR #141 OPEN (READY, awaiting merge — agents cannot self-merge): review-site expansion. Before it: #139 provenance advisory (chain slice 31).
blockers: none — PR #141 needs a merge click (or the chain's next wake merges it on green per relay doctrine).
routine: armed · cron 0 */4 * * * · last-fired 2026-07-11T12:05Z (relayed #124) — the ~16:00Z fire not yet evidenced at this write.
landing: pushed-unmerged — claude/review-site-expansion @ 754d710, PR #141 READY, quality expected green post-flip; everything else all-merged (prune-candidate list unchanged, owner 403 wall).
deployed: fc8087c · three existing services in sync at last chain verify 15:51Z; review/ service still awaiting owner creation (⚑ below) — the expansion deploys with it.
rung: order (owner expansion directive, relayed by the coordinator)
tooling: pr-capable
orders: acked=001-011 done=001-011
⚑ needs-owner: THREE standing asks — canonical list in docs/owner/OWNER-ACTIONS.md (botsite DATABASE_URL; control-plane GITHUB_TOKEN — now ALSO unlocks richer review-bake stats for private fleet repos, see the PAT side-note there; create the review/ Railway service: Root Directory = review, no env vars — the ask now covers the expanded site incl. the subscribable /reviews/feed.xml). Plus one click-adjacent item: MERGE PR #141 when quality is green (self-merge denied to agents).
  ⚑ OWNER-ACTION
  WHAT: Create a small Postgres for the botsite /submit intake and point the botsite service at it.
  WHERE: railway.app → project superbot-websites → New → Database → PostgreSQL; then service botsite → Variables.
  HOW: add variable DATABASE_URL = the new Postgres connection string Railway shows (copy-paste).
  WHY-IT-MATTERS: the public feature/bug submission form is a labeled stub until a store exists.
  UNBLOCKS: the moderated submissions queue + GitHub-issue mirror (rework Q5) — agent-buildable the moment the variable exists.
  VERIFIED-NEEDED: provisioning creates a paid resource in your Railway account and D-0005 forbids agent-initiated Railway mutations without your explicit go — policy wall, deliberately not attempted; no DATABASE_URL exists on the service today.
  ⚑ OWNER-ACTION
  WHAT: Mint a durable fine-grained GitHub PAT and set it on the control-plane service (and optionally as a repo Actions secret for the review-bake workflow).
  WHERE: github.com → Settings → Developer settings → Fine-grained tokens; then railway.app → superbot-websites → control-plane → Variables.
  HOW: token scoped to menno420 repos, read for contents/actions + actions:write for the CI re-run button; set as GITHUB_TOKEN (exact steps: docs/deployment.md § owner TODO). Optional second paste: repo Settings → Secrets and variables → Actions, for richer review-bake stats on private repos.
  WHY-IT-MATTERS: rate headroom + resilience — the fleet surfaces walk 18 lanes tokenless on the anonymous 60-req/h ceiling; the review site's daily stats bake runs on the repo-scoped Actions token and cannot see private fleet repos (their cards honestly say "no data mirrored yet").
  UNBLOCKS: actions-secrets + auto-merge-allowed cells; /owner re-run CI; 5000 req/h across fleet surfaces; full per-repo stats on the review site's /fleet pages.
  VERIFIED-NEEDED: live board shows "unknown (token lacks admin scope)" / "unknown (needs push-scope token)" cells — the token is owner-held; review-bake's Actions token is repo-scoped by GitHub design.
notes: review-expansion follow-ups filed to docs/ideas/backlog.md (bake-time questions sync from [program-review] issues — buildable-now; owner-gated answer-bot flag). Snapshot-aging banner backlog bullet moved to Built. Standing flags carried: REVIEW-QUEUE ROWS OWED — websites #67, #72, #75, #77 (+#81 confirmed; #86→#141 borderline); manager-side asks unchanged (latency persistence; provenance-token convention to kit lane; lanes.json; meta.md convention). Rails held: forward-only, inbox untouched, one writer per file, trigger untouched, no model IDs in commits/PRs; this heartbeat lands inside PR #141 (a sibling heartbeat racing it needs only a branch update, not a rewrite).
