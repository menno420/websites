# Rework `dashboard/` + `botsite/` into `websites`

> **PLAN ONLY — no implementation in this PR; rework begins only after owner review.**
>
> **Status:** `plan` — awaiting owner review (2026-07-09). Ledger: [D-0007].
> Provenance: `menno420/superbot` `docs/planning/websites-project-kickoff-2026-07-09.md`
> sequence step 3 (the deferred, plan-first phase).

This is sequence step 3 of the websites kickoff: rework superbot's two existing
web properties — `dashboard/` and `botsite/`, both living inside
`menno420/superbot` — into this repo, on the substrate the control-plane site
already established. Same relationship `superbot-next` has to `superbot`: **keep
the ideas and functionality, rebuild the implementation.** The existing sites
keep running untouched in superbot until their replacements are ready and cut
over — this plan touches nothing live.

Everything below is grounded in the real source read on 2026-07-09; file paths
are cited so the owner can trust it's read, not guessed.

---

## 1. What each existing site does today

### 1a. `dashboard/` — the developer dashboard + control panel

**Purpose.** A personal, owner-facing developer dashboard for SuperBot, plus a
free multi-user Discord-OAuth control panel, plus the moderation home for the
public site's submissions. Runs as a **second Railway service** in superbot's
production project.

**Stack.** FastAPI + Jinja2, server-rendered, no build step. Deps
(`dashboard/requirements.txt`): `fastapi`, `jinja2`, `httpx`, `uvicorn` — plus a
`sys.path` shim in `dashboard/app.py` so sibling modules import whether it runs
as a package or as Railway's `app:app`. Start command `dashboard/Procfile`
(`uvicorn app:app`). ~24 Jinja templates under `dashboard/templates/`.

**Key routes / features** (from `dashboard/README.md` + `dashboard/app.py`):

| Surface | What | Source module |
|---|---|---|
| `/` `/functions` `/commands` `/aliases` `/settings` `/access` `/ideas` `/bugs` `/updates` `/env` | Read-only catalogues: bot-function registry, cog/command explorer, alias collision-checker, settings-key catalogue, visibility/access ladder, idea backlog, bug board, updates feed, env-var usage map (names + code locations only, never values) | templates + generated `dashboard/data/dashboard.json` |
| `/admin` + `/auth/*` | Discord-OAuth control panel: sign in, pick a guild you administer, edit settings / help appearance / cog enable-disable — applied **live** via the bot's control API | `dashboard/auth.py`, `dashboard/control_client.py`, `dashboard/websession.py` |
| `/admin/moderation` | Owner-gated (`BOT_OWNER_USER_ID`) moderation of public `/submit` submissions; on approve, mirrors to a GitHub issue | `dashboard/submissions_db.py`, `dashboard/github_mirror.py` |
| `/healthz` | Railway liveness probe | app constant |

**Data source (the decoupling hard rule).** The app **never imports `disbot/`**.
Read-only pages render the committed `dashboard/data/dashboard.json`, produced by
`scripts/export_dashboard_data.py` (pure stdlib, in the superbot repo root, which
statically scans bot source via `scripts/scan_*.py`). The bot's Railway service
and this one are fully independent.

**Auth / secrets.** Read-only MVP needs **no** env vars. The control panel is
**dormant by default** — it lights up only when its OAuth + control-API vars are
set (`DISCORD_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI`, `DASHBOARD_SESSION_SECRET`,
`CONTROL_API_TOKEN`). Session is a stdlib HMAC-signed cookie (`websession.py`);
abuse-brakes are per-process sliding-window limiters (`dashboard/ratelimit.py`).
The moderation ring holds the two real secrets: the submissions DB DSN and the
`GITHUB_ISSUE_MIRROR_TOKEN` (fine-grained PAT). Identity is always re-checked by
the bot on every write — the browser's claim is never trusted alone.

**Deploy.** Railway service, **Root Directory = `dashboard`**, so Railway builds
only `dashboard/requirements.txt` and runs `dashboard/Procfile`; redeploys on push
to `main`. Intentionally no `static/` dir (root `.gitignore` ignores it); styling
is Tailwind CDN + an inline block in `base.html`.

