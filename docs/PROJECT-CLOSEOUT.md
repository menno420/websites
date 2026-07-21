# Project Closeout — websites

> **Status:** `reference`
>
> Final closeout of the autonomous agent build period for the websites project. Written for two cold readers: the owner, and a future Claude session opening this repo fresh. Everything here is cited to a PR or commit; anything not independently verified is marked so.

This repo — **websites** — is the owner's launch console and fleet arcade: four independent server-rendered FastAPI services (Python 3.12, Jinja2 + httpx) in one repo, each with its own Dockerfile and Railway service. Merge to `main` deploys. The four services:

- **control-plane** (`app/`) — the owner console + environments hub.
- **botsite** (`botsite/`) — the public arcade, game submission intake, and tester queue.
- **dashboard** (`dashboard/`) — fleet status + admin surface.
- **review** (`review/`) — the review/editions site over committed JSON data.

## What was accomplished

Over the build period, autonomous agent sessions took the repo from scaffold to four live, test-covered, self-landing services. The major shipped pieces:

- **Quality gate + auto-merge landing system** — a single required `quality` check (fast lane + inbox gate + born-red card HOLD + four pytest suites, all riding inside `bootstrap.py`), with an enabler that arms `claude/*` PRs at open and self-lands them green; workflow-file diffs are carved out to owner merge. This is the machinery every PR below rode in on. (See `.github/workflows/quality.yml` + `bootstrap.py`.)
- **Fleet-wide Discord owner login** — one Discord OAuth owner login shared across all three web services: control-plane [#426](https://github.com/menno420/websites/pull/426), botsite [#442](https://github.com/menno420/websites/pull/442), dashboard [#443](https://github.com/menno420/websites/pull/443), with a drift guard over the vendored copies [#445](https://github.com/menno420/websites/pull/445).
- **Postgres persistence for submissions and tester queue** — durable `/submit` intake on Postgres [#425](https://github.com/menno420/websites/pull/425), `/testing` store moved to a dual SQLite/Postgres backend [#446](https://github.com/menno420/websites/pull/446), a shared `botsite/_db.py` shim extracted [#447](https://github.com/menno420/websites/pull/447), and `submissions_store` routed onto it [#449](https://github.com/menno420/websites/pull/449).
- **Hands-off nightly review bake** — the review data bake runs unattended under a dedicated `BAKE_PAT`: landing step wired [#434](https://github.com/menno420/websites/pull/434), proven by a bot-authored bake commit [#438](https://github.com/menno420/websites/pull/438).
- **Arcade catalog with verified Download/Play + detail pages** — arcade flipped live with a real Lumen Drift download [#428](https://github.com/menno420/websites/pull/428), registry/label sync [#435](https://github.com/menno420/websites/pull/435), catalog grown with verified fleet games [#464](https://github.com/menno420/websites/pull/464), and richer per-game detail pages [#470](https://github.com/menno420/websites/pull/470).
- **Review edition auto-drafter + edition-002** — `review/gen_edition.py` drafts editions and edition-002 shipped [#463](https://github.com/menno420/websites/pull/463).
- **Guardrails across services** — NAV-completeness guard for review [#416](https://github.com/menno420/websites/pull/416) and its botsite/dashboard siblings [#418](https://github.com/menno420/websites/pull/418), NAV reachability GET guard for control-plane [#450](https://github.com/menno420/websites/pull/450), and an auto-discovering vendored-copy AST guard [#454](https://github.com/menno420/websites/pull/454).
- **Self-checking owner-action chips** — the `askverify` panel grew from 6 to 8 self-probing signals [#451](https://github.com/menno420/websites/pull/451), backed by a committed signal registry [#453](https://github.com/menno420/websites/pull/453).
- **Owner surface polish** — a cross-service fleet nav strip on all four sites [#466](https://github.com/menno420/websites/pull/466), an inline "your open actions" panel on the owner home [#467](https://github.com/menno420/websites/pull/467), and a submitter status lookup by opaque ref [#469](https://github.com/menno420/websites/pull/469).
- **Records + orientation overhaul** — current-state refreshed [#458](https://github.com/menno420/websites/pull/458) and the seat-digest render regenerated [#459](https://github.com/menno420/websites/pull/459).

## Current true state (verified live at write time)

- **HEAD:** `97c44a9` (#471), tree clean, no open claims.
- **Tests:** full four-suite run = **2185 passed** (`tests/ botsite/tests dashboard/tests review/tests`). `bootstrap.py check --strict` = green (only never-exit-affecting advisory notices on `docs/CAPABILITIES.md`).
- **Live services** — every probed endpoint returned HTTP 200:
  - control-plane `/healthz`, `/` — 200
  - botsite `/healthz`, `/arcade`, `/submit`, `/testing` — 200
  - dashboard `/healthz`, `/status` — 200
  - review `/healthz`, `/`, `/reviews`, `/releases.json` — 200
- **Owner asks:** 10 remain open in `docs/owner/OWNER-ACTIONS.md` — all are product/credential decisions the owner must make; the code side of each is already landed and waiting.

## Continuation — open threads, in priority order

Each item names the exact resume step. Full detail lives in `docs/owner/OWNER-ACTIONS.md` and `docs/NEXT-TASKS.md`.

1. **Owner Discord sitting (quickest, unblocks the most).** control-plane login is already live. botsite (ASK-0006) and dashboard (ASK-0017) still need the four Discord OAuth vars set on their Railway services: `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `OWNER_DISCORD_ID`, `OWNER_SESSION_SECRET`, plus the redirect URI registered in the Discord app. Redirect URIs: botsite `https://botsite-production-cfd7.up.railway.app/owner/auth/callback`, dashboard `https://dashboard-production-a91b.up.railway.app/admin/auth/callback`. Setting them unlocks the botsite `/submit` moderation queue + `/testing` owner reads and the dashboard admin surface. (A simpler alternative for dashboard only: set `SITE_PASSWORD` — but Discord is the unified path.)
2. **review-bake cron wiring.** `review-bake.yml` should also run `gen_releases` + `gen_edition` on its schedule so releases and edition drafts refresh unattended. This is a workflow-file diff → carries the do-not-automerge carve-out → owner merges it in the hub venue.
3. **Arcade detail screenshots.** [#470](https://github.com/menno420/websites/pull/470) shipped optional screenshot/controls/changelog support on game detail pages; the screenshot assets themselves aren't provided yet. Drop images into the arcade data and they render.
4. **The gated ladder (owner input required, no seat work possible until then).** ASK-0005 (PayPal Payouts creds), ASK-0012 (Gumroad publish pass — 10 titles), ASK-0013 (full-res photo originals), ASK-0014 (pick Ultramarine title), ASK-0015 (§5 illustration money-gate), ASK-0016 (Dutch proofread), ASK-0003 (scoped control-API token + separate armed Railway service), ASK-0009 (delete the unused dashboard `SITE_PASSWORD`).
5. **Site consolidation.** `docs/plans/site-consolidation-cutover.md` retires the duplicate `reliable-grace` sites — gated on an explicit owner go, not to be started otherwise.

## Owner walkthrough — every valuable artifact

The four live sites, what each is for, and how to use it:

- **Owner console + environments hub** — https://control-plane-production-abb0.up.railway.app — your launch console. Owner login is live via Discord (`/owner/login`). The `/owner` home shows an "your open actions" panel summarizing what's waiting on you.
- **Arcade + submissions** — https://botsite-production-cfd7.up.railway.app — the public arcade (`/arcade`) with verified Download/Play and per-game detail pages; `/submit` takes game submissions (durable on Postgres); `/testing` is the tester queue; submitters check status by ref at `/submit/status/{ref}`. Owner moderation/reads unlock once the Discord vars are set (ASK-0006).
- **Fleet dashboard** — https://dashboard-production-a91b.up.railway.app — fleet `/status` and an admin surface (`/admin`, Discord-gated once ASK-0017 vars are set).
- **Review site** — https://review-production-fc91.up.railway.app — the review/editions site: `/` home, `/reviews` (editions incl. edition-002 + Atom feed), `/questions`, and machine-readable `/releases.json`.

**Owner checklist (quickest first):**
1. Set the four Discord vars + redirect URI on the **botsite** and **dashboard** Railway services (ASK-0006, ASK-0017) — unlocks the moderation queue, tester reads, and admin surface.
2. (Optional, dashboard only) set `SITE_PASSWORD` as a simpler alternative to Discord for the dashboard admin.
3. Content-gated items when you're ready: Gumroad publish (ASK-0012), Ultramarine title (ASK-0014), photo originals (ASK-0013), Dutch proofread (ASK-0016), PayPal payouts (ASK-0005).

## Working this repo with a fresh session

- **Boot route:** `.claude/CLAUDE.md` → `HANDOFF.md` (untracked, regenerated per session) → `docs/current-state.md`. Then route on demand into `docs/AGENT_ORIENTATION.md`, `docs/SKILLS.md`, `docs/CAPABILITIES.md`. There is no `docs/README.md` index by design.
- **Verify a change** (run before every push — unset `DATABASE_URL` first; the sandbox exports a dead one that forces the psycopg path and reds botsite DB tests):
  ```
  env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q
  env -u DATABASE_URL python3 bootstrap.py check --strict
  ```
- **How PRs land:** branch `claude/<slug>`; open READY (never draft). First commit is a born-red session card (`.sessions/YYYY-MM-DD-<slug>.md`) carrying all four markers (`Status`, `📊 Model`, `💡 idea`, `⟲ Previous-session review`) and a valid PL-004 task-class, with `Status: in-progress` holding the PR red. `quality` is the one required check. Flip `Status` to `complete` and delete your own claim in the LAST commit to release the landing workflow; green head SHA self-merges. Workflow-file (`.github/workflows/**`) diffs carry a do-not-automerge carve-out → owner merges those in the hub venue.
- **Gotchas:** stage named paths only (never `git add -A` — it sweeps in machinery); claim files in `control/claims/` are deleted in the flip commit; a control-only diff takes the fast lane (no card); `bootstrap.py` (~12k lines) and `.substrate/` are kit machinery, exclude them from repo-wide searches; MCP PR reads can lag ~25 min, so cross-check live GitHub before declaring a merge.
