# Owner actions — decisions & actions waiting on you

> **Status:** `owner-guidance`
>
> A single **living** list of decisions/actions that only the owner can make,
> and the ones already made. Future sessions keep this current: when the owner
> decides one, move it to **Decided** with the decision + provenance; when a new
> owner-gated fork appears, add it to **Open**. Skimmable by design.

## 🟡 Open — waiting on the owner

> **Ask IDs (2026-07-16):** every ⚑ ask block below carries one
> `ID: ASK-<4 digits>` line directly under its marker. IDs are append-only —
> assigned once, never reused, never renumbered; a new ask takes the next
> free number. Verification chips (`app/askverify.py`) join on this ID exactly.

| # | Decision | What it unblocks | Notes / where it lives |
|---|---|---|---|
| 1 | ~~**Dashboard `/admin` live-bot control** — arm a production control path, or keep it dry-run?~~ **DECIDED 2026-07-18 (ORDER 035).** | The Discord-OAuth panel that writes the live bot's control API (settings / help / cog routing / submission moderation). | **DECIDED (Q-0004 / ASK-0001):** live bot control lives on the websites CONTROL-PLANE (`app/`) owner surface, gated by Discord OAuth reusing the existing SuperBot app; `/admin` dry-run stays the preview tier; the control-API token + a SEPARATE armed Railway service (ASK-0003) hold the armed path. The login half is built this session; ASK-0002/ASK-0003 are the remaining owner steps. See ORDER 035 (`control/inbox.md`) + Decided row R. |
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

> **Re-verified 2026-07-12T16:49Z (records reconcile, main @ `c5abd3e`):**
> the review-service ask is now **SATISFIED** — the fourth Railway service
> is LIVE: cold fetch `https://review-production-fc91.up.railway.app/`
> returns HTTP 200 unauthenticated, `/healthz` returns
> `{"status":"ok","service":"review"}`, `/version` reports sha `c5abd3ee`
> (= main HEAD at verification). Moved to **Decided row J** (ask text kept
> verbatim below the Decided table). The remaining asks in this block were
> re-checked and REMAIN OPEN: Q-0004 still `open` + `blocking` with
> "Maintainer answer: (unanswered)" (`docs/question-router.md`); Discord
> OAuth + armed service still gated on Q-0004; botsite `/submit` still
> serves the labeled stub (live fetch HTTP 200 with "Stub — not wired"),
> so the DATABASE_URL ask stands.

**STRUCK 2026-07-12T16:49Z (records reconcile — SATISFIED, moved to
Decided row J below; the six-field ask text is kept verbatim under the
Decided table, per "do not delete, move").**

**PAT side-note (updated 2026-07-12 — the control-plane GITHUB_TOKEN ask
itself is RESOLVED, Decided row H):** the remaining optional payoff is a
PAT with private-repo read set as a **websites repo Actions secret** for
the `review-bake` workflow — `review/gen_stats.py` runs on the ambient
Actions token (fine for public repos: "17/18 repos with live stats" in
run 29184552812) and cannot see private fleet repos, whose fleet cards
honestly say "no data mirrored yet". Optional, not blocking.

> **DECIDED 2026-07-18 (ORDER 035, `control/inbox.md`; owner delegated the
> call to the dispatched session).** Live bot control lives on the websites
> CONTROL-PLANE (`app/`) owner surface, gated by Discord OAuth REUSING the
> existing fleet-side SuperBot Discord app; the dashboard `/admin` dry-run
> panel stays the safe preview tier; the scoped control-API token + a SEPARATE
> armed Railway service (ASK-0003) remain the armed-execution architecture,
> stubbed until owner-gated creds exist. The non-gated login half (the Discord
> OAuth login flow + `require_owner` gate wiring) is BUILT this session; the
> remaining owner steps are ASK-0002 (redirect URI + env) and ASK-0003 (token +
> armed service). Six-field ask kept verbatim below.

```markdown
⚑ OWNER-ACTION — DECIDED 2026-07-18 (ORDER 035; kept for the record)
ID: ASK-0001
WHAT: Answer Q-0004 — decide WHERE live bot control lives (websites / superbot / superbot-next), or explicitly keep the dashboard's control panel dry-run-only.
WHERE: docs/question-router.md (Q-0004, open + blocking) — reply in chat or edit the "Maintainer answer" slot; the dry-run panel to judge from is live at the dashboard's /admin.
HOW: one sentence is enough ("carry it into websites as a new service" / "leave it in superbot" / "superbot-next" / "stay dry-run"). Everything downstream (OAuth app, token, armed service) hangs off this answer.
WHY-IT-MATTERS: this is THE gate — it decides whether a bot control-API credential ever enters a websites service. The 2026-07-11 bot-management build took /admin as far as it can go without it: the complete management UX now runs as an honest dry-run (docs/planning/dashboard-bot-management-readiness.md).
UNBLOCKS: the two asks below, plus the superbot-side v1 implementation of docs/specs/bot-control-api-v1.md.
VERIFIED-NEEDED: a product/topology decision only you can make (docs/question-router.md marks it product-intent · blocking · open; ORDER 001 explicitly parked it as non-agent-executable) — no agent attempt applies.
```

> **NARROWED 2026-07-18 (ORDER 035):** the Discord OAuth **login code now
> exists** on the control-plane (`app/discord_auth.py` + the `require_owner`
> gate wiring). Only the portal + env steps remain for the owner — no fresh
> Discord app needed (REUSE the existing SuperBot app, per the DECIDED
> ASK-0001). Remaining owner steps, exactly: **add a redirect URI to the
> existing SuperBot Discord app and copy the client id/secret + owner Discord
> id + session secret onto the control-plane Railway service.** Original ask
> kept verbatim below.

```markdown
⚑ OWNER-ACTION — NARROWED 2026-07-18 (ORDER 035): login code exists; only the portal + env steps remain
ID: ASK-0002
WHAT: Add a redirect URI to the existing SuperBot Discord app and copy the client id/secret + owner Discord id + session secret onto the control-plane Railway service.
WHERE: discord.com/developers/applications → the existing SuperBot app → OAuth2 → Redirects (REUSE, do not register a fresh app — the ASK-0001 decision).
HOW: add the redirect URI https://control-plane-production-abb0.up.railway.app/owner/auth/callback; then on the control-plane Railway service set DISCORD_CLIENT_ID + DISCORD_CLIENT_SECRET (copied from the SuperBot app), OWNER_DISCORD_ID (your Discord user id), and OWNER_SESSION_SECRET (a fresh random secret). NEVER paste these onto the dashboard service (a test forbids the control-API token literals there); the login flow reads them by name only.
WHY-IT-MATTERS: actor identity is the safety spine — the owner session cookie is signed with OWNER_SESSION_SECRET and the callback only mints it when the returned Discord id == OWNER_DISCORD_ID. Until these are set, /owner/login honestly says "not configured" and the /owner gate falls back to SITE_PASSWORD (or stays locked with neither).
UNBLOCKS: real Discord sign-in on the control-plane owner surface (the environments-hub remainder + the future armed panel); the code path is already wired and test-covered.
VERIFIED-NEEDED: adding a redirect URI + pasting env vars are owner-account actions on the Discord app + Railway service — no agent credential exists for either (same class as the Railway-mutation wall; deliberately not attempted).
```

