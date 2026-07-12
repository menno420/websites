# Owner actions — decisions & actions waiting on you

> **Status:** `owner-guidance`
>
> A single **living** list of decisions/actions that only the owner can make,
> and the ones already made. Future sessions keep this current: when the owner
> decides one, move it to **Decided** with the decision + provenance; when a new
> owner-gated fork appears, add it to **Open**. Skimmable by design.

## 🟡 Open — waiting on the owner

| # | Decision | What it unblocks | Notes / where it lives |
|---|---|---|---|
| 1 | **Dashboard `/admin` live-bot control** — arm a production control path, or keep it dry-run? | The Discord-OAuth panel that writes the live bot's control API (settings / help / cog routing / submission moderation). | Needs your direct word. As of 2026-07-11 `/admin` is a complete **dry-run** management UX (typed previews + in-memory audit; zero control-API credentials present — `docs/planning/dashboard-bot-management-readiness.md`). Arming = a **separate** service (OAuth app + control-API token, spec `docs/specs/bot-control-api-v1.md`) + deciding *where bot control lives* (websites / superbot / superbot-next). Rework-plan **Q4** / **Q-0004** (`docs/question-router.md`); three ⚑ asks below. |
| 2 | **Botsite `/submit`** — provision a submissions Postgres + moderation mirror, or keep the stub? | The public feature/bug intake pipeline (moderated queue → GitHub-issue mirror). | Stub today: `botsite/templates/submit.html` (now shows a "Stub — not wired" badge). Needs a Postgres + mirror PAT. Rework-plan **Q5**. |
| 3 | **Redeploy-from-browser scoped deploy hook** — yes / no? | A gated `/owner` button that triggers a Railway redeploy of a websites service from the site itself. | Would require a Railway deploy hook (scoped to `superbot-websites` only — never the ambient production IDs, see `docs/RAILWAY-SAFETY.md`). Currently deploy = merge to `main` (auto). |
| 4 | **Custom domains** for the three sites (control-plane / botsite / dashboard). | Friendly URLs instead of `*.up.railway.app`. | Deferred to cutover. Rework-plan **Q6**. |
| 5 | **Preserve v1 visual design vs. the shipped restyle** (rework Q2). | Whether the ds/-based restyle stands or the original superbot visual design is carried over. | Rework-plan **Q2** (`docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`). |
| 6 | **OLD-site cutover / retirement in superbot** — go / no-go? | Retiring the `dashboard/` + `botsite/` still living in `menno420/superbot` once these replace them. | Gated: needs your go. Verify the live websites URLs first (`python3 scripts/healthcheck.py`). |

### ⚑ Active six-field asks

> **Re-verified 2026-07-12 (ORDER 012 reconcile, main @ b925072):** every
> ask below was re-checked against live state and REMAINS OPEN — review
> Railway service: the live deploy board still tracks exactly three
> services (control-plane/botsite/dashboard, all `in_sync` at
> `b9250728`; no review row); Q-0004: `docs/question-router.md`
> "Maintainer answer: (unanswered)"; Discord OAuth + armed service:
> both gated on Q-0004, no OAuth app or fourth-write-service evidence
> exists; botsite DATABASE_URL: `/submit` still the labeled stub, the
> Railway-mutation policy wall stands (`docs/RAILWAY-SAFETY.md`).

```markdown
⚑ OWNER-ACTION
WHAT: Create the fourth Railway service so the new program-review site (built for Anthropic reviewers) goes live.
WHERE: railway.app → project superbot-websites → New → Service → GitHub repo menno420/websites.
HOW: set Root Directory = review (the service's own Dockerfile at review/Dockerfile is picked up automatically, exactly like botsite/dashboard); branch = main; no environment variables needed (the service is read-only and network-free). After the first deploy, check <service-url>/healthz returns {"status":"ok"} and /version shows the deployed sha.
WHY-IT-MATTERS: the review site — process, growth charts, successes, an honest problems page, and (since the 2026-07-11 expansion) the fleet index, continuous review editions with a subscribable Atom feed, and the evidence-backed questionnaire — exists on main but has no URL until the service exists.
UNBLOCKS: a shareable live URL for Anthropic reviewers (including /reviews/feed.xml they can subscribe to); the board's deploy-drift row and scripts/healthcheck.py can then also add the fourth service. The scheduled review-bake workflow already refreshes the site's committed data daily, so the service goes live self-updating.
VERIFIED-NEEDED: service creation is a Railway account mutation — the Railway-safety policy (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger) forbids agent-initiated Railway mutations without your explicit go, so this was deliberately not attempted (the same policy wall as the Postgres ask; no new attempt/error needed).
```

