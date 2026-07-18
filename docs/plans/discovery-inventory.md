# ORDER 016 — cross-repo website-plans discovery inventory

> **Status:** `audit` — completed 2026-07-12. This is the committed discovery
> inventory ORDER 016's done-when requires ("a committed discovery inventory
> lists the website-related plans found across the repos, each important one
> executed or explicitly ledgered with a reason"). Point-in-time snapshot:
> verify dispositions against live source control before reusing.

**What this is.** ORDER 016 (`control/inbox.md`): "find all website related
plans across the multiple repos and execute all the important ones." The build
slices merged across 2026-07-12; this document is the remaining done-when
artifact — the inventory of every website-related plan found, with each
important one either executed or explicitly ledgered (owner-gated /
superseded / deferred) with a reason.

**Sweep date:** 2026-07-12.

**Repos swept (at these exact HEADs):**

| Repo | HEAD at sweep |
| --- | --- |
| menno420/websites | `0101b93` (`0101b9389be1d734020ea492191b95c2057a0459`) |
| menno420/fleet-manager | `8724b29` (`8724b2984ff74c950253e3b43058b0511c350b44`) |
| menno420/substrate-kit | `bf1fc80` (`bf1fc802fb04e2ec4e1f0607cdb0d1f314d7e42d`) |
| menno420/superbot | `85a2ec0` (`85a2ec08da6ffae689078266b51c834468213ef6`) |