### 1b. `botsite/` — the public marketing + reference site

**Purpose.** The public marketing + reference website for SuperBot (Home /
Features / Commands / Games / Changelog / Status), plus a public bug/suggestion
`/submit` intake. Its own Railway service, separate from both the bot and the
dashboard.

**Stack.** FastAPI (`botsite/app.py`) is the **single owner of routing**; front
end is a **no-build vanilla-JS, hash-routed SPA** (`botsite/site/`). Deps
(`botsite/requirements.txt`): `fastapi`, `uvicorn`, `jinja2`, `asyncpg` —
deliberately **no** httpx/OAuth/itsdangerous (public secret-free surface). Same
`sys.path` shim + `Procfile` recipe as the dashboard.

**Three estates layered in one app:**

- **v1 SPA** (`botsite/site/index.html` / `app.js` / `app.css`) — **design-owned,
  copied verbatim** from the Claude-Design handoff, do-not-edit. The only file
  botsite owns is `botsite/site/data.js`, **generated** (never hand-written) from
  `botsite/data/site.json` via `botsite/site_data.py`, and served live at
  `/data.js`. Legacy server-rendered Jinja pages (`botsite/templates/*.html`)
  stay wired as a no-JS fallback.
- **v2 estate** (2026-07-07): `botsite/ds/` — the **program design system**
  (`tokens.css`, `components.css`, `ds.js`; living styleguide at `/design`);
  `botsite/site/v2/` — the v2 public site (43-feature catalogue, command palette,
  real light theme), reachable at `/v2`, promoted to `/` only when
  `BOTSITE_FRONTEND=v2` is set (rollback = unset); `botsite/console/` — the
  owner's one-glance program console at `/console`, fed by committed
  `botsite/data/console.json`.

**Key routes** (from `botsite/app.py` + `botsite/README.md`): `/` (SPA shell),
`/data.js` (live-generated data layer), `/commands` `/features` `/changelog`
`/status` (legacy Jinja fallback), `/submit` (public intake → one `pending` row),
`/v2`, `/design`, `/console`, `/healthz`.

**Data source (same decoupling rule).** Never imports `disbot/`. Reads only the
committed public subset `botsite/data/site.json` — produced by the *same*
`scripts/export_dashboard_data.py --targets site`, and **redaction by
construction**: a top-level whitelist a CI guard enforces, so dev-only families
(env, settings, access, ideas, raw bugs) physically cannot appear. Core inherited
principle: **never fake data — a missing feed renders as a declared pending
lane.**

**Auth / secrets.** Public, secret-free. Holds **at most one** secret — the
INSERT-only `SUBMISSIONS_DB_DSN` used by `/submit` to write one pending row into
the *dashboard-owned* submissions Postgres (`botsite/submissions_db.py`,
`botsite/migrations/001_submissions.sql`). The README is explicit that the future
gated control panel must be a **separate service, not a router mounted here**, so
a marketing-surface compromise can never reach the control-API/mirror tokens.

**Deploy.** Railway service, **Root Directory = `botsite`**; dark-launched on the
Railway URL, custom domains deferred to cutover. Same no-`static/` rule.

---

## 2. Carry over vs. rebuild — per site

Philosophy mirror: **ideas & functionality carry; implementation gets rebuilt on
this repo's substrate** (FastAPI + Jinja2 + httpx, the `ds/` design system, the
live-GitHub data layer the control-plane app already proved).

### 2a. `dashboard/`