**PAT side-note (updated 2026-07-12 — the control-plane GITHUB_TOKEN ask
itself is RESOLVED, Decided row H):** the remaining optional payoff is a
PAT with private-repo read set as a **websites repo Actions secret** for
the `review-bake` workflow — `review/gen_stats.py` runs on the ambient
Actions token (fine for public repos: "17/18 repos with live stats" in
run 29184552812) and cannot see private fleet repos, whose fleet cards
honestly say "no data mirrored yet". Optional, not blocking.

```markdown
⚑ OWNER-ACTION
WHAT: Answer Q-0004 — decide WHERE live bot control lives (websites / superbot / superbot-next), or explicitly keep the dashboard's control panel dry-run-only.
WHERE: docs/question-router.md (Q-0004, open + blocking) — reply in chat or edit the "Maintainer answer" slot; the dry-run panel to judge from is live at the dashboard's /admin.
HOW: one sentence is enough ("carry it into websites as a new service" / "leave it in superbot" / "superbot-next" / "stay dry-run"). Everything downstream (OAuth app, token, armed service) hangs off this answer.
WHY-IT-MATTERS: this is THE gate — it decides whether a bot control-API credential ever enters a websites service. The 2026-07-11 bot-management build took /admin as far as it can go without it: the complete management UX now runs as an honest dry-run (docs/planning/dashboard-bot-management-readiness.md).
UNBLOCKS: the two asks below, plus the superbot-side v1 implementation of docs/specs/bot-control-api-v1.md.
VERIFIED-NEEDED: a product/topology decision only you can make (docs/question-router.md marks it product-intent · blocking · open; ORDER 001 explicitly parked it as non-agent-executable) — no agent attempt applies.
```

```markdown
⚑ OWNER-ACTION
WHAT: Create the Discord OAuth application for the future ARMED control panel and decide its redirect URI.
WHERE: discord.com/developers/applications → New Application → OAuth2 (do this only after Q-0004 above names where the armed service lives).
HOW: register the app; add redirect URI https://<armed-service-url>/auth/callback (the armed service's real URL once it exists); note the client id + client secret — they go ONLY into the armed service's Railway env (spec §9 names: the OAuth client id/secret + redirect + session-secret vars), NEVER into the dashboard service (a test forbids the literals there).
WHY-IT-MATTERS: actor identity is the safety spine of the control API — every write carries the operator's Discord user id and the bot re-checks their permission per guild; without the OAuth app there is no actor, so no live write path should exist.
UNBLOCKS: real sign-in on the armed panel; until then the dashboard's /admin/login honestly says "not configured" and dry-run actions are attributed to anonymous.
VERIFIED-NEEDED: creating a Discord application requires your Discord developer account — no agent credential exists for it (same class as the Railway-mutation wall; deliberately not attempted).
```

```markdown
⚑ OWNER-ACTION
WHAT: Provision the scoped bot control-API token and the SEPARATE armed Railway service that will hold it.
WHERE: railway.app → project superbot-websites → New → Service (a NEW service, per the standing "never mounted on a read-only surface" rule) + the token minted on the bot side (superbot's control-api seam).
HOW: after Q-0004 and the OAuth app: create the service, set its env per docs/specs/bot-control-api-v1.md §9 (OAuth client id/secret/redirect, session secret, control URL + scoped token). Never reuse the ambient production RAILWAY_*_ID vars (docs/RAILWAY-SAFETY.md); the dashboard service gets NOTHING.
WHY-IT-MATTERS: the credential boundary is the whole design — the public read-only dashboard stays permanently credential-free, so a compromise of it can never reach the live bot; the power lives in one small gated service you provision knowingly.
UNBLOCKS: flipping the specified armed path from spec to service; the dashboard's dry-run flows are the exact UX + request contract it will reuse.
VERIFIED-NEEDED: Railway service creation + secret provisioning are owner account mutations — the Railway-safety policy (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger) forbids agent-initiated Railway mutations without your explicit go (the same policy wall as the review-service ask above; not attempted).
```

(Previous state: none open — the one conditional ask (external wake-trigger
fallback) self-expired 2026-07-10T16:01:32Z: the self-armed routine's first
fire landed; see row E and
`.sessions/2026-07-10-order008-first-fire-manifest-smoke.md`.)

