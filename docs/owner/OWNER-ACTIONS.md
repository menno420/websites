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

```markdown
⚑ OWNER-ACTION
WHAT: Create the fourth Railway service so the new program-review site (built for Anthropic reviewers) goes live.
WHERE: railway.app → project superbot-websites → New → Service → GitHub repo menno420/websites.
HOW: set Root Directory = review (the service's own Dockerfile at review/Dockerfile is picked up automatically, exactly like botsite/dashboard); branch = main; no environment variables needed (the service is read-only and network-free). After the first deploy, check <service-url>/healthz returns {"status":"ok"} and /version shows the deployed sha.
WHY-IT-MATTERS: the review site — process, growth charts, successes, an honest problems page, and (since the 2026-07-11 expansion) the fleet index, continuous review editions with a subscribable Atom feed, and the evidence-backed questionnaire — exists on main but has no URL until the service exists.
UNBLOCKS: a shareable live URL for Anthropic reviewers (including /reviews/feed.xml they can subscribe to); the board's deploy-drift row and scripts/healthcheck.py can then also add the fourth service. The scheduled review-bake workflow already refreshes the site's committed data daily, so the service goes live self-updating.
VERIFIED-NEEDED: service creation is a Railway account mutation — the Railway-safety policy (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger) forbids agent-initiated Railway mutations without your explicit go, so this was deliberately not attempted (the same policy wall as the Postgres ask; no new attempt/error needed).
```

**PAT side-note (extends the standing GITHUB_TOKEN ask in
`control/status.md` + `docs/deployment.md`):** a durable fine-grained PAT
would ALSO unlock richer live stats for the review site's daily
`review-bake` workflow — today `review/gen_stats.py` runs on the Actions
token (fine for public repos) and cannot see private fleet repos, whose
fleet cards honestly say "no data mirrored yet"; a PAT with read access to
the private repos, set as a repo Actions secret passed to the bake, would
fill those gaps. Same token errand, one more payoff.

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

```markdown
⚑ OWNER-ACTION
WHAT: Squash-merge PR #141 (the review-site expansion) — the one open PR agents cannot merge for you.
WHERE: github.com/menno420/websites/pull/141.
HOW: click only — if GitHub says the branch is out of date, click "Update branch", wait for the `quality` check to go green (an agent drift-watchdog also keeps re-greening it), then "Squash and merge".
WHY-IT-MATTERS: the review site's whole expansion — fleet coverage, the daily stats bake, continuous review editions + Atom feed, the questionnaire, interaction hooks — is finished and green but invisible until this click.
UNBLOCKS: the full review-site content on main; the review-bake workflow; the ask below.
VERIFIED-NEEDED: agent merge attempts on this PR are platform-denied because its diff adds a workflow file (`.github/workflows/review-bake.yml`) — recorded on the 2026-07-11 heartbeat; you ruled in chat that you personally merge workflow-file PRs (durable record: `docs/retro/archive-ready-2026-07-11.md` §2c).
```