| Feature / idea | Disposition | Notes |
|---|---|---|
| Read-only catalogues (functions, commands, settings, access, env-map, ideas, bugs, updates) | **Carry idea, rebuild impl** | The *pages* are the point. Rebuild them reading a **data feed** rather than scanning `disbot/` locally (see §3 data layer + open Q7) — websites has no `disbot/` to scan. |
| "Never import `disbot/`; read generated JSON" decoupling | **Carry as-is** | Already how the control-plane app works (reads GitHub live). Preserve as a hard rule. |
| Env-var usage map — names + locations only, never values | **Carry as-is** | Secret-safety invariant; keep verbatim. |
| Alias collision-checker (`/aliases`) | **Carry idea, rebuild impl** | Client-side, no backend — cheap to rebuild; depends on the command/synonym feed. |
| Discord-OAuth multi-user control panel (`/admin`) writing the bot's control API | **Rebuild — but gated on open Q4** | This couples websites to the *running production bot* (`disbot/control_api.py` over Railway private net). That coupling crosses the repo boundary and may belong with `superbot-next`, not here. **Do not port without an owner call.** |
| Submissions moderation (`/admin/moderation` + GitHub-issue mirror) | **Rebuild — gated on open Q5** | Needs a Postgres + the mirror PAT in the new Railway project; paired with botsite `/submit`. Carry the *flow*, re-provision the infra. |
| Tailwind-CDN + inline styling | **Drop / replace** | Rebuild on the `ds/` design system (tokens + components) for one consistent look across all websites surfaces. |
| Per-process rate-limiters, HMAC cookie session | **Rebuild if the control panel is carried** | Only needed if Q4 says the control panel comes over. |

### 2b. `botsite/`

| Feature / idea | Disposition | Notes |
|---|---|---|
| Public marketing/reference pages (Home/Features/Commands/Games/Changelog/Status) | **Carry idea, rebuild impl** | The public face is the whole point; rebuild on the shared substrate. |
| The `ds/` program design system (`tokens.css`, `components.css`, `ds.js`, `/design` styleguide) | **Carry as-is (promote to shared)** | This is the most reusable asset. Lift it into a repo-shared package so control-plane, dashboard, and botsite all render as one system. |
| v2 site (`site/v2/` — 43-feature catalogue, command palette, light theme, honest provenance) | **Carry as the baseline** | v2 is the intended future; rebuild starts from it, not v1. |
| v1 design-owned SPA (`site/index.html`/`app.js`/`app.css`) | **Drop after cutover** | Superseded by v2; keep only as reference. Retire the `BOTSITE_FRONTEND` v1/v2 flag — ship v2 only. |
| Legacy server-rendered Jinja fallback pages | **Drop / merge** | The no-JS fallback is optional; decide whether the rebuild is server-rendered (then the SPA/fallback split disappears) — see fit-alongside §3. |
| Static-JSON export → app only reads; "never fake data / declared pending lanes" | **Carry as-is** | Foundational principle; keep. |
| `/console` owner one-glance program console | **Carry idea — likely merge into control-plane** | This overlaps the control-plane's readiness board + journal browser. Strong merge candidate (open Q3). |
| `/submit` public intake (INSERT-only, one pending row) | **Carry, rebuild impl** | Paired with the dashboard moderation ring (Q5); re-provision the submissions Postgres. |
| "Public, secret-free; control panel is a separate service" invariant | **Carry as-is** | This directly shapes the §3 topology recommendation. |

**Cross-cutting drops/merges:** the v1/v2 duality collapses to one design system;
Tailwind-CDN styling is replaced by `ds/`; `botsite/console/` likely merges into
the control-plane; the two `submissions` halves stay paired but move together.

---

## 3. How they fit alongside the control-plane app

Today this repo is a single FastAPI app (`app/main.py`) with **HTTP Basic auth on
every route via one middleware** (`app/main.py` `auth_gate`), deployed as one
Railway service (`control-plane`) from a root `Dockerfile`. The reworked sites
have **incompatible auth models** with that: botsite is **public** (no auth at
all), the control-plane is **owner-private Basic**, and the dashboard mixes
public-ish read pages, Discord-OAuth, and an owner-gated ring holding real
secrets.

### Recommendation (decide-and-flag)

**One repo, multiple Railway services — not one shared FastAPI process.** Keep the
already-live `control-plane` service as-is; add a **`botsite` service** and (if
carried) a **`dashboard` service**, each its own Dockerfile + `requirements.txt` +
entrypoint, repo-connected to `main`. Share code through an **in-repo Python
package** (design system, GitHub/data helpers, base templates) that each service
imports — share *code*, not a running process.