> **Recon note (2026-07-18):** verified read-only across all four live services — NONE have Discord *login* (all `/login`+`/auth/callback` → 404; dashboard `/admin/login` → 200 static "not configured", no redirect; no service reads `DISCORD_*` OAuth client vars). What looks like it: botsite's "Add to Discord" button is a bot-*install* link (`botsite/data_source.py:33`, `ADD_TO_DISCORD_URL`) and dashboard's "Sign in with Discord" button leads to the not-configured `/admin/login` stub (`dashboard/app.py:454`). Any Discord app "the dashboard/mineverse instances already use" (`app/owner.py:312`) belongs to the mineverse game service in a different repo, not these four sites. This ask remains OPEN/unbuilt, still gated on ASK-0001/Q-0004.
>
> **UPDATE (2026-07-18):** the owner's "a site already has Discord login" is CONFIRMED — but it's the **SuperBot dashboard** (https://superbot-dashboard.up.railway.app), a DIFFERENT fleet repo/service, NOT any of the four websites-repo services (whose 0/4 finding above stands). A screen recording shows a full working OAuth login there (consent as menno4207, identify+guilds scopes, redirect back, panel listing 2 administered guilds). A **"SuperBot" Discord OAuth app with provisioned client creds already exists fleet-side** (active since ~Aug 2025, creds on that service's Railway env). Therefore ASK-0002's cheapest satisfaction path is likely **REUSE, not a new app**: the owner adds a redirect URI for the websites control-plane / env-hub to the existing SuperBot Discord app and pastes the same client id/secret into the websites Railway env — much smaller than registering a fresh app. **Options: (a) REUSE the existing SuperBot app [recommended], (b) register a fresh dedicated app — pending owner preference.** ASK-0002 still gated on ASK-0001/Q-0004 for O-021 regardless; no code work triggered by this.

> **UNBLOCKED 2026-07-18 (ORDER 035):** ASK-0001 is DECIDED — the armed path
> lands as a SEPARATE armed Railway service (never on the read-only control
> plane), so this ask's substance stands unchanged. It stays owner-gated:
> Railway service creation + scoped-token minting are owner-account mutations
> no agent may perform. The control-plane login flow (ASK-0002) is the actor
> identity this armed service consumes.

```markdown
⚑ OWNER-ACTION — UNBLOCKED by ORDER 035 (still owner-gated)
ID: ASK-0003
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

**STRUCK 2026-07-12 (docs truth sweep — SATISFIED, moved to Decided row M
below; the ask text is kept verbatim under the Decided table, per "do not
delete, move").** The toggle is flipped and proven end-to-end: review-bake
run `29202721928` (`event: workflow_dispatch`, actor menno420,
2026-07-12T17:49:33Z, conclusion **success**) got past the old
`createPullRequest` wall — it created PR #194 as github-actions[bot],
and #194 auto-merged (merged 2026-07-12T19:41:08Z, `merged_by:
github-actions[bot]`), landing the bake diff on main as `a513ff4`
(review/data snapshot.json + fleet.json + stats.json). Two factual notes:
(1) the first SCHEDULED (cron) bake fire is still unproven — the only
successful run so far is the manual dispatch; next cron is due
~2026-07-13 morning; (2) the stale orphan bake branches named in the ask
(`bake/review-data-20260711-202653`, `bake/review-data-20260712-073843`)
are now deletable, but branch deletion is 403-walled for agents on every
path (`docs/CAPABILITIES.md`), so they are left in place for the owner.

```markdown
⚑ OWNER-ACTION
ID: ASK-0004
WHAT: Create the botsite submissions PostgreSQL database and give the botsite service its connection string. THE CODE IS SHIPPED (PR #425 — `botsite/submissions_store.py`, `/submit` persists via DATABASE_URL, owner-authed `/submit/queue.json` read-back, DATABASE_URL declared across the env registry); the intake goes LIVE the moment DATABASE_URL is set — no further code change. Two precise, paste-ready steps:
  1. https://railway.app/project/70198ece-cbc0-484e-86d9-f8a1eca4f045 → New → Database → PostgreSQL.
  2. botsite service → Variables → add DATABASE_URL = `${{Postgres.DATABASE_URL}}` (Railway's reference to the new DB) — one entry. Railway redeploys botsite → intake live.
WHERE: railway.app → project superbot-websites → New → Database → PostgreSQL; then service botsite → Variables.
HOW: add variable DATABASE_URL = `${{Postgres.DATABASE_URL}}` (a Railway service-reference to the new Postgres, so the string tracks the DB automatically). One entry.
THEN VERIFY: POST the /submit form on the live botsite → it should say received; `GET /submit/queue.json` (owner Basic-auth via SITE_PASSWORD) lists the new submission.
WHY-IT-MATTERS: the public /submit intake (feature/bug submissions with a moderated queue) stays fail-soft "intake not live" until DATABASE_URL exists — the whole pipeline is one paste away.
UNBLOCKS: the submissions pipeline (rework Q5 — Open row 2 above); the moderation → GitHub-issue mirror is the follow-up build once data can persist.
VERIFIED-NEEDED: attempted via the account API this session — classifier-walled (verbatim "Permission for this action was denied by the Claude Code auto mode classifier. Reason: Blocked by classifier."; `docs/CAPABILITIES.md` 2026-07-18 wall entry, tried twice); requires an owner UI action. Still owner-gated. Click steps first recorded in `docs/retro/self-review-2026-07-11.md` §2.
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

### ⚑ Asks added by ORDER 018 PR1 (2026-07-12 — tester program `/testing` on botsite)

```markdown
⚑ OWNER-ACTION
ID: ASK-0005
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
ID: ASK-0006
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

### ⚑ Ask added by ORDER 018 PR2 (2026-07-12 — AI exit-review on `/testing`)

**STRUCK 2026-07-12T17:56Z (ORDER 022 reconcile — SATISFIED, moved to
Decided row K below; the ask text is kept verbatim under the Decided
table, per "do not delete, move").** The final verification the
"reported RESOLVED" framing was waiting on has now happened: the review
service's live `/ask` page (cold fetch 2026-07-12) renders WITHOUT the
"Live assistant degraded" banner and says "assistant is live, answering
server-side" — `ai_ready` is true at runtime, so the key is present.

### ⚑ Ask added by ORDER 020 (2026-07-12 — owner writeback on the launch console)

**STRUCK 2026-07-18 (SATISFIED / verified-live — moved to Decided row O
below; the six-field ask text is kept verbatim under the Decided table, per
"do not delete, move").** Verified live 2026-07-18: O-020 owner writeback
commits end-to-end via branch+auto-PR — live test note → PR #399 → merged
`main` `b12dcd9`; the deployed control-plane `GITHUB_TOKEN` already has
`contents:write` + `pull-requests:write` (no owner paste/overwrite was
needed). ORDER 020 done-when discharged. (Supersedes the 2026-07-18 status
clarification and its "direct-to-main vs branch+PR" open design question —
resolved to branch+PR, Q2=b owner-confirmed, PR #398; the runtime opens the
PR itself, which is why PR-write is also required and already present.)

### ⚑ Ask added by the 2026-07-12 records reconcile (`/owner/environments` live half — ORDER 016 follow-through)

**STRUCK 2026-07-12T17:56Z (ORDER 022 reconcile — SATISFIED, moved to
Decided row L below; the ask text is kept verbatim under the Decided
table, per "do not delete, move").** RAILWAY_TOKEN was set on the
control-plane service (superbot-websites/production) 2026-07-12 and the
service redeployed (owner directive, ORDER 022 — fleet-manager
`control/inbox.md` @ `1bb53f9`). Independently verified same day: a live
Railway GraphQL read during ORDER 022's query-shape verification shows
the variable NAME `RAILWAY_TOKEN` present on control-plane/production
(names only, never values), and all three query shapes in
`app/railway.py` verified correct against the live API (its stale
"UNVERIFIED" docstring note is now updated).

### ⚑ Ask added 2026-07-13 (bake required-check wall — extends the ORDER 020 PAT ask)

```markdown
⚑ OWNER-ACTION
ID: ASK-0008
WHAT: Extend the ORDER 020 fine-grained PAT so ONE token serves both needs — when minting it, grant menno420/websites BOTH Contents: Read and write (ORDER 020's writeback need) AND Pull requests: Read and write (bake PR creation as a real actor) — then ALSO store it as a websites repo Actions secret named BAKE_PAT; an agent session then switches review-bake's GH_TOKEN to it. **Recommended: one PAT, two scopes, three paste targets (control-plane + botsite Railway GITHUB_TOKEN per ORDER 020, plus the BAKE_PAT Actions secret) — this is the durable fix for the nightly bake PRs sitting blocked.**
WHERE: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens (Repository access: Only select repositories → menno420/websites; Permissions → Contents: Read and write, Pull requests: Read and write); then github.com/menno420/websites → Settings → Secrets and variables → Actions → New repository secret → name BAKE_PAT.
HOW: generate the token once with both permissions, paste it into the ORDER 020 targets (Railway GITHUB_TOKEN on control-plane + botsite) and into the new BAKE_PAT Actions secret (the value never goes in the repo). Say the word and a session flips review-bake.yml's landing step to `GH_TOKEN: ${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}`.
RISK: ↩️ reversible — revoke the PAT / delete the BAKE_PAT secret any time; the workflow change will be written with that explicit `|| secrets.GITHUB_TOKEN` fallback, so an unset or revoked secret returns to exactly today's behavior (GITHUB_TOKEN-created PR, checkless until a session close/reopens it) rather than breaking the bake.
WHY-IT-MATTERS: measured 2026-07-13 (docs/CAPABILITIES.md wall entry): a bake PR created with the Actions GITHUB_TOKEN gets no pull_request-event checks, and the #269 dispatch-chained quality run goes GREEN on the PR head (run 29242891214 on PR #270) but the main ruleset still refuses it — verbatim `405 Repository rule violations found` / `Required status check "quality" is expected.` — so armed auto-merge never fires and every nightly bake PR waits for a hand. A PAT-created PR is a real actor's PR: it triggers its own pull_request quality run, the exact kind the ruleset counts.
UNBLOCKS: the nightly bake loop becomes fully hands-off (bake → PR → real pull_request quality run → auto-merge on green); no more parked bake PRs like #270; interim close/reopen ritual retired.
VERIFIED-NEEDED: the next scheduled bake's PR shows a pull_request-event `quality` run in its checks tab and auto-merges without any intervention. PAT minting + repo-secret creation are owner-held (no agent credential exists — same wall class as the ORDER 020 ask above); the failing 405 path itself WAS attempted and captured verbatim this session (PR #270).
```

> **Interim (2026-07-18):** the owner added the `BAKE_PAT` repo Actions secret
> (live owner action). The workflow line is now flipped in PR #434 —
> review-bake.yml's landing step reads `GH_TOKEN: ${{ secrets.BAKE_PAT ||
> secrets.GITHUB_TOKEN }}` — pending merge and post-merge PAT-path proof (a
> `workflow_dispatch` bake PR showing a pull_request-event `quality` run that
> auto-merges). Not yet moved to Decided; the VERIFIED-NEEDED check above is
> the remaining gate.

> **SATISFIED — with evidence, 2026-07-19 (final resolution).** The
> VERIFIED-NEEDED gate is now met end-to-end. PR #434 merged to main as
> `403a91de` — review-bake.yml's landing step reads
> `GH_TOKEN: ${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}`. A proof
> `workflow_dispatch` (review-bake.yml run 29678801173, actor menno420 →
> success) created bake PR #438 on `bake/review-data-20260719-075148`,
> **authored by `menno420`** (the BAKE_PAT identity, NOT github-actions[bot]);
> the PR received a real `pull_request`-event `quality` check and had
> auto-merge armed (squash) — proving the PAT landing path lands nightly bakes
> hands-off. The old-token direct push still hit GH013 and correctly fell back
> to the PAT-PR + auto-merge path (by design). Cleanup: stale pre-fix bot bake
> PRs #422 and #437 closed (superseded, no-limbo rule). ASK-0008 is
> discharged.

### ⚑ Ask added 2026-07-13 (env-leads close — ORDER 027 item 4)

```markdown
⚑ OWNER-ACTION
ID: ASK-0009
WHAT: Delete the unused SITE_PASSWORD variable from the dashboard Railway service — set-but-unused drift left over from the removed 2026-07-09 Basic-auth gate.
WHERE: railway.app → project superbot-websites → service dashboard → Variables → SITE_PASSWORD → delete.
HOW: one delete, Save. Nothing else to change — the dashboard app has zero readers of this variable (`rg SITE_PASSWORD dashboard/` matches nothing; PR #282 read-path check, documented docs/dashboard.md:127). The real readers live elsewhere: app/config.py (control-plane /owner) and botsite/testing.py (/testing/owner) — those services' variables are untouched by this errand.
RISK: ✅ reversible and inert — the variable is read by nothing on the service, so deleting it changes no behavior; re-add it in the console any time if the gate ever returns.
WHY-IT-MATTERS: a live credential-shaped variable that no code reads is pure drift — it misleads every env audit (the ORDER 026 names-only read flagged it as "undocumented") and pads the missing-vs-set signal on /owner/environments.
UNBLOCKS: a clean dashboard env surface — future names-only reads and envhub audits stop tripping over a ghost variable.
VERIFIED-NEEDED: Railway variable mutations are policy-walled/harness-denied for agents (docs/RAILWAY-SAFETY.md; docs/CAPABILITIES.md 2026-07-13 verbatim denial — deliberately not attempted). Verify after deletion: the next names-only read / the /owner/environments dashboard group no longer lists SITE_PASSWORD.
```

### ⚑ Asks added 2026-07-16 (arcade launch-blocker join — the two public arcade promises become ledger rows)

> Both clicks have been rendered as "What's blocking launch" panels on the
> public arcade detail pages since PR #349 and machine-probed by the owner
> console since the 2026-07-15 preflight slice — but neither had a ledger
> row, so their verification chips could only bind by keyword signature.
> These rows give them stable ids; `botsite/data/arcade.json` blockers and
> `app/askverify.py` now join on the id exactly.

**STRUCK 2026-07-18 (SATISFIED — moved to Decided row P below; the six-field
ask text is kept verbatim under the Decided table, per "do not delete, move").**
The owner published the GitHub Release `lumen-drift-v1.3` on
`menno420/gba-homebrew` (~2026-07-18 20:10Z). Independently verified 2026-07-18:
`git ls-remote --tags https://github.com/menno420/gba-homebrew.git` reads the
live tag `lumen-drift-v1.3` (SHA `e64651ce4dbb5e99f31adf370da23f31716ef849`),
and the review release-drift bake (`review/gen_releases.py`) now records
lumen-drift `drift: false` ("expected release lumen-drift-v1.3 matches the live
latest tag"; `drift_count` 1 → 0). `botsite/data/arcade.json` flipped:
availability → `download`, url set to the published release page
(`https://github.com/menno420/gba-homebrew/releases/tag/lumen-drift-v1.3` — the
direct `.gba` asset URL is not HTTP-verifiable from the session egress, so the
guaranteed-live release page is recorded), blocker dropped. The arcade card +
detail page now carry a real Download button.

**STRUCK 2026-07-18 (SATISFIED — moved to Decided row Q below; the six-field
ask text is kept verbatim under the Decided table, per "do not delete, move").**
The owner ran product-forge's "Deploy games-web to Pages" workflow (run #3,
SUCCESS, 2026-07-18 ~20:10Z), publishing the site. Independently verified
2026-07-18: `https://menno420.github.io/product-forge/` returns HTTP 200 with
real content (the games-web character-sheet app — `<title>games-web · Character
Sheet (phase 1 · mock data)</title>`, not a Pages 404 placeholder).
`botsite/data/arcade.json` flipped: availability → `live`, url set to
`https://menno420.github.io/product-forge/`, blocker dropped. The arcade card +
detail page now carry a real Play link.

### ⚑ Asks added 2026-07-16 (registry blocker join — catalog / products / puddle-museum owner gates become ledger rows)

> The three remaining botsite registries (catalog.json, products.json,
> puddle_museum.json) gained the same optional blocker+ask_id object the
> arcade carries (PR #360's schema, shared via botsite/blockers.py): every
> genuinely owner-gated entry now renders its owner click/decision on the
> public page and joins these rows by stable id. The five write-slice
> parked titles (the-marginalia-society, the-night-kiln, the-paper-orange,
> the-pepper-ledger, the-windmill-mouse) get NO row and NO blocker — a
> missing manuscript is agent work, not an owner action. Unlike
> ASK-0010/0011, NONE of these five rows is machine-checkable (Gumroad
> listing state, off-repo files, product/money decisions) — each
> VERIFIED-NEEDED says so plainly, and app/askverify.py registers them
> probe-less with the honest reason.

```markdown
⚑ OWNER-ACTION
ID: ASK-0012
WHAT: Run the Gumroad publish pass — one owner session that publishes the ten publish-ready catalog titles and products, which also un-gates the Ship-It Bundle and flips the three fleet-store coming-soon mirrors.
WHERE: gumroad.com (the mennomagic01 store, where stripe-webhook-test-kit already lives) — the staged copy is in venture-lab (per-title vetting packets under docs/publishing/vetting/, launch copy under docs/launch/); the public faces are /products/catalog and /products on the botsite.
HOW: for each of the ten (membership-kit, template-packs, agent-fleet-field-manual, kill-rule-intake-kit, false-green-test-trap, merge-wall-cookbook, the-slow-word, the-weigh-house, de-waag, het-trage-woord): create the listing from the staged copy, hit Publish, do your own test purchase, then say the word — a session records each live URL in botsite/data/catalog.json (+ the three products.json mirrors: membership-site-boilerplate-kit, agent-workflow-template-pack, agent-fleet-field-manual), flipping status/availability to live and dropping the blocker. The Ship-It Bundle (bundle-starter) becomes publish-ready the moment its two components (membership-kit + template-packs) are live — a Gumroad bundle references existing live products.
RISK: ↩️ reversible — unpublish any listing on Gumroad at any time; nothing moves in this repo until a session records the live URLs.
WHY-IT-MATTERS: eleven of the catalog's 22 entries plus three of the four store products sit honestly labeled "awaiting the owner's publish click" on the public pages — the entire publish-ready shelf is one owner session away from being real, and until then every card explains itself with a blocker panel instead of a Buy link.
UNBLOCKS: the ten catalog entries and the three product mirrors flip from blocker panel to a real Buy link; bundle-starter's hard gate clears; the catalog's "publish-ready" group empties into "live".
VERIFIED-NEEDED: NOT machine-checkable — Gumroad listing state is not observable by any read-only probe this repo holds (no Gumroad credential exists; deliberately not attempted). Verification is a session recording the live listing URLs in the registries, where the existing no-dead-links tests then pin them.
```

```markdown
⚑ OWNER-ACTION
ID: ASK-0013
WHAT: Hand off the full-res photo originals for the two wallpaper packs (Dutch Skies + Golden Hours) — the sellable files are owner-held off-repo.
WHERE: your own photo library → any private handoff channel you choose, or a direct upload to the Gumroad listing yourself; the one place they must NOT land is this public repo. The catalog entry is photo-packs on /products/catalog.
HOW: deliver the full-resolution originals once (private share, or upload them straight to a Gumroad product you create); a session then packages/stages the sellable zips and the publish click follows the same Gumroad pass as ASK-0012.
RISK: ↩️ reversible — a private handoff can be withdrawn before anything is published; nothing lands in the public tree by design.
WHY-IT-MATTERS: the catalog says it honestly — "the sellable zips cannot exist in the public repo — full-res originals are owner-held off-repo, so nothing proceeds until the owner hands them off." No agent can produce this product without the files.
UNBLOCKS: photo-packs moves from hard-gated to publish-ready (then live via the Gumroad pass); its blocker panel drops.
VERIFIED-NEEDED: NOT machine-checkable — whether owner-held off-repo files have been handed off is not observable by any read-only probe; verification is the files arriving wherever you choose to put them, then a session updating the catalog entry.
```

```markdown
⚑ OWNER-ACTION
ID: ASK-0014
WHAT: Pick the Ultramarine title — publish as "The Widow's Blue" (the vetting packet's recommended rename; the title-collision work is done) or keep Ultramarine.
WHERE: reply in chat, or write it back from the site's owner console (/owner/queue); the packet is venture-lab docs/publishing/vetting/ultramarine.md; the catalog entry is ultramarine on /products/catalog.
HOW: one sentence ("The Widow's Blue" / "keep Ultramarine"). A session then applies the chosen title across the manuscript and listing copy, and the book joins the ASK-0012 Gumroad publish pass.
RISK: ↩️ reversible until publish — a title choice costs nothing to change while the book is unpublished.
WHY-IT-MATTERS: the packet's status note records a title collision worked to a recommendation ("rename to 'The Widow's Blue' recommended … owner picks") — publishing under a colliding name buries the book in search results, and a naming call on a book is the owner's to make.
UNBLOCKS: the last open decision on this title clears; ultramarine joins the ASK-0012 publish set.
VERIFIED-NEEDED: NOT machine-checkable — a naming decision has no external state to probe; verification is your word (chat or console writeback), then the recorded title in the catalog entry.
```

```markdown
⚑ OWNER-ACTION
ID: ASK-0015
WHAT: Decide the §5 illustration gate — the money-decision on commissioning illustrations for the picture books (The Painted Stones and The Puddle Museum), which also gates all three Puddle Museum editions (EN/NL/DE).
WHERE: the vetting packets' §5 (venture-lab docs/publishing/vetting/the-painted-stones.md + the-puddle-museum.md); the public faces are /products/catalog (both parked entries) and /puddle-museum (all three coming-soon edition cards); reply in chat or via /owner/queue.
HOW: one decision — fund/commission illustrations (name a budget or an illustrator and a session takes it from there), choose an alternative you accept, or explicitly keep them parked. The seat's recommendation on record is Park.
RISK: 💰 a spend decision — the only ask in this set that can cost real money; parking costs nothing and is the recorded recommendation.
WHY-IT-MATTERS: picture books do not ship without pictures, and buying illustration is a real-money commitment agents must never make on their own — five public cards (two catalog entries, three editions) honestly wait on this single fork.
UNBLOCKS: on a go — the illustration work, then publication of both picture books and the three Puddle Museum editions; on an explicit park — the panels can say "parked by owner decision" instead of "pending".
VERIFIED-NEEDED: NOT machine-checkable — a product/money decision with no external state to probe (the same class as ASK-0001); verification is your word, then this row moving to Decided.
```

```markdown
⚑ OWNER-ACTION
ID: ASK-0016
WHAT: Arrange the native-speaker Dutch proofread for De papieren sinaasappel — its packet marks the proofread a blocking quality gate before that title's publish click.
WHERE: a native Dutch reader you trust (you, or someone you pick); the packet is venture-lab docs/publishing/vetting/de-papieren-sinaasappel.md; the catalog entry is de-papieren-sinaasappel on /products/catalog.
HOW: have the manuscript read by a native speaker and feed the corrections back in any form — notes in chat are enough, a session works them in. (De Waag and Het trage woord carry the same proofread as a pending explicit owner step, but their packets sequence them behind their EN editions rather than blocking on it — this row covers only the title whose packet says blocking.)
RISK: ↩️ reversible — a proofread only ever improves the manuscript; nothing publishes until the separate publish click.
WHY-IT-MATTERS: a Dutch literary-historical novel (WWII, Hongerwinter — a subject Dutch readers know intimately) shipping with non-native prose errors would damage the title and the store; the packet made this the one explicit blocking quality gate.
UNBLOCKS: the last blocking step before de-papieren-sinaasappel joins the ASK-0012 Gumroad publish pass.
VERIFIED-NEEDED: NOT machine-checkable — whether a human proofread happened is not observable by any probe; verification is the corrections arriving (chat or console writeback) and a session updating the packet's gate note.
```

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
| I | **Tester payout rail (ORDER 018)** | **PayPal Payouts confirmed** as the v1 rail — no longer a decision ask; only the setup remains (the ⚑ ask above). Dry-run payout module + kill switch + caps shipped in ORDER 018 PR1. | Owner live via the coordinator session, relayed 2026-07-12; `.sessions/2026-07-12-order-018-testing-platform-pr1.md`. |
| J | **Review Railway service** (was the standing fourth-service ⚑ ask) | **DONE by owner** — the review service is LIVE at `https://review-production-fc91.up.railway.app`: `/` returns HTTP 200 unauthenticated, `/healthz` returns `{"status":"ok","service":"review"}`, `/version` reports sha `c5abd3ee` (= main HEAD at verification — the service is deploy-current). Follow-ups now unblocked (not owner-gated): add the fourth service to the board's deploy-drift row + `scripts/healthcheck.py`. | Cold fetches 2026-07-12T16:49Z (records reconcile); ask text kept verbatim below. Re-confirmed 2026-07-12T17:56Z (ORDER 022 reconcile): `/healthz` still 200 `{"status":"ok","service":"review"}`, and the control-plane's live `/api/readiness.json` deploy-drift row now tracks all FOUR services `in_sync` at `e25d7d58` (`all_in_sync: true`). |
| K | **ANTHROPIC_API_KEY on botsite + review** (was the ORDER 018 PR2 exit-review ask, "reported RESOLVED" pending final verification) | **DONE** — the key was set on both services per ORDER 022 (owner directive, fleet-manager `control/inbox.md` @ `1bb53f9`) and the pending verification has now happened: the review service's live `/ask` page renders with NO "Live assistant degraded" banner and says "assistant is live, answering server-side" — `ai_ready` true at runtime. **Ground-truth flag 2026-07-13 (ORDER 026 discovery):** a live GraphQL names read 2026-07-13 (names only, never values) shows ANTHROPIC_API_KEY **ABSENT** on superbot-websites/botsite — likely set on the parallel botsite copy in the production-bot project instead — and dashboard carries an undocumented SITE_PASSWORD (drift). **Read-path check CLOSED 2026-07-13 (PR #282, ORDER 027 item 4):** dashboard reads no `SITE_PASSWORD` (set-but-unused drift, `docs/dashboard.md:127`; real readers `app/config.py` + `botsite/testing.py`); the botsite-copy key stays **not measured — walled** (`docs/botsite.md:108`; Railway reads/writes harness-denied, `docs/CAPABILITIES.md` 2026-07-13); the unused dashboard variable's deletion is the ⚑ ask above. | Cold fetch of `https://review-production-fc91.up.railway.app/ask` 2026-07-12T17:56Z (ORDER 022 reconcile); ORDER 022 @ fleet-manager `control/inbox.md` `1bb53f9`; ask text kept verbatim below. |
| L | **RAILWAY_TOKEN on control-plane** (was the `/owner/environments` live-half ask) | **DONE by owner** — a project-scoped token was set as RAILWAY_TOKEN on the control-plane service (superbot-websites/production) 2026-07-12 and the service redeployed (ORDER 022 directive). Supporting evidence: a live Railway GraphQL read (ORDER 022 query-shape verification, 2026-07-12) shows the variable NAME `RAILWAY_TOKEN` present on control-plane/production, and all three `app/railway.py` query shapes (`projectToken`, `project(id:)`, `variables(...)`) verified correct against the live API — verdict already-correct, stale "UNVERIFIED" docstring updated. | ORDER 022 @ fleet-manager `control/inbox.md` `1bb53f9`; live GraphQL shape verification 2026-07-12 (names only, never values); ask text kept verbatim below. |
| M | **Actions "create and approve pull requests" toggle** (was the archive-consolidated review-bake follow-up ask) | **DONE by owner — proven end-to-end.** review-bake run `29202721928` (`event: workflow_dispatch`, actor menno420, 2026-07-12T17:49:33Z) succeeded, created PR #194 as github-actions[bot], and #194 auto-merged (`merged_by: github-actions[bot]`, 2026-07-12T19:41:08Z) — bake diff on main `a513ff4`. The Actions `createPullRequest` wall is gone. Residuals: first SCHEDULED (cron) success still unproven (next cron ~2026-07-13 morning); the two stale orphan bake branches remain (branch deletion 403-walled for agents — `docs/CAPABILITIES.md` — owner cleanup). | Run + PR verified via GitHub API 2026-07-12 (docs truth sweep); merge commit `a513ff4` on main; ask text kept verbatim below. |

| N | **Railway env-var placeholders — resolved: will NOT be pre-created (paste real values directly)** (ORDER 026) | **Deliberately NOT created — agent decision, 2026-07-13.** Empty placeholders would falsely badge `set-live` on `/owner/environments` (the live read is names-only: `app/railway.py` `_names_only()` drops values, so envhub/envdrift cannot tell empty-but-present from configured) and would blind the missing-vs-set signal; additionally, empty values crash 3 services at import (`int("")` on the CACHE_TTL-style vars) or silently blank URL defaults. Independently, the one write probe was harness-denied before reaching Railway. Six-field guidance block below. | ORDER 026 @ `control/inbox.md` `b0e542c`; `docs/CAPABILITIES.md` append log 2026-07-13 (verbatim denial); live GraphQL names read 2026-07-13 (names only, never values) — missing per service: control-plane 11 / botsite 16 / dashboard 5 / review 2. |

| O | **O-020 owner writeback PAT / GITHUB_TOKEN** (was ASK-0007) | **SATISFIED — verified LIVE 2026-07-18, no owner action needed.** O-020 owner writeback commits end-to-end via branch+auto-PR: a live `/owner/queue` test note → branch `claude/owner-writeback-1` (`0be58459`) → auto-PR **#399** → quality green → auto-merged to `main` as **`b12dcd9`**. The deployed control-plane `GITHUB_TOKEN` already carries BOTH `contents:write` AND `pull-requests:write` (the runtime opens the PR itself), so **no owner paste or overwrite was needed** — ORDER 020's done-when is discharged. The 2026-07-18 "direct-to-main vs branch+PR" design question is resolved to branch+PR (Q2=b owner-confirmed, PR #398). | Live submit→branch→PR→merge chain verified 2026-07-18 (real commit SHA `0be58459`, PR #399, merge `b12dcd9`); ask text kept verbatim below. |

| P | **Publish the lumen-drift-v1.3 release** (was ASK-0010) | **DONE by owner — verified LIVE 2026-07-18.** The GitHub Release `lumen-drift-v1.3` is published on `menno420/gba-homebrew` (~2026-07-18 20:10Z). Independently verified: `git ls-remote --tags` reads the live tag `lumen-drift-v1.3` (SHA `e64651ce4dbb5e99f31adf370da23f31716ef849`), and the review release-drift bake now records lumen-drift `drift: false` (`drift_count` 1 → 0). `botsite/data/arcade.json` flipped (availability → `download`, url → the release page, blocker dropped) — the arcade card gains its real Download button. The direct `.gba` asset URL was not HTTP-verifiable from the session egress (github.com web/API for gba-homebrew is walled for this session; only git transport is allowed), so the guaranteed-live release page is the recorded download target. | Live git-transport tag read + release-drift bake 2026-07-18; arcade flip in `botsite/data/arcade.json`; `review/data/releases.json` `drift_count: 0`; ask text kept verbatim below. |

| Q | **Configure product-forge Pages** (was ASK-0011) | **DONE by owner — verified LIVE 2026-07-18.** The owner ran product-forge's "Deploy games-web to Pages" workflow (run #3, SUCCESS, 2026-07-18 ~20:10Z). Independently verified: `https://menno420.github.io/product-forge/` returns HTTP 200 with real content (the games-web character-sheet app, not a Pages 404 placeholder). `botsite/data/arcade.json` flipped (availability → `live`, url set, blocker dropped) — the arcade card gains its real Play link. | Live HTTPS 200 + real-content read 2026-07-18; arcade flip in `botsite/data/arcade.json`; ask text kept verbatim below. |

| R | **Where live bot control lives (Q-0004 / ASK-0001)** (was Open row 1 + the standing three-ask block) | **DECIDED 2026-07-18 — owner delegated the call to the dispatched session (ORDER 035).** Live bot control lives on the websites CONTROL-PLANE (`app/`) owner surface, gated by Discord OAuth REUSING the existing fleet-side SuperBot Discord app. The dashboard `/admin` dry-run panel stays the safe preview tier. The scoped control-API token + a SEPARATE armed Railway service (ASK-0003) remain the armed-execution architecture, stubbed until owner-gated creds exist. The non-gated login half — `app/discord_auth.py` (the OAuth authorization-code login flow, signed session cookie, CSRF `state` floor) + `require_owner` accepting a Discord session OR SITE_PASSWORD — is built + test-covered this session; env-unset stays fail-closed and names the opening owner action. Remaining owner steps: ASK-0002 (redirect URI + env) and ASK-0003 (token + armed service). | ORDER 035 (`control/inbox.md`, 2026-07-18); owner verbatim delegation "#4 … if you have a recomended decision, then decide"; branch `claude/discord-oauth-owner-gate`; ASK-0001 six-field ask kept verbatim above. |

### Resolved guidance — kept as six fields (Decided row N, 2026-07-13)

```markdown
⚑ OWNER-ACTION — RESOLVED 2026-07-13 (Decided row N; guidance, not a new ask)
WHAT: ORDER 026 outcome — Railway env-var placeholders were deliberately NOT pre-created; when you configure a variable, create it with its real value in the same step.
WHERE: railway.app → project superbot-websites → each service → Variables.
HOW: paste the REAL value when creating each variable — the /owner/environments checklist shows exactly which names are missing per service (2026-07-13 live read: control-plane 11, botsite 16, dashboard 5, review 2), so no pre-created empty entries are needed to know what to fill.
RISK: ✅ — nothing was changed on Railway.
WHY-IT-MATTERS: the live read is names-only (`app/railway.py` `_names_only()` drops values at the client boundary), so an empty placeholder falsely badges `set-live` and blinds the missing-vs-set signal on /owner/environments; empty values would also crash 3 services at import (`int("")` on the CACHE_TTL-style vars) or silently blank URL-default vars.
UNBLOCKS: the existing per-var asks (SITE_PASSWORD, PAYPAL_CLIENT_ID/SECRET, GITHUB_TOKEN contents-write rows above) stay accurate exactly as written — each remains one paste of a real value.
VERIFIED-NEEDED: nothing to click for this row itself — verification is built in: the /owner/environments badge flips to `set-live` only when the real value lands. (The write probe's harness denial is quoted verbatim in docs/CAPABILITIES.md, 2026-07-13.)
```

### Satisfied ask — kept verbatim (Decided row J, satisfied by 2026-07-12)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-12 (Decided row J; kept for the record)
WHAT: Create the fourth Railway service so the new program-review site (built for Anthropic reviewers) goes live.
WHERE: railway.app → project superbot-websites → New → Service → GitHub repo menno420/websites.
HOW: set Root Directory = review (the service's own Dockerfile at review/Dockerfile is picked up automatically, exactly like botsite/dashboard); branch = main; no environment variables needed (the service is read-only and network-free). After the first deploy, check <service-url>/healthz returns {"status":"ok"} and /version shows the deployed sha.
WHY-IT-MATTERS: the review site — process, growth charts, successes, an honest problems page, and (since the 2026-07-11 expansion) the fleet index, continuous review editions with a subscribable Atom feed, and the evidence-backed questionnaire — exists on main but has no URL until the service exists.
UNBLOCKS: a shareable live URL for Anthropic reviewers (including /reviews/feed.xml they can subscribe to); the board's deploy-drift row and scripts/healthcheck.py can then also add the fourth service. The scheduled review-bake workflow already refreshes the site's committed data daily, so the service goes live self-updating.
VERIFIED-NEEDED: service creation is a Railway account mutation — the Railway-safety policy (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger) forbids agent-initiated Railway mutations without your explicit go, so this was deliberately not attempted (the same policy wall as the Postgres ask; no new attempt/error needed).
```

### Satisfied ask — kept verbatim (Decided row K, satisfied by 2026-07-12)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-12 (Decided row K; kept for the record)
WHAT: ~~Set ANTHROPIC_API_KEY on the botsite Railway service so the tester program's AI exit-review runs.~~ Reported wired 2026-07-12: the coordinator session copied the key from the Railway "worker" service via the Railway API onto BOTH the botsite and review services (verified present by name; services auto-redeployed).
WHERE: was: console.anthropic.com → API Keys; railway.app → superbot-websites → botsite → Variables. Now: nothing — the variable is reportedly already on botsite (and review).
HOW: no action. Optional tuning knobs remain available (defaults are sensible): TESTING_AI_MODEL (default claude-haiku-4-5-20251001 — cheap grading), TESTING_AI_DAILY_CAP (default 50 calls/day), TESTING_AUTOPAY_MIN_SCORE (default 80).
RISK: ↩️ reversible — delete the variable any time; while unset the program degrades honestly (submissions accepted exactly as before, pages say the review is manual) and no call is ever made. Spend is bounded even with the key set: ~1500 max output tokens/call, 50 calls/day default, 4 calls/submission, one retry max.
WHY-IT-MATTERS: with the key present each tester submission arrives in the owner queue pre-graded (0–100 score, low-effort flag, findings by severity, follow-up Q&A) and the auto-pay gate computes real eligibility for PR3.
UNBLOCKS: the AI exit-review shipping in ORDER 018 PR2 goes live on merge with no owner errand; the same integration pattern is the template for ORDER 017's review-site assistant.
VERIFIED-NEEDED: the wiring report is relayed from the coordinator session and is NOT independently verifiable from this repo (no agent credential here can read Railway variables — docs/RAILWAY-SAFETY.md still walls agent-initiated Railway reads/mutations from repo sessions). Verify after #176/#179 merge via the owner queue's AI-state panel at <botsite-url>/testing/owner (it shows whether the key is present at runtime). Only if that panel shows degraded does the original one-paste ask above come back into force.
```

### Satisfied ask — kept verbatim (Decided row L, satisfied by 2026-07-12)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-12 (Decided row L; kept for the record)
WHAT: Mint a Railway token scoped to the superbot-websites project ONLY (prefer the most read-only scope Railway offers — the page issues GraphQL queries exclusively, no mutation strings exist in app/railway.py) and set it as RAILWAY_TOKEN on the control-plane Railway service, so /owner/environments shows live deploy/variable data.
WHERE: railway.app → project superbot-websites → Settings → Tokens → create a PROJECT-scoped token (never the account key, never the ambient production RAILWAY_*_ID trio — docs/RAILWAY-SAFETY.md); then railway.app → superbot-websites → service control-plane → Variables → New Variable RAILWAY_TOKEN.
HOW: create the project token, copy it once, paste it as RAILWAY_TOKEN on the control-plane service (the value never goes in the repo). The read layer picks it up on the service's automatic redeploy; then open /owner/environments — the live half should flip from the "not-configured" owner-errand banner to per-service variable NAMES (names + presence only, never values — app/railway.py drops values at the client boundary).
WHY-IT-MATTERS: the gated /owner/environments page (PR #166, ORDER 016 slice 1) is live behind the owner gate (HTTP 401 unauthenticated, verified 2026-07-12) but its live half renders "not-configured" while RAILWAY_TOKEN is unset — you only see the committed facts, not what is actually configured where; the owner decided 2026-07-11 to mint this token but it has not landed (docs/CAPABILITIES.md 2026-07-12 wall entry).
UNBLOCKS: live env-var-name visibility across all four services from one gated page, and first real-API verification of the GraphQL read path (UNVERIFIED until the token exists, per the capability ledger).
VERIFIED-NEEDED: code path confirmed 2026-07-12 — app/config.py reads RAILWAY_TOKEN from the env; app/railway.py renders state "not-configured" while it is unset and the CAPABILITIES ledger records the token as NOT provisioned (session env + deployed service, 2026-07-12). Token minting + Railway variable mutations are owner-held / policy-walled for agents (docs/RAILWAY-SAFETY.md — deliberately not attempted; same wall as the asks above).
```

### Satisfied ask — kept verbatim (Decided row M, satisfied by 2026-07-12)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-12 (Decided row M; kept for the record)
WHAT: Allow GitHub Actions to create pull requests on menno420/websites, so the daily review-bake can land its data refresh.
WHERE: github.com/menno420/websites → Settings → Actions → General → "Workflow permissions" → check "Allow GitHub Actions to create and approve pull requests" → Save.
HOW: one checkbox + Save. Optionally afterwards: Actions → review-bake → "Run workflow" (branch main) to land the first bake immediately instead of waiting for the daily cron.
WHY-IT-MATTERS: the review-bake workflow has now run TWICE and failed BOTH times at the same wall — run 29167034060 (event: workflow_dispatch, 2026-07-11T20:26:33Z, your manual run) and run 29184552812 (event: schedule, 2026-07-12T07:38:28Z — the daily cron IS firing). Each run baked the data fine (snapshot + fleet + stats: "17/18 repos with live stats"), was correctly ruleset-blocked from pushing to main, pushed its fallback branch, then died at `gh pr create` with: "GraphQL: GitHub Actions is not permitted to create or approve pull requests (createPullRequest)". Until the toggle flips, every daily bake fails. (Staleness fix 2026-07-12T16:49Z: review/data/stats.json is no longer absent from main — an agent session landed it manually via ORDER 017 A, PR #175 — but the AUTOMATED daily loop is still dead: the workflow's run history still shows exactly the same 2 runs, both failed; no run has succeeded since.)
UNBLOCKS: the self-updating review-site data loop (snapshot/fleet/stats refreshed daily via [bake] PRs that auto-merge on green); also makes the two orphan branches the failed runs pushed (bake/review-data-20260711-202653, bake/review-data-20260712-073843 — stale, safe to delete) stop accumulating.
VERIFIED-NEEDED: the "Allow GitHub Actions to create and approve pull requests" setting is repo-console-only (Settings → Actions), owner-held; agents hold no path to it. Failure verified by event type from both runs' logs 2026-07-12 (ORDER 012); exact error string quoted above.
```

### Satisfied ask — kept verbatim (Decided row O, satisfied by 2026-07-18)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-18 (Decided row O; kept for the record)
ID: ASK-0007
WHAT: Mint a fine-grained GitHub PAT with Contents read AND write scoped to menno420/websites ONLY, and paste it as GITHUB_TOKEN on the control-plane + botsite Railway services.
WHERE: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token (Repository access: Only select repositories → menno420/websites; Permissions → Contents: Read and write); then railway.app → project superbot-websites → services control-plane and botsite → Variables → GITHUB_TOKEN.
HOW: generate the token, copy it once, replace the GITHUB_TOKEN value on both services (the value never goes in the repo). The writeback engine reads the env at REQUEST time, so the capability lights up on the next submit/retry with no redeploy needed beyond Railway's automatic one.
WHY-IT-MATTERS: the owner writeback console (/owner/queue, ORDER 020) currently QUEUES submissions instead of committing them — the deployed token is read-scoped, so every mark-complete / request-assistance / note is stored locally with an honest "write token not available — queued" error, and Railway's ephemeral disk loses queued entries on redeploy.
UNBLOCKS: console writeback commits land in git — assistance requests append real ORDERs to control/inbox.md and completions/notes append to docs/owner/owner-notes.md — so the fleet actually sees and acts on what you write on the site.
VERIFIED-NEEDED: submit a note on /owner/queue (reachable from /queue) and see a commit SHA link in the banner and audit log instead of "queued". Deliberately not attempted by agents: PAT minting is owner-held (no agent credential exists) and Railway variable mutations are policy-walled (docs/RAILWAY-SAFETY.md — same wall as the standing asks above).
```

> **Satisfaction note (2026-07-18):** verified live end-to-end — a real
> `/owner/queue` note POST on the deployed control-plane committed to branch
> `claude/owner-writeback-1` (`0be58459`), opened auto-PR **#399**, went
> quality-green and auto-merged to `main` as **`b12dcd9`**. Crucially the
> deployed control-plane `GITHUB_TOKEN` **already** held BOTH `contents:write`
> AND `pull-requests:write`, so the paste/overwrite this ask asked for was
> **not needed** — the capability was already live. The writeback now lands via
> a branch + auto-merging PR (Q2=b owner-confirmed, PR #398), not a direct
> Contents-API PUT to `main`, so the PR-write scope is load-bearing (the
> runtime opens the PR itself). ASK-0008's PAT-scope half is therefore also
> already covered on the Railway `GITHUB_TOKEN`; only its `BAKE_PAT` Actions
> secret half remains open.

### Satisfied ask — kept verbatim (Decided row P, satisfied by 2026-07-18)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-18 (Decided row P; kept for the record)
ID: ASK-0010
WHAT: Publish the GitHub Release lumen-drift-v1.3 in menno420/gba-homebrew — the one owner click between the finished GBA ROM and a public download.
WHERE: github.com/menno420/gba-homebrew → Releases → draft/publish the lumen-drift-v1.3 release (attach the built ROM).
HOW: one click on the release page. Afterwards say the word (or any session's healthcheck will notice): a session then records the release's download URL in botsite/data/arcade.json (availability → download, url set, blocker dropped) and the arcade card gains its real Download button.
WHY-IT-MATTERS: the public arcade has promised this game since PR #349 — /arcade/lumen-drift renders this exact click as its "What's blocking launch" panel. A finished, publish-safe game the public page names but nobody can download is the longest-standing visible gap on the arcade.
UNBLOCKS: the Lumen Drift card and detail page flip from blocker panel to a real Download button; the owner-console verification chip for this row flips to done-detected on its own.
VERIFIED-NEEDED: machine-checked already — app/askverify.py probe lumen-drift-release GETs /repos/menno420/gba-homebrew/releases/tags/lumen-drift-v1.3 (200 = done, 404 = still open; still 404 at filing). Publishing a release on gba-homebrew is owner-held: no agent credential for that repo exists (write access unverified, deliberately not attempted — same wall class as the PAT asks above).
```

### Satisfied ask — kept verbatim (Decided row Q, satisfied by 2026-07-18)

```markdown
⚑ OWNER-ACTION — SATISFIED 2026-07-18 (Decided row Q; kept for the record)
ID: ASK-0011
WHAT: In menno420/product-forge, set Settings → Pages → Source to GitHub Actions, so the existing games-web deploy workflow can publish the site.
WHERE: github.com/menno420/product-forge → Settings → Pages → Build and deployment → Source: GitHub Actions.
HOW: one settings click, Save. The already-committed deploy workflow then publishes on its next run; once the site's URL answers 200, a session records it in botsite/data/arcade.json (availability → live, url set, blocker dropped).
WHY-IT-MATTERS: /arcade/games-web has rendered this exact click as its "What's blocking launch" panel since PR #349 — the deploy workflow exists but its documented URL returns 404 until Pages has a source, so the public card honestly says unavailable.
UNBLOCKS: the games-web card and detail page flip from blocker panel to a real Play link; the owner-console verification chip for this row flips to done-detected on its own.
VERIFIED-NEEDED: machine-checked already — app/askverify.py probe product-forge-pages GETs /repos/menno420/product-forge/pages (200 = configured, 404 = still open; unreadable-with-this-token = honest unknown, never inferred). Repository settings are owner-held — no agent credential can flip Pages source (deliberately not attempted).
```

## How to use this doc

- New owner-gated fork → add a row to **Open** with where it lives.
- The owner also writes back directly from the site (ORDER 020): completion
  assertions and notes land in [owner-notes.md](owner-notes.md) — read it
  each session and reconcile completions into this ledger.
- Owner decides → move it to **Decided / resolved** with the decision + a
  provenance pointer (a `[D-NNNN]`, a `Q-NNNN`, or a dated verification).
- Keep it short. Detail belongs in the linked decision/plan/router, not here.