```markdown
⚑ OWNER-ACTION
WHAT: Run the review-bake workflow once, manually, right after merging PR #141.
WHERE: github.com/menno420/websites → Actions → "review-bake" → "Run workflow" (branch: main).
HOW: click only.
WHY-IT-MATTERS: `review/data/stats.json` is deliberately absent until the first successful CI bake — one manual run seeds the live fleet stats immediately instead of waiting for the daily cron, and proves the Action end-to-end while attention is on it.
UNBLOCKS: real fleet/stats data on the review site's pages from day one.
VERIFIED-NEEDED: not an agent wall (agents can trigger workflow_dispatch — `docs/CAPABILITIES.md`) but a sequencing ask: the workflow only exists on main after YOUR merge above, and with the project chat archived no agent session is guaranteed to be running at that moment. Any future session may do this instead — then strike this ask.
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

```markdown
⚑ OWNER-ACTION
WHAT: Mint a durable fine-grained GitHub token and set it on the control-plane service as GITHUB_TOKEN.
WHERE: github.com → Settings → Developer settings → Fine-grained tokens; then railway.app → superbot-websites → control-plane → Variables.
HOW: scope the token to your repos with Contents + Actions read (Actions write only if you want the CI re-run button); paste it as GITHUB_TOKEN. Exact steps: `docs/deployment.md` § owner TODO.
WHY-IT-MATTERS: every fleet page (/fleet /orders /queue /projects /reviews) runs on the anonymous 60-requests/hour GitHub ceiling today.
UNBLOCKS: reliable live fleet surfaces on the control-plane; per the PAT side-note above, the SAME token errand (added as a repo Actions secret) also unlocks live + private-repo stats for the review site's daily bake.
VERIFIED-NEEDED: wall recorded in `docs/CAPABILITIES.md` (2026-07-09: `GITHUB_TOKEN` unset/limited on the live service; anonymous rate-limit 403 captured) — the token is owner-held; no agent path exists.
```

### ⚑ Asks added by ORDER 018 PR1 (2026-07-12 — tester program `/testing` on botsite)

```markdown
⚑ OWNER-ACTION
WHAT: Set up PayPal Payouts — the payout rail you confirmed for the tester program (relayed live 2026-07-12) — and put its two credentials on the botsite service.
WHERE: paypal.com (business account) → developer.paypal.com → Apps & Credentials; then railway.app → project superbot-websites → service botsite → Variables.
HOW: (a) upgrade/create a PayPal BUSINESS account at paypal.com; (b) developer.paypal.com → Apps & Credentials → Live → Create App → copy the Client ID + Secret; (c) request/enable Payouts on that live app (PayPal gates Payouts approval on business accounts — this step can take days, start it early); (d) railway.app → superbot-websites → botsite → Variables → add PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET with those values (names exactly as written; the values never go in the repo); (e) auto-pay STAYS OFF even then — it additionally requires TESTING_AUTOPAY_ENABLED=true, which you only set once PR3 ships the live call and you want it armed. Context for the record: a regular credit card can pay IN but cannot PUSH money OUT to testers — an outbound rail (PayPal Payouts / Stripe Connect / Wise / gift-card API) is structurally required, and PayPal Payouts is the confirmed choice.
RISK: ↩️ reversible — delete the two variables to disarm; independently, the shipped v1 payout module is DRY-RUN-only (no provider HTTP call exists in the code) and the kill switch defaults OFF, so no money can move even with credentials present.
WHY-IT-MATTERS: testers are promised real money ($10–20/task); until the rail is armed every payout is a manual PayPal send you do by hand from the owner queue's ledger.
UNBLOCKS: PR3 wiring the real PayPal Payouts call behind the existing dry-run adapter, caps, and kill switch — the "automatic payout once steps are confirmed" flow you asked about.
VERIFIED-NEEDED: PayPal business-account/app creation is owner-held (no agent credential exists), and Railway variable mutations are policy-walled for agents (docs/RAILWAY-SAFETY.md — same wall as the standing Postgres/GITHUB_TOKEN asks; deliberately not attempted).
```

```markdown
⚑ OWNER-ACTION
WHAT: Set SITE_PASSWORD on the botsite Railway service so the tester-program owner queue becomes reachable.
WHERE: railway.app → project superbot-websites → service botsite → Variables → New Variable.
HOW: name SITE_PASSWORD, value = a password only you know (same pattern as the control-plane owner area; any username works at the Basic-auth prompt). One paste, Save. The queue then lives at <botsite-url>/testing/owner.
RISK: ↩️ reversible — change or delete the variable any time; while unset the queue fails closed (503) and the public /testing pages keep working.
WHY-IT-MATTERS: every tester claim and submission waits in /testing/owner for your review — without the password the queue is deliberately unreachable (503, never an open door).
UNBLOCKS: reviewing submissions, the approve/reject/mark-paid buttons, and the JSON export backup valve (the mitigation for tester data living in SQLite on the ephemeral disk).
VERIFIED-NEEDED: Railway variable mutations are policy-walled for agents (docs/RAILWAY-SAFETY.md — deliberately not attempted; same wall as the asks above).
```

**Durable-storage side-note (extends the standing Postgres ask above — not a
new ask):** the tester program's claims/submissions/payout-ledger live in
SQLite on the botsite service's **ephemeral** disk — every redeploy wipes
them (the owner queue banner + `/testing/owner/export.json` export valve are
the shipped mitigations). The SAME one-paste `DATABASE_URL` errand in the
existing "botsite submissions PostgreSQL" ask unblocks durable storage for
BOTH `/submit` and `/testing` — one database, two payoffs.

## 🟢 Decided / resolved

| # | Item | Decision | Provenance |
|---|---|---|---|
| A | **Required `quality` CI check on `main`** | **Owner set the ruleset** — `quality` is now a REQUIRED status check; PRs blocked until green. | Owner-configured ruleset 2026-07-09; verified live (PR #18 `mergeable_state=blocked` while `quality` pended). Board row shows `quality` configured + expected. |
| B | **Basic-auth gate on control-plane + dashboard** | **Dropped** — both sites are fully public; the readiness board masks Actions-secret names to a count. | Owner verbatim "Yes drop the auth"; decision stamped in `docs/decisions.md`. |
| C | **superbot kickoff doc (was PR #1876) → README link** | **Resolved** — the doc is merged on superbot `main`; the README link now returns HTTP 200 (verified 2026-07-09). Was a 404 while the PR was unmerged. | `README.md` → `superbot/docs/planning/websites-project-kickoff-2026-07-09.md`. |
| D | **Leaky born-red session gate** (PR #19 auto-merged empty on an `in-progress` card) | **Resolved — no owner action** — adopted upstream kit **v1.0.0** `bootstrap.py` (fails born-red cards under `--strict`) + folded diff-aware `--session-log` into the `quality` gate. Both directions proven + regression-tested. Upstream substrate-kit repo fix handled by a **separate** session. | Decision stamped in `docs/decisions.md` (born-red-gate entry); `.github/workflows/quality.yml`; `tests/test_born_red_session_gate.py`. |
| E | **Lane wake routine** (was Open row 7 — external owner-armed trigger) | **Self-armed and CONFIRMED working — no owner click needed.** Fleet ORDER 008 (2026-07-10) verified sessions can create routines; this lane armed trigger `trig_017H9Qb9oxtLgUy6sw2gnSHg` (cron `0 */4 * * *`, fresh-session-per-fire, prompt = the standing inbox ritual). First fire confirmed 2026-07-10T16:01:32Z (`list_triggers` `last_fired_at`; this session is that fire) — the conditional fallback ask has been withdrawn. | `control/inbox.md` ORDER 008; claim PR #56; `docs/CAPABILITIES.md` append log 2026-07-10; `.sessions/2026-07-10-order008-first-fire-manifest-smoke.md`; `control/status.md`. |
| F | **Tester payout rail (ORDER 018)** | **PayPal Payouts confirmed** as the v1 rail — no longer a decision ask; only the setup remains (the ⚑ ask above). Dry-run payout module + kill switch + caps shipped in ORDER 018 PR1. | Owner live via the coordinator session, relayed 2026-07-12; `.sessions/2026-07-12-order-018-testing-platform-pr1.md`. |

## How to use this doc

- New owner-gated fork → add a row to **Open** with where it lives.
- Owner decides → move it to **Decided / resolved** with the decision + a
  provenance pointer (a `[D-NNNN]`, a `Q-NNNN`, or a dated verification).
- Keep it short. Detail belongs in the linked decision/plan/router, not here.