**Historical record (kept verbatim per the capability ledger):** before ORDER
008, the fleet **coordinator's** toolset exposed **no send_later/scheduling
tool at all** — no scheduler primitive of any kind — and its cross-session
probe failed with the exact error: "target session could not be verified;
retry send_message shortly". That coordinator-side wall still stands; ORDER
008's finding is that a **worker session on this surface** does carry a
scheduler primitive (`docs/CAPABILITIES.md` append log, 2026-07-10).

### ⚑ Asks consolidated at project-chat archive (2026-07-11 — see `docs/retro/archive-ready-2026-07-11.md`)

**STRUCK 2026-07-12 (ORDER 012 reconcile — both satisfied, moved to
Decided rows F/G below):** the "squash-merge PR #141" ask (merged by you
2026-07-11T20:24:48Z as squash `0545906`) and the "run review-bake once
manually" ask (you ran it 2026-07-11T20:26:33Z — run `29167034060`,
`event: workflow_dispatch`; it failed on a repo setting, NOT for lack of
the click — the follow-up is the single ask below).

```markdown
⚑ OWNER-ACTION
WHAT: Allow GitHub Actions to create pull requests on menno420/websites, so the daily review-bake can land its data refresh.
WHERE: github.com/menno420/websites → Settings → Actions → General → "Workflow permissions" → check "Allow GitHub Actions to create and approve pull requests" → Save.
HOW: one checkbox + Save. Optionally afterwards: Actions → review-bake → "Run workflow" (branch main) to land the first bake immediately instead of waiting for the daily cron.
WHY-IT-MATTERS: the review-bake workflow has now run TWICE and failed BOTH times at the same wall — run 29167034060 (event: workflow_dispatch, 2026-07-11T20:26:33Z, your manual run) and run 29184552812 (event: schedule, 2026-07-12T07:38:28Z — the daily cron IS firing). Each run baked the data fine (snapshot + fleet + stats: "17/18 repos with live stats"), was correctly ruleset-blocked from pushing to main, pushed its fallback branch, then died at `gh pr create` with: "GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)". Until the toggle flips, every daily bake fails and review/data/stats.json stays absent from main.
UNBLOCKS: the self-updating review-site data loop (snapshot/fleet/stats refreshed daily via [bake] PRs that auto-merge on green); also makes the two orphan branches the failed runs pushed (bake/review-data-20260711-202653, bake/review-data-20260712-073843 — stale, safe to delete) stop accumulating.
VERIFIED-NEEDED: the "Allow GitHub Actions to create and approve pull requests" setting is repo-console-only (Settings → Actions), owner-held; agents hold no path to it. Failure verified by event type from both runs' logs 2026-07-12 (ORDER 012); exact error string quoted above.
```

```markdown
⚑ OWNER-ACTION
WHAT: Create the botsite submissions PostgreSQL database and give the botsite service its connection string.
WHERE: railway.app → project superbot-websites → New → Database → PostgreSQL; then service botsite → Variables.
HOW: add variable DATABASE_URL = the connection string Railway shows for the new Postgres. One paste.
WHY-IT-MATTERS: the public /submit intake (feature/bug submissions with a moderated queue) stays a labeled stub until the database exists.
UNBLOCKS: the submissions pipeline (rework Q5 — Open row 2 above); the moderation → GitHub-issue mirror is the follow-up build once data can persist.
VERIFIED-NEEDED: Railway mutations are policy-walled for agents (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger — deliberately not attempted; same wall as the review-service ask). Click steps first recorded in `docs/retro/self-review-2026-07-11.md` §2.
```