**One-line rationale:** the botsite README's own core invariant — the public
marketing surface must never share a process with the control-API/mirror secrets —
plus three genuinely different auth models and the fact that superbot already runs
these as three separate Railway services, all point the same way; a single mounted
app would force the public site behind the control-plane's blanket Basic-auth
middleware and co-locate secrets the split exists to isolate.

**Why not mounted sub-apps in one service:** it saves one Railway service at the
cost of re-coupling exactly what the two-site split deliberately separated
(secrets + auth), and it fights the existing global `auth_gate` middleware. Not
worth it.

**Repo layout implication (flag, not a hard commit):** the current root
`Dockerfile` + `app/` assumes one service. Multi-service in one repo wants either
per-service Root Directories (superbot's proven recipe: `services/control_plane/`,
`services/botsite/`, `services/dashboard/`, `shared/`) or per-service Dockerfile
paths. Restructuring the live control-plane is a **later, careful, forward-only**
move — the rework can start by adding a new top-level `botsite/` dir with its own
Dockerfile and leaving `app/` exactly where it is, deferring any control-plane
relayout until it's actually worth doing.

**Auth per surface** (flag — depends on owner intent, open Q1):

| Surface | Recommended auth | Depends on |
|---|---|---|
| control-plane (`/`, `/journal`) | Basic (unchanged) | — |
| botsite public pages | **none — public** | Q1: is botsite public here as it is today? (assumed yes) |
| botsite `/submit` | none (INSERT-only, rate-limited) | Q5 (submissions infra) |
| dashboard read-only catalogues | **open** — public, or Basic like control-plane? | Q1 + Q3 (merge?) |
| dashboard control panel + moderation | Discord-OAuth + owner-gate (as today) | Q4 (carry the panel at all?) |

**Shared templates / static / design layer.** Promote `botsite/ds/` to a repo
`shared/ds/` package; give the control-plane's own templates the option to adopt
it later so everything reads as one system. No `static/` dir issue here (that was
a superbot `.gitignore` quirk; this repo Docker-copies assets explicitly).

**Shared GitHub / data layer.** The control-plane's `app/github.py` (live REST +
raw-content client, TTL cache, per-cell degrade) is the reusable data spine. The
rebuilt dashboard/botsite consume superbot's committed JSON artifacts
(`dashboard/data/dashboard.json`, `botsite/data/site.json`,
`botsite/data/console.json`) via **raw.githubusercontent.com** — the same
token-free public-file path the control-plane already uses — so websites stays
**read-only toward superbot** and forward-only (open Q7 confirms this over
rebuilding the export tooling inside websites).

---

## 4. Migration / deploy approach

**Order: botsite first, dashboard second.** Rationale: botsite is **public**
(simplest auth — none), its data is a clean whitelisted JSON subset, it already
has a finished design system (`ds/`) and a v2 baseline to rebuild from, and it is
the highest-visibility / lowest-risk win. The dashboard carries the hard open
questions (OAuth, control-API coupling to the live bot, a Postgres + mirror PAT,
owner-gating) — it should follow once those are answered and once the shared
substrate botsite establishes is proven.

**Incremental, forward-only, live-sites-untouched.** superbot's `dashboard/` and
`botsite/` services keep running unchanged throughout. Each rebuilt site is built
in this repo, deployed to a **new Railway service in the existing
`superbot-websites` project** (alongside `control-plane`), and **dark-launched on
its Railway URL** for live verification before anything cuts over. Nothing in
superbot is edited by this program.

**Railway shape.** New service per site in `superbot-websites` (project ID
`70198ece-cbc0-484e-86d9-f8a1eca4f045`, per `docs/deployment.md`), each
repo-connected to `menno420/websites@main` so **merge = deploy** (no manual deploy
step). Use `RAILWAY_API_KEY` only and the explicit `superbot-websites` IDs — the
ambient `RAILWAY_PROJECT_ID/SERVICE_ID/ENVIRONMENT_ID` point at the **production
bot** and must never be passed to any Railway call (the standing footgun; the one
hard rail: no destructive Railway mutation anywhere without an explicit owner
go-ahead).