**Method:** four parallel read-only sweep workers — websites swept its local
checkout (inbox orders, docs/planning + docs/ideas + docs/owner, all
`.sessions/` idea lines, review data, PR #160's branch and all open PRs); the
three remote repos were swept via the GitHub MCP at pinned HEAD SHAs
(directory browsing + full-text reads of control files, planning/ideas/owner
docs, seat packages) after `add_repo` scope grants. No repo files were
changed by the sweeps. Every finding below carries a `repo/path@sha` citation.

---

## Headline: the important ones — executed or ledgered

This section satisfies the done-when's second clause. Every important plan
found across the four repos, with its disposition and reason:

**EXECUTED**

- **Owner Launch Console + Fleet Arcade** — the websites seat's canonical
  mission ("Control plane — Owner Launch Console + Fleet Arcade. Merge =
  deploy.", superbot/docs/owner/fleet-8seat-structure-2026-07-11.md@85a2ec0;
  ranks 1 and 3 of the next-batch shortlist in
  superbot/docs/planning/fleet-strategy-synthesis-2026-07-11.md@85a2ec0; the
  seat's standing rung-3 ladder in
  fleet-manager/projects/websites/instructions.md@8724b29 line 34). Executed
  as merged slices: /projects dispatch view (#158), arcade slice-1 (#161),
  /queue + /orders + owner-queue filters (ORDER 019, #182/#187/#188), IA v2
  console landing pages, mineverse arcade card flipped honest-LIVE (ORDER
  022 drift fixes). fleet-manager-side ORDERs 019/021/022 (review site,
  /directory web-presence page, arcade + environments deltas) are DONE per
  websites/control/status.md@0101b93 line 6. This remains the seat's
  standing between-orders mission — "executed" here means the ordered slices
  landed, not that the mission is closed.
- **Review-site EAP refresh** — refresh + upgrade the public program-review
  site for the Anthropic review window (data refresh to 07-12, live /ask AI
  assistant, homepage rebuild, accuracy pass). Ordered three ways:
  fleet-manager/control/inbox.md@8724b29 ORDER 019 (lines 724-748), the full
  work order superbot/docs/owner/websites-review-site-order-2026-07-12.md@85a2ec0,
  and websites' own ORDER 017. Executed: the #172/#174/#175/#180/#184 wave;
  ORDER 017 DONE per websites/control/status.md@0101b93.
- **Prompt library + website-as-paste-source** — /prompts renders all 26
  fleet paste artifacts live from fleet-manager; per-seat dispatch screens
  with copy-ready full prompt bodies ("THE WEBSITE BECOMES THE PASTE SOURCE",
  superbot/docs/owner/fleet-rearm-2026-07-12.md@85a2ec0 §4.8; restated in
  superbot/docs/owner/next-session-brief-2026-07-13.md@85a2ec0). Executed:
  ORDERs 014 (#165) + 015 (single Prompts home, #192), /projects/{package}
  dispatch view (#158) — both DONE per websites/control/status.md@0101b93.

**PARTIAL (built to the gate; remainder ledgered)**

- **Owner writeback (ORDER 020)** — mark-complete / request-assistance /
  notes committed back to the repo from the sites. Filing #183 + build #189
  merged; writeback queues until the owner pastes a fine-grained
  contents:write PAT (websites/docs/owner/OWNER-ACTIONS.md@0101b93). Gate:
  owner PAT, then live writeback verification.
- **Environments hub (ORDER 021)** — all fleet envs, names-never-values,
  create-per-project-group. Hub built and merged (#202/#203, incl. the
  creation manifest). Gate: the owner's Discord-auth DECISION, then the
  Discord gate build at the `app/owner.py` seam
  (websites/control/inbox.md@0101b93 ORDER 021).

**OWNER-GATED (ledgered — cannot proceed without a specific owner action)**

- **/submit Postgres pipeline** — public submissions intake needs the owner
  to provision Railway Postgres + `DATABASE_URL` on the botsite service
  (fleet-manager/docs/owner-queue.md@8724b29 item D#24
  OQ-WEBSITES-RAILWAY-POSTGRES "blocks /submit";
  websites/docs/owner/OWNER-ACTIONS.md@0101b93; lineage from
  superbot/docs/planning/website-two-site-split-plan-2026-06-19.md@85a2ec0).
  Agent-side provisioning is policy-walled.
- **Tester payouts + gated tester-owner queue** — the ORDER 018 tester
  platform is built (paid task catalog, AI exit-review, guided mode, dry-run
  PayPal payout module); going live needs owner PayPal Payouts credentials +
  botsite `SITE_PASSWORD` (websites/docs/owner/OWNER-ACTIONS.md@0101b93;
  ORDER 018 DONE-with-flagged-gates per websites/control/inbox.md@0101b93).
- **Custom domains** for the three sites — open owner decision, deferred to
  cutover (websites/docs/planning/dashboard-botsite-rework-plan-2026-07-09.md@0101b93
  Q6; fleet-manager/docs/findings/retro-synthesis-2026-07-09.md@8724b29 item 16).
- **Live bot-control panel** — dashboard `/admin` is a complete dry-run UX;
  arming it needs exactly: the owner's Q-0004 "where does bot control live"
  answer, a Discord OAuth app, a scoped control-API token + separate armed
  Railway service, and superbot-side implementation of
  `docs/specs/bot-control-api-v1.md`
  (websites/docs/planning/dashboard-bot-management-readiness.md@0101b93).
- **Old-site cutover (superbot dashboard/ + botsite/ retirement)** — Options
  A–D owner decision, part of the "decide ≤2026-07-13" bundle
  (fleet-manager/docs/planning/2026-07-12-repo-consolidation-plan.md@8724b29
  §5e; docs/owner-queue.md@8724b29 lines 706-709). Retiring before the
  decision would strand live services.
- **P6 console move** — relocate the program console off the botsite service
  onto the kit-lab Railway project
  (substrate-kit/docs/planning/kit-lab-founding-plan-2026-07-07.md@bf1fc80
  §7.2 row P6). Explicitly owner-gated on P5 (owner creates the `kit-lab`
  Railway project) plus P11 public flip or P13 read-only PAT
  (substrate-kit/docs/current-state.md@bf1fc80;
  docs/gen2/queue-state.md@bf1fc80 item 12: "nothing an agent can start
  until a token/visibility exists").
- **Games theme/feature selector UI** — websites owns the website-first
  onboarding selector + theme gallery
  (superbot/docs/ideas/games-theme-engine-website-first-2026-07-10.md@85a2ec0;
  fleet-manager/control/inbox.md@8724b29 ORDER 013 mapping). Gated on
  committed theme packs/manifests existing in the game-seat repos (the
  websites selector is the LAST-shippable increment) plus the owner's
  Discord-OAuth flow shaping (Q-0267).
- **Per-value secret reveal (env-visibility slice 3)** — option (B) of
  websites/docs/planning/live-env-visibility-plan-2026-07-11.md@0101b93,
  explicitly owner-gated, NOT built (slices 1–2 shipped).

**SUPERSEDED (ledgered — a later decision replaced the plan)**

- **Superbot-era legacy website plans** — the two-site-split lineage
  (website-two-site-split-plan-2026-06-19.md, the react-SPA migration plan,
  dashboard live-editor plan, developer-dashboard plan, web-tier
  centralization proposal, the Fable design brief, the 07-08
  rebuild-status-site kickoff — all under superbot/docs/planning/@85a2ec0)
  predate the websites repo split. Superseded by: the executed two-site
  split, then the 2026-07-09 websites-repo kickoff
  (superbot/docs/planning/websites-project-kickoff-2026-07-09.md@85a2ec0,
  which itself marks the 07-08 kickoff superseded) and the four live
  websites services that rebuilt those surfaces. What survives of them is
  ledgered above (the /submit + Postgres lineage, the cutover decision, the
  design-system lineage).
- **Owner-gated live answer-bot on the review site** (backlog idea 9,
  websites/docs/ideas/backlog.md@0101b93) — superseded by ORDER 017 B,
  which built the live `/ask` assistant.

**DEFERRED (ledgered — captured, real, not owner-approved or not yet due)**

- **Website suggestion copilot** — AI-assisted suggestion/bug intake
  interviewing the visitor
  (superbot/docs/ideas/website-suggestion-copilot-2026-07-10.md@85a2ec0).
  Owner-raised idea, not ordered; also partially owner-gated (server-side AI
  key + spend cap; rides the /submit Postgres click).
- **dashboard.json feed-contract completion** — contract the remaining
  websites-rendered families family-by-family with websites pinning +
  validating at render time
  (superbot/docs/ideas/pinned-feed-contract-for-dashboard-json-2026-07-09.md@85a2ec0;
  first slice shipped superbot #1920; kit-side doctrine
  substrate-kit/docs/ideas/pinned-feed-contract-doctrine-2026-07-09.md@bf1fc80).
  Superbot-side production work; websites consumes.
- **Design-system lane** — one shared visual kit across websites, bot
  embeds, future apps
  (fleet-manager/docs/ideas/design-system-lane-2026-07-09.md@8724b29) —
  `captured (not approved)`, owner-origin.
- **Backlog ideas** — the ~19 open captured bullets in
  websites/docs/ideas/backlog.md@0101b93 (see the websites section below):
  buildable rung-3 material, deliberately queued rather than executed under
  this order.
- **Websites cutover-comms / rebuild-dashboard role**
  (superbot/docs/ideas/rebuild-websites-cutover-role-2026-07-03.md@85a2ec0)
  — deferred until the superbot-next cutover it serves is real.

---

## websites (self-sweep @ 0101b93)

### Inbox ORDERs (control/inbox.md@0101b93; done-state truth = control/status.md@0101b93 line 13)

| ORDER | Ask (one line) | Done-state |
| --- | --- | --- |
| 001 | deploy-state drift cell on board (GIT_SHA vs live main head) | DONE |
| 002 | /fleet page — one row per fleet lane rendering control/status*.md | DONE |
| 003 | gen-1 self-review retro (docs/retro/self-review-2026-07-09.md) | DONE |
| 004 | backfill `Model:` line on 18 pre-v1.2.0 session cards | DONE |
| 005 | /queue owner to-do aggregator + /environments registry render | DONE |
| 006 | latency PING-ACK | DONE |
| 007 | gen-2 boot + walking skeleton + build ORDER 005 + env-setup.sh | DONE |
| 008 | self-arm 4-hourly wake routine | DONE (trigger later vanished; wake rides coordinator failsafe — OWNER-ACTIONS row E) |
| 009 | fleet-info surfacing wave (/projects, heartbeat freshness, review-queue) | DONE |
| 010 | model-attribution `📊 Model:` standing rule | DONE |
| 011 | 24h self-review section in status | DONE |
| 012 | records reconcile (status/OWNER-ACTIONS vs live, CLAUDE.md re-render) | DONE (PR #160) |
| 013 | CSRF/Origin + rate-limit on app/owner.py POST routes | DONE (#159) |
| 014 | /prompts fleet prompt library | DONE (#165) |
| 015 | consolidate prompt surfaces into one render path | DONE (#192) |
| 016 | find all website-related plans across repos + execute the important ones | IN PROGRESS — build slices merged (#161 #166 #168 #170 wave); this inventory is the remaining done-when artifact |
| 017 | review-site refresh for the Anthropic window (data, /ask, homepage) | DONE (#172/#174/#175/#180/#184) |
| 018 | tester-recruitment platform (catalog, AI exit-review, guided mode) | DONE (#176/#179/#181; payment/fulfillment owner-gated) |
| 019 | owner-queue filters + centralized list filter/sort site-wide | DONE (#182/#187/#188) |
| 020 | owner writeback on the sites → committed to repo | IN PROGRESS — #183/#189 merged; owner contents:write PAT gate |
| 021 | owner environments hub (fleet envs, names-never-values, create flow) | IN PROGRESS — #202/#203 merged; owner Discord-auth decision gate |

Status line 6 additionally records fleet-manager-side ORDERs 019/021/022
(review site, /directory, arcade + environments) as DONE.

### Doc plans + owner actions

| Plan | Source | State | Route |
| --- | --- | --- | --- |
| Live env-variable visibility, gated (/owner/environments) | websites/docs/planning/live-env-visibility-plan-2026-07-11.md@0101b93 | built (slices 1–2) / owner-gated (slice 3) | Slices 1–2 shipped (gated route, names/status view, manage-links; RAILWAY_TOKEN set — OWNER-ACTIONS row L). Slice 3 per-value secret reveal is explicitly owner-gated, not built. |
| Dashboard/botsite rework open questions Q1–Q7 | websites/docs/planning/dashboard-botsite-rework-plan-2026-07-09.md@0101b93 | partial | Sites rebuilt + deployed. Still open: Q4 bot-control location (= Q-0004, THE gate), Q5 submissions Postgres + moderation mirror, Q6 custom domains, Q2 visual-design keep-vs-restyle, old-site cutover — all tracked as OWNER-ACTIONS open rows 1–6. |
| Arm the dry-run /admin into live bot control | websites/docs/planning/dashboard-bot-management-readiness.md@0101b93 | owner-gated | Needs exactly: Q-0004 answer, Discord OAuth app, scoped control-API token + separate armed Railway service, superbot-side build of docs/specs/bot-control-api-v1.md (spec committed here, pinned by dashboard/bot_control_contract.json). |
| gen-2 handover NEXT queue | websites/docs/planning/queue-state-2026-07-09-winddown.md@0101b93 | historical | Exhausted 2026-07-11 — every item shipped (docs/current-state.md §Next steps). |
| current-state "Next steps" residue | websites/docs/current-state.md@0101b93 §Next steps | partial (1 open) | Item 1 = owner call on the control panel (plan Q4); items 2–3 done. §Recently-shipped's "PLANNED (not built yet)" pointer to the env-visibility plan is stale (now mostly built). |
| Ideas backlog — open captured bullets | websites/docs/ideas/backlog.md@0101b93 | deferred (captured) | ~19 open bullets, buildable unless noted: manifest completeness diff; /owner/environments name-drift check; tester-task URL liveness guard; guide-chat transcript as evidence; /prompts pinned-registry drift chip; /fleet coverage-chip rollup; sanitized guilds[] in dashboard.json (superbot-side); bake-time questions sync; live answer-bot (superseded by ORDER 017 /ask); v1.12.0 boot-set-trim hand-merge; kit-version-line test pin; manager asks (lanes.json, low-water heartbeat token, meta.md deployed:-line, pickup-latency + provenance conventions); chain-entry refresh ender; verdict-inheritance guard; clock-freeze port (dormant); AI-question-log harvest; review privacy lint; arcade live-URL drift probe; merge-holds as file-at-HEAD (also docs/ideas/merge-hold-at-head-2026-07-11.md@0101b93). |
| Owner-gated asks (plans waiting on owner) | websites/docs/owner/OWNER-ACTIONS.md@0101b93 | owner-gated | Actions "allow create PRs" toggle (self-updating review-bake loop); Q-0004; Discord OAuth app; scoped control-API token + armed service; botsite DATABASE_URL Postgres (/submit + durable /testing storage); PayPal Payouts creds + botsite SITE_PASSWORD; fine-grained contents:write PAT (ORDER 020); optional PAT-as-Actions-secret for private-repo bake stats. Open decision rows: redeploy-from-browser hook, custom domains, v1-design keep, old-site cutover. |

### Session-card ideas (~40 distinct, deduped; all @0101b93)

Grouped rather than tabulated; `.sessions/` paths cited per group.

- **Built / shipped** (evidence: backlog.md Built/shipped sections +
  current-state): per-repo ?repo= filter + /activity Atom feed
  (2026-07-09-activity-atom-feed.md, -activity-ideas-views.md); honest-red
  own board row (-adopt-substrate-kit.md); deploy-state cell
  (-railway-deploy.md); /fleet lanes from manifest (-order-002-fleet-page.md);
  kit-version rollup (-kit-upgrade-engage.md, -kit-upgrade-v1.6.0.md);
  quality.yml --inbox-base (2026-07-10-kit-upgrade-v1.7.0.md, v1.7.1.md);
  the 2026-07-10/11 wave — nav guard/manifest, contract tests, heartbeat
  tokens rung:/tooling:/landing:, stalled-claim aging, /queue.json,
  own-heartbeat self-check, wait_deploy, cron_slots, review_row_check,
  open_work, pickup rollup, relay doctrine, control-gate tests,
  time-discipline guard, ideas state filter, board chips, snapshot-aging
  banner (2026-07-10-*.md, 2026-07-11-*.md); journal fleet deep-links
  (2026-07-12-journal-guard-fleet.md); /projects role-coverage chips
  (2026-07-12-projects-dispatch-view.md); partial builds: board sites-row
  group (-dashboard-botsite-rework-plan.md), /owner audit-trail panel
  (-owner-area.md).
- **Captured in docs/ideas/backlog.md**: manifest completeness diff
  (2026-07-12-environments-hub-slice2.md); /owner/environments drift check
  (2026-07-12-order-015-owner-environments.md); AI question-log harvest
  (2026-07-12-order-017-ai-assistant.md); review privacy lint
  (2026-07-12-order-017-private-lane-filter.md); guide-chat transcript
  evidence (2026-07-12-order-018-testing-guided-mode-pr3.md); tester-task
  URL liveness (2026-07-12-order-018-testing-platform-pr1.md); arcade
  live-URL drift probe (2026-07-12-order-022-drift-fixes.md); /fleet
  coverage rollup (2026-07-12-projects-role-coverage-chips.md); /prompts
  pinned-registry drift chip (2026-07-12-prompt-library.md).
- **Card-only** (real, uncaptured — candidate grooming material):
  per-command OpenGraph/meta + copy-invocation
  (2026-07-09-botsite-content-depth.md); readiness.json cron poller →
  auto-file issue on red (-control-plane-site.md); "deploy trigger present?"
  companion cell (-dashboard-autodeploy-fix.md); positive env-var allowlist
  guard (-dashboard-stub-denylist.md); public-surface secret-shape leak
  guard (-drop-auth.md); manifest↔live last-seen drift cell
  (-fleet-manifest-live.md); derive expected_required_checks from ruleset
  (-harden-verify.md); committed journal_index.json
  (-journal-search-mobile.md); stale-data amber badge
  (-monitoring-autorefresh.md); time-aware DRIFT alert
  (-order-001-deploy-drift.md); shared/ds/ package + CSS byte-drift guard
  (-rework-botsite.md); repo-wide production-coupling denylist
  (-rework-dashboard.md); board /rate_limit token-health badge
  (-wire-github-token.md); healthcheck auto-files issue
  (2026-07-10-scheduled-healthcheck.md); console-copy drift stamps
  (2026-07-10-routine-prompt-doc.md); route-level clock freeze
  (2026-07-11-test-time-discipline-guard.md); automerge required_context =
  quality (2026-07-11-kit-upgrade-v1.8.0.md); /work.json category rollups
  (2026-07-12-control-plane-ia-v2.md); heartbeat_facts.py + lint_heartbeat.py
  (2026-07-12-coordinator-heartbeat.md, -coordinator-sitting-report.md);
  SAFE review-service Railway id (2026-07-12-environments-hub-slice1.md);
  seat-roster constant dedupe
  (2026-07-12-order-015-consolidate-prompt-surfaces.md); coordinator fan-out
  manifest (2026-07-12-order-017-coordinator.md); shared FINDINGS registry
  (2026-07-12-order-017-homepage.md); evidence-permalink CI verification
  (2026-07-12-order-017-review-data-refresh.md); shared ai_client module
  (2026-07-12-order-018-testing-ai-review-pr2.md); auto-flush queued
  writebacks on token arrival (2026-07-12-order-020-owner-writeback.md);
  reviewed-SHA pin comment on parked PRs (2026-07-12-reviewer-session.md);
  boot-time already-merged pre-check (2026-07-12-session.md).
- **Kit/manager-routed**: dashboard.json pinned feed contract
  (2026-07-09-console-feed-contract.md); ledger-parity sub-check
  (-engage-kit.md); vendored-kit freshness check (-fix-born-red-gate.md);
  gate-tightening grandfather step (-project-self-review.md); bootstrap
  queue verb (-winddown-queue-state.md); sanctioned non-home citation form
  (-winddown-succession-docs.md); kit adopt-seed / SKILLS orphan warn /
  upgrade-report carve-outs (2026-07-12-kit-upgrade-v1.14.0.md,
  -kit-v1130-upgrade.md, -kit-upgrade-v1.15.0.md).

### PR #160 (the "016 reserved" thread)

PR #160 is **merged** (2026-07-12T15:20:51Z, branch
`claude/order-012-records-reconcile`, head `16ea30d`, 10 files). It is the
ORDER 012 records-reconcile PR that **landed the ORDER 016 text into
control/inbox.md** (renumbered 014→015→016 en route) — "016 reserved by PR
#160's branch" meant the order *number* was minted there. **No plans
inventory or plan documents exist on that branch** (files: control/inbox.md,
control/status.md, .claude/CLAUDE.md, .substrate/state.json, four re-rendered
docs, CAPABILITIES.md, OWNER-ACTIONS.md). Citations:
websites/control/inbox.md@16ea30d, websites/control/status.md@16ea30d. The
only other open PR at sweep time is #209 — this inventory's own PR.

---

## fleet-manager (@ 8724b29)

| Plan | Source | State | Route |
| --- | --- | --- | --- |
| ORDER 019 — review-site refresh for the Anthropic EAP window (data to 07-12, live /ask, homepage rebuild, accuracy) | fleet-manager/control/inbox.md@8724b29 (lines 724-748) | built | Executed as websites ORDER 017 (#172/#174/#175/#180/#184); websites heartbeat reports done=…019 fm-side. Full work-order body: superbot docs/owner/websites-review-site-order-2026-07-12.md. |
| ORDER 021 — web-presence /directory page from a committed registry | fleet-manager/control/inbox.md@8724b29 (lines 772-802) | built | /directory shipped on control-plane; fm ORDER 021 DONE per websites/control/status.md@0101b93 line 6. |
| ORDER 022 — arcade LIVE flip, /owner/environments Railway verify, bake-bridge, ledger reconcile | fleet-manager/control/inbox.md@8724b29 (lines 804-863) | built | Items 1/2/4 executed (websites ORDER 022 drift-fixes session); item 3 amended OBSOLETE in the inbox itself (owner clicked the Actions toggles; bake run 29202721928 SUCCESS). Fence honored: review-production-f027 not moved during the EAP window. |
| Websites cutover Options A–D (retire superbot dashboard/ + botsite/) | fleet-manager/docs/planning/2026-07-12-repo-consolidation-plan.md@8724b29 (§5e); docs/owner-queue.md@8724b29 (706-709); docs/proposals/2026-07-12-consolidation-and-reset-plan.md@8724b29 | owner-gated | "Decide ≤2026-07-13, one sitting" bundle; retiring before the decision strands live services. Websites itself = KEEP ("live product, 3 Railway services deploy-verified daily"). |
| ORDER P1-1 — rehome product-forge games-web into the websites arcade (or superbot-games) | fleet-manager/docs/planning/2026-07-12-repo-consolidation-plan.md@8724b29 (100-112) | owner-gated | Gated on owner approving the consolidation plan; executing agent checks the arcade catalog (websites 06409f5 slice) first and records the call in the PR body. |
| Cron trim — auto-merge-enabler.yml 48 runs/day → event-driven | fleet-manager/docs/owner-queue.md@8724b29 (item 48, OQ-WEBSITES-FM-CRON-TRIM) | owner-gated | Awaiting a one-word owner answer ("websites/fm crons: A" recommended); agent-side workflow edit after. |
| OQ-RAILWAY-PROJECT-SPLIT — consolidate duplicated Railway projects (reliable-grace vs superbot-websites) | fleet-manager/docs/owner-queue.md@8724b29 (item F#39) | owner-gated (frozen) | Recommendation: FREEZE until the 2026-07-14 EAP window closes — the Anthropic email links reliable-grace URLs. |
| OQ-WEBSITES-RAILWAY-POSTGRES — DATABASE_URL for /submit | fleet-manager/docs/owner-queue.md@8724b29 (item D#24) | owner-gated | Owner provisions Railway Postgres; agent-side is policy-walled. Repeated in launch-readiness §7 + retro-synthesis. |
| OQ-WEBSITES-PAT — control-plane GITHUB_TOKEN | fleet-manager/docs/owner-queue.md@8724b29 (item D#25) | owner-gated | Owner creates fine-grained PAT (lifts anonymous 60 req/h; lights admin cells + /owner re-run). |
| OQ-WEBSITES-STALE-BRANCHES — delete 4 stale branches | fleet-manager/docs/owner-queue.md@8724b29 (item B#11) | owner-gated | Agent branch-delete is a verified 403. Nuance (launch-readiness 405-411): claude/rework-dashboard tip = closed-unmerged PR #9 hardening ("small real loss if not re-landed" — 2-min re-check first); claude/harden-verify has post-merge commits. |
| Restructure paste debts — coordinator-prompt v3 into the trigger; instructions v2 into the Project | fleet-manager/docs/owner-queue.md@8724b29 (262-276, 479-480, 562-565); projects/README.md@8724b29 | owner-gated | Owed owner pastes (OQ-RESTRUCTURE-*); websites keeps its cron (only fresh-session-per-fire lane), explicitly NO trigger cutover. |
| Websites seat standing ladder — launch-console + arcade slices between orders | fleet-manager/projects/websites/instructions.md@8724b29 (line 34) | built (standing) | Binding seat instruction; the mission the executed slices serve. Deployed text is v2-stale — re-paste owed (above). |
| Seat-package drift fixes — work-loop fix port, dual setup-script retirement, commit deployed trigger prompt, optional cron retune | fleet-manager/projects/websites/meta.md@8724b29 (58-70) | deferred | Open lane follow-ups ("known drift this package fixes/flags"); item 4 flags the proposals-file "PROPOSED" badge as stale. |
| Fleet-triage verdict — websites KEEP; "merge #141 + create the review Railway service" | fleet-manager/docs/fleet-triage.md@8724b29 (39, 77) | historical | Both actions since done (review service live at review-production-fc91). |
| Launch-readiness §7 — BLOCKED-ON-3 owner clicks; agent-doable kit upgrade + branch disposition | fleet-manager/docs/launch-readiness-2026-07-10.md@8724b29 (383-411) | historical / partial | 07-10 snapshot; kit upgrade long since done (v1.15.0); the 3 owner clicks live on in OWNER-ACTIONS/owner-queue rows above. Also floats websites as alternate flagship lane (366-376). |
| Gen-1 retro product-decision backlog (items 16-22: domains, Postgres, bot-control + OAuth, design keep, cutover, redeploy hook, public bot-health URL) | fleet-manager/docs/findings/retro-synthesis-2026-07-09.md@8724b29 (137-186, 783-789) | owner-gated | Click-level owner list, mostly still open; OAuth half partially resolved 2026-07-12 (dashboard Discord app reused, one redirect click remains — owner-queue 341-353). |
| Games-program mapping — websites owns the theme/feature selector UI + gallery | fleet-manager/control/inbox.md@8724b29 (ORDER 013, 326-374) | owner-gated / deferred | ORDER 013 (the mapping) DONE; the selector build is dependency-gated on committed themes; websites raw-fetches theme schema + themes/*.yaml. |
| Design-system lane — shared visual kit fleet-wide | fleet-manager/docs/ideas/design-system-lane-2026-07-09.md@8724b29 | deferred | `state: captured`, owner-origin, "captured (not approved)". |
| Expected "websites suggestions ORDER" from owner site-testing | fleet-manager/docs/dispatch-log.md@8724b29 (228-229) | historical | Anticipated 2026-07-10; plausibly materialized as ORDERs 019/021/022. |
| Seat instruction proposal (standing default: queue-state NEXT, deploy health, ideas grooming) | fleet-manager/docs/proposals/instructions/websites.md@8724b29 (38-60, 155-183) | historical | Badge "PROPOSED" but deployed 2026-07-10 (badge flagged stale by projects/websites/meta.md); superseded in practice by instructions v2. |
| Review-queue drainer (fleet-wide post-merge review owner) | fleet-manager/docs/ideas/review-queue-drainer-2026-07-10.md@8724b29 | deferred | Captured (not approved); motivated by websites' ORDER 005 acked-but-unexecuted lesson. |

---

## substrate-kit (@ bf1fc80)

| Plan | Source | State | Route |
| --- | --- | --- | --- |
| P6 console move — /console + ds/ + console.json producer off botsite onto kit-lab | substrate-kit/docs/planning/kit-lab-founding-plan-2026-07-07.md@bf1fc80 (§7.1-7.3, §10 KL-6) | owner-gated | Blocked on P5 (owner creates the kit-lab Railway project) + P11 public flip or P13 read-only PAT; confirmed in docs/current-state.md@bf1fc80 (owner gate 5) and docs/gen2/queue-state.md@bf1fc80 item 12 ("nothing an agent can start until a token/visibility exists"). §7.3's console-lane fills (model-spend lane, kit-benchmarks lane, B4 outcome fields) ride the same gate. |
| Websites data-plane migration (Phase 4, superbot-independence sketch) — move exporters + JSON home per P6 | substrate-kit/docs/reports/2026-07-09-fleet-adoption-review.md@bf1fc80 (§3.4, §3.2) | deferred | Marked "direction-setting; NOT this-session work"; until the live bot is replaced, superbot legitimately keeps producing the data rows. |
| Kit-version / readiness cell on the websites board | substrate-kit/docs/ideas/control-board-kit-readiness-cell-2026-07-09.md@bf1fc80 | built | `state: captured, outcome: open` kit-side, but the websites half shipped — /fleet renders the kit: heartbeat rollup (websites current-state). Kit half (the `kit:` line) shipped with kit ORDER 003. The kit's open-outcome row is bookkeeping lag, not missing work. |
| Grounded-skills slice 7 — /journal/{repo}/file guard widening | substrate-kit/docs/planning/2026-07-12-grounded-skills-program.md@bf1fc80 (§7, §3.3) | built | SHIPPED as websites #177 (merge d4a7389; JOURNAL_RENDER_REPOS allow-set, 18 lanes) per docs/reports/2026-07-12-grounded-skills-wrap.md@bf1fc80 §1; the GITHUB_TOKEN gate it named is RESOLVED (wrap §3b). |
| v1.15.0 lane-owed items — merge 5 diverged planted docs; hand-adopt the CAPABILITIES fence seed; Q-0270 boot-triad collapse note | substrate-kit/docs/reports/2026-07-12-grounded-skills-wrap.md@bf1fc80 (§3a; websites upgrade-report @ #199/43988f4) | deferred | Lane-owed post-upgrade housekeeping; contained, rung-5 material for a future websites session. |
| Websites seat-digest onboarding (seat_digest_sync.py --sync) | substrate-kit/docs/reports/2026-07-12-grounded-skills-wrap.md@bf1fc80 (§3b) | deferred | "Unblocked, not done" (kit #298 wave-A landed); part of the slice-6 single-source seat-digest render; the UNIVERSAL wake fetch-list vN bump rides the kit's ⚑ FOR OWNER list. |
| Review-bake PAT side-note | substrate-kit/docs/reports/2026-07-12-grounded-skills-wrap.md@bf1fc80 (§3b) | owner-gated (optional) | "Optional, non-blocking"; the substantive ask lives in websites/docs/owner/OWNER-ACTIONS.md (lines 50-56). |
| Exact-model-ID historical-cards census (websites-#178-style cleanup fleet-wide) | substrate-kit/docs/reports/2026-07-12-grounded-skills-wrap.md@bf1fc80 (§3c) | deferred | Card-only backlog candidate, not filed in docs/ideas/; report-only surface for a one-time owner decision. |
| Fleet-adoption-review websites residuals — friction-outbox envelope verify; owner glance at Settings→Rules for required `quality` | substrate-kit/docs/reports/2026-07-09-fleet-adoption-review.md@bf1fc80 (§1.4, §4, §5 item 5) | historical / built | 07-09 snapshot; gaps 1-4 covered by websites #31; the required-check confirmation has since been verified live websites-side (current-state: "quality is now a REQUIRED status check", verified on PR #18). |
| Route the websites ORDER 005 fleet relay | substrate-kit/docs/current-state.md@bf1fc80 (#75 row) + docs/gen2/next-boot.md@bf1fc80 (§1 item 4) | historical | 2026-07-10-era relay flag; ORDER 005 has long been DONE websites-side (PR #53) — the kit repo simply does not record closure. |
| Pinned feed-contract doctrine for the superbot→websites JSON seam | substrate-kit/docs/ideas/pinned-feed-contract-doctrine-2026-07-09.md@bf1fc80 | deferred | `captured/open` kit-side doctrine; pattern proven end-to-end (superbot #1884 + websites #11). Possible later: template contract file + parity-test scaffold. |
| (websites-origin, kit-scoped) staged-artifact regen-lag checker; _MODEL_DOCTRINE_PHRASE emphasis-blind fix | substrate-kit/docs/ideas/staged-artifact-regen-lag-checker-2026-07-12.md@bf1fc80; model-doctrine-emphasis-blind-phrase-2026-07-11.md@bf1fc80 | deferred | Both propose kit-engine changes, not websites work; listed for completeness. |
| (data point) adopters.md DRIFT row — websites self-reports kit v1.14.0 vs tree v1.15.0 | substrate-kit/docs/adopters.md@bf1fc80 | absent (bookkeeping) | Fix = websites updates its own `kit:` heartbeat line on its next status overwrite. |

---

## superbot (@ 85a2ec0)

| Plan | Source | State | Route |
| --- | --- | --- | --- |
| Review-site refresh work order (workstreams A-D: data, AI widget, homepage, accuracy) | superbot/docs/owner/websites-review-site-order-2026-07-12.md@85a2ec0 | built | Executed as websites ORDER 017 (PRs #175 data, #174 AI, #172 control + the rest of the wave); ANTHROPIC_API_KEY owner click since done (OWNER-ACTIONS row K). Time-box honored (EAP window to 07-14). |
| Fleet-rearm §4.8 websites night dispatch — prompt library as paste source, fleet-freshness page, product pages, merge greens, cold-browser EAP pass | superbot/docs/owner/fleet-rearm-2026-07-12.md@85a2ec0 (§4.8) | built / partial | Paste-source prompt library shipped (ORDERs 014/015 + /projects/{package}); repo-state freshness surfaces exist as /fleet + /orders + /activity; per-product venture-lab pages + the deployed-vs-canonical drift row remain seat-ladder material (deferred, standing mission). |
| 07-13 reboot brief — v3.4 prompt bodies served from the website; #194 merge-on-green; #163 leave draft; final cold-browser pass | superbot/docs/owner/next-session-brief-2026-07-13.md@85a2ec0 | partial | The paste-source surface is live; the v3.4-specific serving + the owner click-procedure are the 07-13 sitting's work (deferred to it). Review site "refreshed and AI-armed (ORDER 019 done)" per the brief itself. |
| Websites Project founding kickoff — kit adoption, control-plane site, deferred dashboard/botsite rework | superbot/docs/planning/websites-project-kickoff-2026-07-09.md@85a2ec0 | built | Fully executed: kit adopted (#1), control-plane built (#2), rework done after check-in (#7/#8). Supersedes the 07-08 rebuild-status-site kickoff. |
| Owner Launch Console (rank 1, home = websites + fleet-manager) | superbot/docs/planning/fleet-strategy-synthesis-2026-07-11.md@85a2ec0 | built (standing) | Executed as the /queue + /orders + /projects dispatch-view + owner-writeback slices; extends existing surfaces per the plan's own framing. Lower-priority incubations (Repo Truth Audit, Theme Studio, Server Blueprint Packs, cross-game achievements) = deferred. |
| Fleet Arcade / Play Portal (rank 3) | superbot/docs/planning/fleet-strategy-synthesis-2026-07-11.md@85a2ec0; fleet-consolidation-and-next-round-2026-07-11.md@85a2ec0; docs/owner/next-round-founding-prompts-2026-07-11.md@85a2ec0 | built (standing) | /arcade shipped (#161 slice-1; mineverse flipped honest-LIVE via ORDER 022); catalog growth (Lumen Drift, games-web rehoming = fm ORDER P1-1) continues on the seat ladder / owner approval. |
| Websites = seat 8 mission line | superbot/docs/owner/fleet-8seat-structure-2026-07-11.md@85a2ec0 | built (standing) | "Control plane — Owner Launch Console + Fleet Arcade. Merge = deploy." — the canonical mission the re-arm pack repeats; not a closeable item. |
| Website suggestion copilot (AI suggestion/bug intake) | superbot/docs/ideas/website-suggestion-copilot-2026-07-10.md@85a2ec0 | deferred | Owner-raised idea, not ordered; routes via manager ORDER once the idea-probe battery exists; also rides the /submit Postgres owner click + an AI key/spend-cap decision. |
| Website-first game provisioning — selector UI + theme gallery | superbot/docs/ideas/games-theme-engine-website-first-2026-07-10.md@85a2ec0 | owner-gated / deferred | Owner-shaped (Q-0267); websites owns the selector UI + gallery, games seats own the manifests; dependency-gated on committed theme packs; phase-1 signed "setup code" shortcut named. |
| Pin dashboard.json feed contract family-by-family; websites validates at render time | superbot/docs/ideas/pinned-feed-contract-for-dashboard-json-2026-07-09.md@85a2ec0 | partial / deferred | First slice SHIPPED (superbot #1920, families meta + bugs; websites pins + validates console.json per websites #11). Remaining families = superbot-side production work, deferred. |
| Websites cutover-comms + rebuild-dashboard role; repoint export producer at superbot-next | superbot/docs/ideas/rebuild-websites-cutover-role-2026-07-03.md@85a2ec0 | deferred | Open forks (interim producer old/new/both, cadence, scope) wait on the superbot-next cutover being real. |
| Program design system + botsite v2 + console shell (Fable design brief) | superbot/docs/planning/website-design-fable-brief-2026-07-07.md@85a2ec0 | historical / superseded | Largely executed in the superbot era (console shipped, PR #1802); the ds/ design system it produced is the lineage the websites services vendored. |
| Fleet-drive session record — rebase websites #160/#161/#166; owner adds ANTHROPIC_API_KEY; Q-0089 generated OWNER-QUEUE.md | superbot/.sessions/2026-07-12-fleet-drive-and-websites.md@85a2ec0 | historical / built | All three PRs since merged; the API key since set (OWNER-ACTIONS row K); Q-0089 is adjacent to the built /queue surface. Root-cause fix for the stuck merges (require-up-to-date removed) recorded. |
| Dev-site project-status donut + dashboard refocus on projects | superbot/docs/ideas/dev-site-project-status-donut-2026-06-19.md@85a2ec0 | partial / deferred | "Plans & execution at a glance" half shipped as the program console (#1802); remaining tail (per-subsystem/per-cog roll-ups, completion-denominator owner question) deferred. |
| Website two-site split (public bot site vs gated dev dashboard) | superbot/docs/planning/website-two-site-split-plan-2026-06-19.md@85a2ec0 | superseded | Executed in its era (decisions LOCKED 2026-06-19), then superseded by the websites-repo rebuild; survives as the /submit + Postgres lineage and the four-zone IA the current sites inherit. |
| Owner companion clicks — websites DATABASE_URL + control-plane GITHUB_TOKEN | superbot/docs/owner/dispatch-prompts-2026-07-11.md@85a2ec0 (Part A) | owner-gated | Same two clicks ledgered in fm owner-queue D#24/D#25 and websites OWNER-ACTIONS — recognized fleet-wide as blocked-on-owner-env. |
| Roadmap routing (context) — website work routed out of the hub | superbot/docs/roadmap.md@85a2ec0 | historical | Points at website-split-next-steps-2026-06-19.md as handoff; the integrations/media/voice/website roadmap sits in "Someday / Later" gated on a privacy/security/moderation review. |

---

## Negative findings

- **No plans inventory existed anywhere before this document** — none of the
  four repos contained a cross-repo website-plans inventory or anything
  shaped like one.
- **PR #160 minted the ORDER 016 number but carried no inventory** — its 10
  files are the ORDER 012 records reconcile (inbox/status/CLAUDE.md/doc
  re-renders); no plan docs (websites/control/inbox.md@16ea30d).
- **substrate-kit has zero "arcade" content and no literal "launch console"**
  — full-text checks including the 71KB founding plan; console references
  are to the program-console shell on the botsite service.
- **fleet-manager's current-state, seat-digest, decisions, architecture,
  MISSION, README, control/README carry no website plans** (grep-verified);
  merge-queue/evidence-index/handoff/review-queue docs hold only
  status/pointer mentions.
- **superbot's control files carry no website orders** —
  control/inbox.md@85a2ec0 holds only hub ORDERs 001-002; websites orders
  live in the websites repo's own inbox, superbot records them as owner docs.
  Remaining superbot "arcade" code-search hits are the Discord help-overlay
  hub rename + BTD6 data, unrelated.
- **websites' own quiet corners**: docs/owner/owner-notes.md@0101b93 is
  header-only (zero writeback entries yet); review/data/*.md propose no new
  website work beyond the already-tracked PAT ask; the queue-state winddown
  NEXT list is exhausted; all docs/ideas/ standalone files except
  merge-hold-at-head-2026-07-11.md are marked built; the only open PR is
  #209 (this one).

## Not swept (honesty section)

- **fleet-manager**: `.sessions/`, docs/retro/, docs/succession/,
  docs/research/, docs/experiments/, telemetry/, templates/, tools/,
  scripts/, environments/ not swept file-by-file (session logs/machinery;
  environments content reached indirectly via the audit/followups docs);
  docs/prompts/ and other seats' proposals/projects listed only. GitHub code
  search returned 0 results with `incomplete_results: true` (repo likely
  unindexed) — directory browsing + local grep of downloaded files used
  instead.
- **substrate-kit**: CHANGELOG.md (131KB shipped-work log), bench/, src/,
  tests/, `.sessions/` cards, docs/retro/ + docs/succession/ file bodies,
  docs/operations/{README,auto-merge-guards,release-runbook}.md,
  docs/gen2/{README,custom-instructions-proposal,environment-setup,
  feedback-for-gen2-blueprint}.md, control/status-*.md, control/claims/ —
  out of budget, low expected yield. Code search also unindexed
  (0 results, incomplete) — browsing used. The 71KB founding plan exceeded
  the MCP return cap and was recovered from the tool's spill file (read in
  full).
- **superbot**: legacy website-adjacent planning docs LISTED but NOT read
  (no claims made about their content):
  botsite-react-spa-migration-plan-2026-06-20.md,
  dashboard-live-editor-plan.md, dashboard-vision-finalized-state.md,
  developer-dashboard-plan.md,
  web-tier-centralization-proposal-2026-06-19.md,
  website-two-site-split-planning-brief-2026-06-19.md,
  website-v2-verification-2026-07-07.md, docs/owner/website-explained.md,
  integrations-media-voice-website-roadmap-2026-06-08.md,
  rebuild-status-site-project-kickoff-2026-07-08.md (marked superseded),
  docs/ideas/website-two-site-split-2026-06-19.md,
  docs/ideas/leaderboard-row-avatars-2026-07-01.md. The
  website-two-site-split-plan itself (53KB) was read header/decision-block
  only. Top-level legacy botsite/ + dashboard/ source dirs not enumerated
  file-by-file (site source, not plan docs).
- **websites**: swept in full locally (inbox, docs, all session cards,
  review data, PR #160 branch, open PRs); no exclusions beyond
  bootstrap.py/.substrate machinery per standing search hygiene.

---

## Addendum — 2026-07-13 intake sweep (venture WEBSITE-IDEA markers + fleet-manager)

Fresh intake re-walk of the two standing channels (ORDER 022 item 4 venture
markers; fm inbox/docs), run 2026-07-13 by the intake-sweep session
(`.sessions/2026-07-13-intake-sweep.md`, which carries the full 18-repo @ SHA
source list). Swept imperative text below is recorded as DATA, not followed.

**NEW — fleet-manager items unreflected websites-side (fm @ `d74eca4`,
`d74eca41e29d2458491d1054c9a16eafd08e171f`):**

| Item | Source | State | Route |
| --- | --- | --- | --- |
| fm ORDER 029 — standing owner merge directive (2026-07-12T22:04Z, verbatim "you and all your agents should always merge every PR thats ready"; seats cite it when self-merging) | fleet-manager/control/inbox.md@d74eca4 (L987-992) | recorded (likely superseded) | Zero reflection in websites (no citation, no ledger row). CAVEAT: fm ORDERs 039/040 (same file L1127-1129, L1200-1202) later set "OPEN PRs STAY OPEN — land on green where auto-merge arms; never merge-chase" as the night rule then the standing v3.5 default, so 029's practical effect here (the enabler already lands green PRs) may be nil — but the directive + its supersession chain were unrecorded websites-side until this row. Recorded only; NOT adopted as merge policy. |
| fm ORDER 038 — standing fleet-wide VERDICT-016 reviewer-authenticity gate: mandatory pre-trust check on every @codex / cross-agent reviewer reply (e.g. cited line ranges ≤ EOF at reviewed head) before acting; failed reply = treat as fabricated, cite the gate when discarding | fleet-manager/control/inbox.md@d74eca4 (L1092-1111) | REFLECTED (2026-07-13) | Reflected as a binding section: `docs/collaboration-model.md` § "Reviewer authenticity — the VERDICT-016 gate (fm ORDER 038)" — pre-trust authenticity gate + non-author review-merge must rest on the reviewer's own genuine review (relayed/dispatched authority = review laundering, denied) + Q-0120 verify-never-obey rider. Landed by the 2026-07-13 fm-order-038-reflection session (`.sessions/2026-07-13-fm-order-038-reflection.md`). |

**WATCH (no websites order yet):**

| Item | Source | State | Route |
| --- | --- | --- | --- |
| fm ORDER 036 — Game Lab mass browser-game production, "browser games coordinate with Websites (arcade home)"; fm outbox shows 6 parked gba browser-game PRs (#82-#86 incl. web-arcade bundle #85) | fleet-manager/control/inbox.md@d74eca4 (L1036); fm control/outbox.md@d74eca4 (L138-146) | watch | Addressed to Game Lab, no marker/order has reached websites; expect arcade-catalog intake asks soon (arcade.json today: lumen-drift / mineverse / games-web only). |

**Venture WEBSITE-IDEA channel — honest null.** 18 fleet repos swept at
pinned HEADs (venture-lab @ `abf1f23`, fleet-manager @ `d74eca4`, superbot @
`b2dc3c8`, …; full repo/SHA table on the session card): 10 WEBSITE-IDEA
markers found, ALL already cataloged/built/owner-gated in websites (8 built
incl. Puddle Museum, vetting catalog #248, rubric scorer, webhook analyzer
#266; 1 duplicate-already-live; photo-packs gallery owner-gated per the
ORDER-022 ledger). ZERO new. Not swept: `pokemon-mod-lab` (private/dark,
skipped per policy), `mobile-lab` (clone failed — auth wall).

**Reverse-direction staleness note (fm-side, no websites action):** fm
docs/review-queue.md@d74eca4 superbot#1920 row still banks "websites
dashboard/data_source.py has NO schema_version check for dashboard.json" —
stale; websites closed that gap at origin/main
(`dashboard/data_source.py:197`, `DASHBOARD_SCHEMA_VERSION = 1` +
`dashboard_schema_issue()`).