**STRUCK 2026-07-12 (ORDER 012 reconcile — SATISFIED, moved to Decided
row H below):** the "mint a GITHUB_TOKEN for the control-plane service"
ask. Live verification 2026-07-12: `/api/readiness.json` now returns
authenticated-only cells — Actions-secret counts read `status 200,
known: true` across repos (e.g. superbot "5 secret(s)"; anonymous callers
cannot list Actions secrets at all) and `auto_merge.allowed` is known —
so a working token IS set on the live control-plane. Residual option
(NOT re-filed as an ask): adding a PAT as a **websites repo Actions
secret** would let the review-bake see private fleet repos too (today it
runs on the ambient Actions token and still reached "17/18 repos with
live stats" — run 29184552812 log); websites' own Actions-secret count
is 0 at last check.

## 🟢 Decided / resolved

| # | Item | Decision | Provenance |
|---|---|---|---|
| A | **Required `quality` CI check on `main`** | **Owner set the ruleset** — `quality` is now a REQUIRED status check; PRs blocked until green. | Owner-configured ruleset 2026-07-09; verified live (PR #18 `mergeable_state=blocked` while `quality` pended). Board row shows `quality` configured + expected. |
| B | **Basic-auth gate on control-plane + dashboard** | **Dropped** — both sites are fully public; the readiness board masks Actions-secret names to a count. | Owner verbatim "Yes drop the auth"; decision stamped in `docs/decisions.md`. |
| C | **superbot kickoff doc (was PR #1876) → README link** | **Resolved** — the doc is merged on superbot `main`; the README link now returns HTTP 200 (verified 2026-07-09). Was a 404 while the PR was unmerged. | `README.md` → `superbot/docs/planning/websites-project-kickoff-2026-07-09.md`. |
| D | **Leaky born-red session gate** (PR #19 auto-merged empty on an `in-progress` card) | **Resolved — no owner action** — adopted upstream kit **v1.0.0** `bootstrap.py` (fails born-red cards under `--strict`) + folded diff-aware `--session-log` into the `quality` gate. Both directions proven + regression-tested. Upstream substrate-kit repo fix handled by a **separate** session. | Decision stamped in `docs/decisions.md` (born-red-gate entry); `.github/workflows/quality.yml`; `tests/test_born_red_session_gate.py`. |
| E | **Lane wake routine** (was Open row 7 — external owner-armed trigger) | **Self-armed and CONFIRMED working — no owner click needed.** Fleet ORDER 008 (2026-07-10) verified sessions can create routines; this lane armed trigger `trig_017H9Qb9oxtLgUy6sw2gnSHg` (cron `0 */4 * * *`, fresh-session-per-fire, prompt = the standing inbox ritual). First fire confirmed 2026-07-10T16:01:32Z (`list_triggers` `last_fired_at`; this session is that fire) — the conditional fallback ask has been withdrawn. **Ground-truth update 2026-07-12 (ORDER 012):** that trigger NO LONGER EXISTS live — an exhaustive `list_triggers` sweep (823 triggers, full account history back to 2026-06-12) does not contain `trig_017H9Qb9oxtLgUy6sw2gnSHg`; not deleted by this lane (already absent). The lane's wake now rides the coordinator-session failsafe `trig_01Aak59jvQQdimDgy5K1yAGQ` (cron `45 */2 * * *`) — see `control/status.md` ROUTINE. | `control/inbox.md` ORDER 008; claim PR #56; `docs/CAPABILITIES.md` append log 2026-07-10; `.sessions/2026-07-10-order008-first-fire-manifest-smoke.md`; `control/status.md`. |
| F | **PR #141 squash-merge** (was the archive-consolidated merge-click ask) | **DONE by owner** — merged 2026-07-11T20:24:48Z (`merged_by: menno420`, squash commit `0545906`); the review/ expansion is on main. | github.com/menno420/websites/pull/141 (`merged: true`); verified via GitHub API 2026-07-12 (ORDER 012). |
| G | **One manual review-bake dispatch** (was the archive-consolidated run-once ask) | **DONE by owner — but the run failed on a repo setting.** Run `29167034060` (`event: workflow_dispatch`) fired 2026-07-11T20:26:33Z; the first `schedule` fire `29184552812` followed 2026-07-12T07:38:28Z (the cron works). Both failed at `gh pr create`: "GitHub Actions is not permitted to create or approve pull requests". Follow-up = the single toggle ask above. | Both run logs, read 2026-07-12 (ORDER 012); run history: 2 runs total, both failed. |
| H | **Control-plane GITHUB_TOKEN** (was the standing PAT ask) | **DONE by owner** — the live board now returns authenticated-only cells (Actions-secret counts `known: true`, `auto_merge.allowed` known), impossible anonymously; deploy-drift row reads all three services `in_sync`. | Live `/api/readiness.json` verified 2026-07-12 (ORDER 012); wall history in `docs/CAPABILITIES.md` (2026-07-09 entry + 2026-07-12 resolution). |

## How to use this doc

- New owner-gated fork → add a row to **Open** with where it lives.
- Owner decides → move it to **Decided / resolved** with the decision + a
  provenance pointer (a `[D-NNNN]`, a `Q-NNNN`, or a dated verification).
- Keep it short. Detail belongs in the linked decision/plan/router, not here.