**DNS / domains.** Deferred to cutover, exactly as botsite did originally
(dark-launch on the Railway URL first). Custom-domain assignment and which site
gets the apex is an owner decision (open Q6). No DNS is touched until the owner
approves cutover.

**Rollback thinking.** Because the superbot services stay live and DNS is unchanged
until cutover, rollback at every step before cutover is **free — do nothing**
(the old site is still serving). At cutover, rollback = point DNS back at the
superbot service (kept warm for a defined window). The submissions Postgres (if
carried) migrates with a reversible plan of its own (Q5). No forward step deletes
or edits the live sites.

**Milestone sequence** (each a real, deployed, verifiable checkpoint):

1. Shared substrate: lift `ds/` → `shared/`, add the raw-GitHub data helper. (No new service.)
2. botsite rebuild → new Railway service → dark-launch URL → live verify.
3. (owner go) botsite cutover: DNS + retire v1/console duplication.
4. dashboard rebuild (scope set by Q3/Q4/Q5) → new service → dark-launch → verify.
5. (owner go) dashboard cutover; retire the superbot services.

---

## 5. Open questions for the owner

> Also tracked as Q-blocks in `docs/question-router.md` (Q-0001…Q-0007), where
> each carries its current status and any decision that has since touched it.

Tight list — only the genuine product/intent calls the rework can't make itself:

1. **Public vs. private, per site.** botsite is assumed to stay **public** (as
   today). Are the dashboard's **read-only catalogues** public too, or gated
   behind the control-plane's Basic auth? (The control panel + moderation are
   private regardless.)
2. **Preserve exact visual design, or restyle onto `ds/`?** botsite v1 is
   design-owned Claude-Design files copied verbatim. The rebuild recommendation is
   to standardize on the `ds/` system (and v2 baseline). Confirm that's wanted vs.
   preserving the exact v1 look pixel-for-pixel.
3. **Merge or keep separate?** Three candidates overlap the control-plane's
   owner-oversight job: botsite `/console`, and the dashboard's read-only
   oversight pages (updates/ideas/bugs). Fold them into the control-plane, or keep
   dashboard and botsite as distinct sites?
4. **Does the Discord-OAuth control panel come over at all?** It writes the
   **live production bot's** control API — coupling websites to a running bot
   across the repo boundary. Carry it here, leave it in superbot, or move control
   to `superbot-next`?
5. **Submissions pipeline** (`/submit` → dashboard-owned Postgres → GitHub-issue
   mirror). Carry it? It needs a new Postgres + the mirror PAT provisioned in the
   `superbot-websites` project.
6. **Domain names.** Which custom domains, and which site gets the apex vs. a
   subdomain? (Deferred to cutover, but the target shapes the plan.)
7. **Data feed.** OK to consume superbot's committed JSON artifacts
   (`dashboard.json` / `site.json` / `console.json`) via raw GitHub (clean,
   read-only, forward-only) — or should the `scripts/export_dashboard_data.py`
   scanning tooling be rebuilt inside websites? (Recommendation: consume the
   artifacts.)

---

## Appendix — files read to ground this plan (all read-only)

- superbot: `dashboard/README.md`, `dashboard/app.py`, `dashboard/auth.py`,
  `dashboard/requirements.txt`, `dashboard/Procfile`; `botsite/README.md`,
  `botsite/app.py`, `botsite/requirements.txt`, `botsite/Procfile`; directory
  listings of `dashboard/templates/`, `botsite/site/`, `botsite/ds/`,
  `botsite/console/`, `botsite/data/`.
- websites: `docs/site.md`, `docs/deployment.md`, `docs/decisions.md`,
  `docs/current-state.md`, `app/main.py`, `app/config.py`, `Dockerfile`,
  `requirements.txt`, `.sessions/` convention (`README.md` +
  `2026-07-09-railway-deploy.md`).
