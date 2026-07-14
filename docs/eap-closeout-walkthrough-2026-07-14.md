# websites — EAP close-out walkthrough (2026-07-14)

> **Status:** `audit`
>
> The ORDER 030 (b) close-out walkthrough (`control/inbox.md` @ `a17de3b`),
> written for the owner's end-of-EAP review of this seat: what shipped, how to
> verify it, every click waiting on you, a 5-minute live tour, and the
> handoff. A dated snapshot — source files and `docs/current-state.md` win
> over anything here if they disagree. Depth lives in the close-out audit:
> [eap-project-audit-2026-07-14.md](audits/eap-project-audit-2026-07-14.md).

## A. What this seat did during the EAP

Six calendar days (2026-07-09 → 07-14): **353 commits on main, 332 PRs opened
/ 316 merged, 201 session cards, 1414 tests** across four suites (measured in
the [close-out audit §1](audits/eap-project-audit-2026-07-14.md) — read that
doc for tooling verdicts, walls with verbatim denials, friction numbers, and
the ranked wishlist). Highlights, PR-cited:

- **Four independent FastAPI services, all built here and LIVE on Railway**
  (shared code, never a shared process): **control-plane** (#2 — readiness
  board, journal browser, fleet heartbeats `/fleet`, `/orders`, `/queue`,
  activity + Atom feed), **botsite** (#7 — public marketing/reference site),
  **dashboard** (#8 — read-only bot inventory; `/admin` a deliberate dry-run
  stub), **review** (#141 expansion — the program-review site for Anthropic
  reviewers: process/growth/successes/problems, fleet index, review editions
  + Atom feed, evidence-backed questionnaire).
- **Quality gate, CI-permanent:** the required `quality` check (owner ruleset,
  verified on #18) runs all four suites + the kit gate; the born-red
  session-gate leak was closed by adopting kit v1.0.0 (the born-red-gate
  decision, stamped in `docs/decisions.md`) and the
  control fast lane's measured false-green closed by #314; the clarity bar
  walks 123 concrete routes in CI (#241).
- **Bake pipeline proven end-to-end:** scheduled `review-bake` regenerates the
  review site's data mirrors daily — first scheduled SUCCESS 2026-07-13 (data
  PRs #259/#270; graveyard refresh + dispatch-chained quality #269). Durable
  hands-off landing awaits the BAKE_PAT click (section C row 8).
- **Tester program** on botsite `/testing` (ORDER 018): claims/submissions/
  payout ledger, AI exit-review, owner queue, export valve + import valve
  (#320) with referential integrity (#323).
- **Owner console:** `/owner/briefing` morning briefing (#273), `/projects`
  launch console (#158), owner writeback (#183/#189), environments hub
  (#202/#203), control-plane IA v2 (5-category navigation).
- **Fleet prompt library** `/prompts` — all seat paste artifacts rendered
  live, current-files-first (ORDER 014; restructured by #267).
- **Standing verification:** post-deploy healthcheck (#19), scheduled
  browser-level smoke-crawl (#321), deploy-drift board row + `/version` on
  every service (ORDER 001).

## B. Current state + how to run/verify

Main is green; all four services deploy from `main` automatically (merge =
deploy). Living ledger: `docs/current-state.md`. Run before every push, and
to verify any of this yourself:

```bash
# Full four-service test suite (baseline ~1414 collected)
python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q

# Kit gate: docs hygiene (badges/links/reachability) + session-log markers
python3 bootstrap.py check --strict

# Post-deploy healthcheck: /healthz + / on the four live services,
# registry live-parse, arcade URL drift, tester-task liveness (no args)
python3 scripts/healthcheck.py

# Browser-level smoke-crawl: headless Chromium over the public pages,
# desktop + mobile viewports; console errors / non-200s / broken links fail
python3 scripts/smoke_crawl.py [--max-pages N] [--deadline SECONDS]
```

Note on the smoke-crawl: in the agent container it needs
`--executable-path`/`--proxy-server` overrides (the egress proxy resets a
TLS 1.3 ClientHello — header of `scripts/smoke_crawl.py`); on GitHub Actions
runners and normal machines it runs plain as quoted.

## C. Owner actions checklist

Everything below waits on you. Source of truth (full six-field blocks, kept
current): [docs/owner/OWNER-ACTIONS.md](owner/OWNER-ACTIONS.md) — 9 pending
⚑ asks, rendered compactly here. Risk key: ✅ inert · ↩️ reversible · ⚠ gate
decision / arms a credential.

| # | Click / decision | Where | Recommendation | Verify | Risk |
|---|---|---|---|---|---|
| 1 | Answer **Q-0004** — where does live bot control live (websites / superbot / superbot-next / stay dry-run)? | `docs/question-router.md` (Q-0004); judge the dry-run panel at the dashboard's `/admin` | **One sentence is enough; "stay dry-run" is the safe default** — this is THE gate for rows 2–3 | "Maintainer answer" slot filled in `docs/question-router.md` | ⚠ |
| 2 | Create the **Discord OAuth app** for the future armed control panel | discord.com/developers/applications → New Application → OAuth2 | **Defer until Q-0004 is answered** — creds go ONLY into the future armed service env, never the dashboard | App exists with redirect `https://<armed-service-url>/auth/callback`; dashboard still credential-free | ⚠ |
| 3 | Provision the **armed Railway service + scoped control-API token** | railway.app → superbot-websites → New → Service; token minted on superbot's control-api seam | **Defer until rows 1–2 exist** — the credential boundary (dashboard gets NOTHING) is the whole design | New service env per `docs/specs/bot-control-api-v1.md` §9; dashboard variables untouched | ⚠ |
| 4 | Create the **botsite submissions PostgreSQL** + paste `DATABASE_URL` | railway.app → superbot-websites → New → Database → PostgreSQL; then service botsite → Variables | **Do it — one database, two payoffs**: unblocks `/submit` AND durable tester-program storage (today SQLite on ephemeral disk, wiped each redeploy) | `DATABASE_URL` present on botsite; `/owner/environments` badge flips `set-live` | ↩️ |
| 5 | Set up **PayPal Payouts** + paste `PAYPAL_CLIENT_ID`/`PAYPAL_CLIENT_SECRET` on botsite | developer.paypal.com → Apps & Credentials → Live → Create App (Payouts enabled); railway.app → botsite → Variables | **Start early — Payouts approval can take days**; auto-pay stays OFF regardless until you also set `TESTING_AUTOPAY_ENABLED=true` | Both variables present; payout module stays dry-run until the kill switch flips | ↩️ |
| 6 | Set **`SITE_PASSWORD` on the botsite service** so the tester-program owner queue opens | railway.app → superbot-websites → service botsite → Variables → New Variable | **Do this first — the highest-leverage single paste** (`control/status.md` names it): every tester claim/submission waits behind it | `<botsite-url>/testing/owner` prompts Basic auth and returns 200 instead of 503 | ↩️ |
| 7 | Mint the **ORDER 020 fine-grained PAT** (menno420/websites, Contents: read+write) → `GITHUB_TOKEN` on control-plane + botsite | GitHub → Settings → Developer settings → Fine-grained tokens; then railway.app → both services → Variables | **Mint it as row 8's dual-scope token — one PAT, two scopes, three paste targets** | Submit a note on `/owner/queue` → banner shows a commit-SHA link instead of "queued" | ↩️ |
| 8 | **BAKE_PAT** — same PAT with Pull requests: read+write added, stored as a websites Actions secret named `BAKE_PAT` | github.com/menno420/websites → Settings → Secrets and variables → Actions → New repository secret | **The durable fix for parked nightly bake PRs** — a session then flips review-bake's `GH_TOKEN` to it (explicit fallback keeps today's behavior if revoked) | The next scheduled bake PR shows a `pull_request`-event quality run and auto-merges | ↩️ |
| 9 | **Delete the unused `SITE_PASSWORD`** from the dashboard service (set-but-unused drift) | railway.app → superbot-websites → service dashboard → Variables → SITE_PASSWORD → delete | **Delete — inert**: zero readers in dashboard code (`docs/dashboard.md:127`) | Next names-only env read / `/owner/environments` dashboard group no longer lists it | ✅ |

PR clicks and cross-references:

- **PR [#324](https://github.com/menno420/websites/pull/324)** — parked green
  by design (its own rail labels workflow-touching PRs do-not-automerge);
  owner-click decision: merge or close. **Recommend: merge** — owner-click
  merge is its designed landing path. Verify: the automerge-race carve-out
  rail is active on the next workflow-touching PR.
- **7 draft lifeboat PRs
  [#245](https://github.com/menno420/websites/pull/245) /
  [#249](https://github.com/menno420/websites/pull/249) /
  [#257](https://github.com/menno420/websites/pull/257) /
  [#278](https://github.com/menno420/websites/pull/278) /
  [#279](https://github.com/menno420/websites/pull/279) /
  [#280](https://github.com/menno420/websites/pull/280) /
  [#300](https://github.com/menno420/websites/pull/300)** — owner-click
  disposal; all marked safe-to-close by their own bodies (session-card +
  kit-state churn parked off-checkout, nothing valuable inside).
  **Recommend: close all seven.** Verify: open-PR list shrinks to live work.
- **PR [#281](https://github.com/menno420/websites/pull/281)** (coordinator
  session) — flips at its own ender; no action.
- **ORDERs 020 / 021** — owner-gated, NOT duplicated here: ORDER 020 is
  checklist **row 7** (+ row 8's dual-scope framing); ORDER 021 is
  **rows 1–2** (Q-0004 + Discord OAuth).
- **PR #334** — being resolved this session — see the close-out report.
- **PR #330** — being resolved this session — see the close-out report.

## D. 5-minute verify-it-yourself tour

- **control-plane** — <https://control-plane-production-abb0.up.railway.app>
  — the readiness board (deploy-drift row: all four services `in sync`), then
  `/fleet` (live lane heartbeats) and `/queue` (your ⚑ asks rendered).
- **botsite** — <https://botsite-production-cfd7.up.railway.app> — the public
  bot site; `/commands` (live from superbot's committed data) and `/testing`
  (the tester program; the owner queue behind row 6's password).
- **dashboard** — <https://dashboard-production-a91b.up.railway.app> — the
  read-only bot inventory; `/admin` is the honest dry-run control panel
  awaiting Q-0004.
- **review** — <https://review-production-f027.up.railway.app> — built for
  reviewers: `/process`, `/growth` (charts from real git history),
  `/problems` (as specific as the successes), `/questionnaire` (every answer
  cited).

## E. Handoff notes

- **Work sources for the next phase:** `control/inbox.md` orders first;
  standing rung-3 source is `docs/ideas/backlog.md` (~33 captured bullets
  open at the close-out audit); `docs/current-state.md` is the living ledger
  to keep true.
- **Batons in flight at close-out:** PRs #334 (ORDER 028) and #330 (bake
  data) being resolved this session; heartbeat `control/status.md` truing +
  the smoke-crawl first-fire re-verify are sibling ORDER 030 (a) items;
  coordinator #281 flips at its own ender.
- **What the next phase needs from the owner:** section C — rows 6/4/7+8 are
  the highest-leverage pastes (tester queue reachable, durable storage,
  writeback + hands-off bake); rows 1–3 are the one product decision
  (Q-0004) and its downstream provisioning; #324 merge-or-close and the
  seven lifeboat closes empty the open-PR list.
- **What the next phase needs from agents:** flip `review-bake.yml` to
  `BAKE_PAT` once row 8 lands; build the `/submit` + tester-program Postgres
  path once row 4 lands; keep the claims ledger + heartbeat rituals
  (`control/claims/README.md`, `control/README.md`) — they are what kept 300+
  auto-merged PRs from colliding.
