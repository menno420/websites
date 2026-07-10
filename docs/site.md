# Control-plane site (readiness board + journal browser)

> **Status:** `reference` — shipped in PR #2, 2026-07-09. Stack/model provenance: [D-0003], [D-0004].

The owner-facing oversight site: check every repo's working quality and progress
by *looking*, instead of asking an agent to go fetch GitHub state. Two halves:

1. **Readiness board** (`/`) — one row per repo (`superbot`, `superbot-next`,
   `substrate-kit`, `websites`), each signal shown as **configured?** AND
   **working now?**, fetched live from the GitHub REST API:
   ruleset/branch-protection, required checks + the exact check runs on the
   `main` head commit, CODEOWNERS present/enforced, Actions secrets (count
   only — names masked), auto-merge + enabler-workflow presence, open-PR health (count +
   oldest). This generalizes superbot's hand-maintained
   `docs/operations/repo-settings-state.md` ledger into a live view.
   - **Deploy-state drift (websites row only, [D-0018]):** an extra "deploy
     state" cell shows, per websites Railway service (control-plane, botsite,
     dashboard), the **DEPLOYED** commit short-sha vs the `main` HEAD short-sha
     the board already fetches live. Reads `in sync` (deployed == head), `DRIFT`
     (deployed ≠ head, both shown), or `unknown` (fetch failed / sha unset). All
     three services deploy from `main` on merge (Railway auto-deploy), so drift =
     a deploy in progress or a stale/failed deploy. control-plane reads its own
     deployed sha from the environment (no network); botsite/dashboard are read
     over their public `/version` JSON through the TTL cache.
   - **Known trap honored:** superbot-next's `report` job (golden-parity
     workflow) is red-until-parity BY DESIGN — the board badges it
     `red-by-design` (purple) and never counts it toward "broken checks".
   - Any signal the token can't read renders `unknown (reason)` — the board
     degrades per-cell, it never fakes a value.
2. **Activity timeline** (`/activity`, `.json` variant) — recent pull requests
   across **all four repos** (superbot, superbot-next, substrate-kit, websites)
   merged into ONE reverse-chronological stream, each row badged by repo and
   state (`merged` / `open` / `draft` / `closed`) and deep-linked to GitHub.
   Reuses the shared TTL-cached `github.repo_api` layer the board already rides;
   a failing per-repo fetch degrades to an honest banner, never a silent drop.
   ([D-0020]) The same timeline is **subscribable as an Atom 1.0 feed** at
   **`/activity.xml`** (`application/atom+xml`) so a reader or webhook can *watch*
   fleet PR activity instead of polling the page ([D-0025]): a second serializer
   over the exact same TTL-cached list (no second fetch path). `activity.atom_feed`
   maps each dated PR to an `<entry>` (title `repo #num title`, `id` = the PR's
   GitHub URL, `updated` = its real merge/update time, a `link` to GitHub, author,
   a short summary); the feed `updated` is the newest entry's time and its self
   link points back at `/activity.xml`. All text/attributes are escaped by
   `xml.etree.ElementTree` (never hand-concatenated). Honest degradation: a PR
   with no timestamp is omitted (never dated with an invented value), and when the
   fetch fails the feed still validates — one diagnostic `<entry>` noting the
   empty/errored state (clearly-derived generation timestamp), never a malformed
   feed or a fake PR. The `/activity` page advertises it with a
   `<link rel="alternate" type="application/atom+xml">` discovery tag in the head
   and a visible **Subscribe (Atom)** link.
3. **Idea backlog** (`/ideas`, `.json` variant) — the `docs/ideas/` conveyor
   across every repo that keeps one (superbot ~220, substrate-kit ~16; the other
   two only a README). Each idea's title + one-line summary is parsed from the
   file (frontmatter stripped, first `# H1`, then a `**One line:**` marker or the
   first real paragraph); newest ideas per repo are enriched, the rest counted
   with a browse-all link. A repo with no `docs/ideas/` shows an absence, not an
   error. Every idea deep-links to GitHub and to the in-app markdown file view
   (`/journal/{repo}/file`). ([D-0020])
3a. **Fleet heartbeat** (`/fleet`, `.json` variant) — every fleet **lane's**
   `control/status*.md` heartbeat on one glanceable screen ([D-0021], ORDER 002).
   The fleet-coordination protocol has each Project overwrite a `control/status.md`
   in its own repo every session; those committed files are the only visible truth
   of a running agent (the claude.ai UI can't show session activity). `app/fleet.py`
   fetches every lane's status file (shared TTL cache), parses the documented
   `control/README.md` format (heading → project; `key: value` fields where a
   colon *inside* a value never splits a field; `⚑ needs-owner` + the substrate-kit
   `kit:` line handled), classifies `health:` into green / red-by-design (purple —
   never counted broken) / broken / unknown, badges heartbeat freshness **stale**
   past `FLEET_STALE_HOURS` (12h), attaches each repo's last-commit age + open-PR
   count, and renders the full status body as markdown (reusing
   `journal.render_markdown`). Lanes sort **attention-first** (fetch-error → broken
   → stale → absent → red-by-design → healthy). A repo with no status file shows an
   honest absence (not an error — the bare `superbot` lane, whose heartbeat is
   written to superbot-next, is the real case); a fetch failure shows an honest
   banner. The **lane set** is derived **live** from the manager's canonical
   registry `menno420/superbot` → `docs/eap/fleet-manifest.md` ([D-0022]):
   `resolve_lanes` fetches that manifest (same TTL-cached github layer, superbot
   read-only), `parse_manifest` reads its markdown table by header name, and
   `manifest_to_lanes` expands it into lane dicts — the `manager` row (no concrete
   repo) is skipped, the multi-repo SuperBot coordinator becomes a `superbot` +
   `superbot-next` lane, and a repo shared by >1 row (the superbot-games
   cohabitation lanes) reads `control/status-<slug>.md`. A lane **added to the
   manifest auto-appears** here (drift removed). If the manifest can't be
   fetched/parsed the page falls back to the hand-kept `config.FLEET_LANES` and
   shows an **honest "cached fallback list" notice** (never silently pretends it
   was live); `lane_source` in `/fleet.json` reports `manifest` vs `fallback`. A
   manifest lane whose repo the token can't read renders an honest `unreadable`
   state rather than being dropped. No new dependency, no new secret, no Railway
   op; the websites row dogfoods its own status.
   **Enriched machine-readable heartbeat fields** ([D-0028], retro G3): the
   `orders:` line is parsed (`acked=`/`done=` ids, ranges like `001-008`
   expanded; **outstanding = acked minus done**, computable from the heartbeat
   alone; a `claimed-by:` annotation captured verbatim), and three OPTIONAL
   lines — `routine:` (wake-clock state; **armed with a last fire older than
   the stale threshold flags "armed but silently dead"**, an armed routine
   with no recorded fire shows an honest "no fire recorded yet"), `landing:`
   (`all-merged` / `pushed-unmerged <branch>` / `LOCAL-ONLY <branch>` — the
   mechanical stranded-work catch; pushed/local badge as rescue candidates
   and **sort attention-first** with the stale rank), `deployed:` (last
   live-verified sha, rendered as written). Summary header gains stranded /
   silent-routine / outstanding-orders roll-up badges; `/fleet.json` carries
   the parsed `orders_info` / `routine_info` / `landing_info` structures so
   the manager machine-reads "what's left" per lane without diffing inbox vs
   status vs git. A lane writing none of the optional lines renders exactly
   as before; free-text `orders:` parses honestly to `ok=False`, never
   invented ids.
3b. **Owner queue** (`/queue`) — every ⚑ owner ask on ONE deduplicated,
   newest-first surface ([D-0027], ORDER 005): the owner's single to-do list.
   Two halves: (1) every fleet lane's `⚑ needs-owner` field, reusing the exact
   `fleet.overview()` pipeline `/fleet` rides (same fetch, same parse, same TTL
   cache — never a second fetch path); (2) the manager's curated
   `menno420/fleet-manager docs/owner-queue.md`. `app/owner_queue.py` parses the
   fleet's six-field OWNER-ACTION format (WHAT/WHERE/HOW/WHY-IT-MATTERS/
   UNBLOCKS/VERIFIED-NEEDED — tolerant of the flattened one-line shape lane
   parsing produces AND raw multiline markdown) into structured cards; a plain
   ask with no blocks renders as an honest free-text item. Duplicates (same
   normalized WHAT/text) merge into one item that keeps **every** source badge.
   Ordering is newest-first by source-lane heartbeat; undated items (the
   fleet-manager doc) sort last, labeled "date unknown" — never given an
   invented time. Honest degradation: fleet-manager is private + read at
   runtime only — `GITHUB_TOKEN` unset → a clear **not configured** banner;
   token set but fetch failed → **unavailable** with the reason; unreadable
   lane heartbeats are counted with an "asks may be missing" banner. A
   fetched owner-queue.md with no structured blocks yields zero list items
   (a whole document is not an "ask") and renders in full below, labeled.
3c. **Environments** (`/environments`) — read-only render of the fleet's
   claude.ai environment registry `menno420/fleet-manager environments/`
   ([D-0027], ORDER 005): README, setup-script templates, env-var schemas,
   specs — one card per file, README first, markdown via the sanitized
   `journal.render_markdown`, scripts/schemas as escaped code blocks with a
   **copy-to-clipboard** button (`app/static/copycode.js`, vanilla JS, degrades
   silently without the Clipboard API). The manager's repo stores; this site
   renders; secrets are never present by design (the registry stores
   names/placeholders only). Listing walks `environments/` one subdirectory
   level deep (bounded `MAX_FILES=40`) over the TTL-cached contents API.
   Honest degradation mirrors `/queue`: **not configured** (token unset) /
   **unavailable** (reason surfaced) / per-file + per-subdir error banners.
3d. **Projects** (`/projects`, `.json` variant) — read-only render of the
   fleet's Project-package registry `menno420/fleet-manager projects/`
   ([D-0030], ORDER 009 increment 1): one card per `projects/<repo>/`
   package showing its role-classified files (meta / Custom Instructions /
   coordinator prompt / setup script / failsafe / wake-routine prompt —
   tolerant basename heuristics, unrecognized files listed honestly as
   "other"), each deep-linked to GitHub, plus `meta.md` rendered inline
   (sanitized markdown) with a best-effort `deployed:`/`state:` line
   surfaced as a badge (no such line → an honest "state unknown", never
   invented). Bounded walk (`MAX_PACKAGES=30`, `MAX_FILES_PER_PACKAGE=20`)
   over the same TTL-cached contents API as `/environments`. Honest
   degradation extends the `/queue` model with an **empty** state: a 404 on
   `projects/` (the registry was still landing upstream at ship time)
   renders a friendly "registry not landed yet" card — never a 500;
   not-configured / unavailable / per-package + per-meta error banners
   otherwise. `/projects.json` drops the rendered meta HTML (mirrors
   `/fleet.json`).
4. **Journal browser** (`/journal`) — session logs (`.sessions/`), decision
   ledgers (`docs/decisions.md`), question-routers, recent PRs and commits
   across the repos, rendered readably and deep-linked back to GitHub.
   substrate-kit has no docs/.sessions tree — it shows PR/commit history.
   - **Markdown is rendered server-side** ([D-0014]): `.md` files open as real
     HTML (headings, code blocks, tables, links) via `journal.render_markdown()`,
     which **lazy-imports** `markdown` and **sanitizes** the output with `bleach`
     to an allow-list — a missing lib degrades to an escaped `<pre>` instead of
     500ing. GitHub deep-links are preserved.
   - **Cross-repo search** (`/journal/search`, `.json` variant): one case-
     insensitive query fans out across **all four repos'** journal corpus —
     session-log filenames + contents, decision-ledger entries, question-router
     Q-blocks — fetched through the TTL cache, ranked by match count, each hit
     showing repo · file · line · highlighted snippet + a GitHub deep-link
     (`…#L{n}`). Fetch failures surface an honest banner, never a silent drop.

## Routes

| Route | Auth | What |
|---|---|---|
| `/` | public | readiness board (secrets masked to a count) |
| `/api/readiness.json` | public | board data as JSON (no secret names) |
| `/fleet` | public | fleet heartbeat — every lane's `control/status*.md` (HTML) — [D-0021] |
| `/fleet.json` | public | same fleet heartbeat as JSON (rendered body stripped) |
| `/queue` | public | owner queue — every ⚑ needs-owner ask + the fleet-manager owner-queue, deduplicated (HTML) — [D-0027] |
| `/environments` | public | fleet-manager `environments/` registry, copy-to-clipboard (HTML) — [D-0027] |
| `/projects` | public | fleet-manager `projects/` Project-package registry (HTML) — [D-0030] |
| `/projects.json` | public | same registry as JSON (rendered meta HTML stripped) |
| `/activity` | public | cross-repo PR activity timeline (HTML) — [D-0020] |
| `/activity.json` | public | same timeline as JSON |
| `/activity.xml` | public | same timeline as a subscribable Atom 1.0 feed (`application/atom+xml`) — [D-0025] |
| `/ideas` | public | cross-repo `docs/ideas/` backlog (HTML) — [D-0020] |
| `/ideas.json` | public | same backlog as JSON |
| `/journal` | public | journal overview, all repos |
| `/journal/search?q=…` | public | cross-repo journal search (HTML) — [D-0014] |
| `/journal/search.json?q=…` | public | same search as JSON (plain snippets) |
| `/journal/{repo}` | public | per-repo sessions / ledgers / PRs / commits |
| `/journal/{repo}/file?path=…&ref=main` | public | render a repo file (markdown → HTML) |
| `/static/*` | public | static assets (the live-monitoring auto-refresh JS) — [D-0023] |
| `/healthz` | public | Railway healthcheck |
| `/version` | public | deployed commit SHA (`{service, sha, short}`) — powers the deploy-state cell ([D-0018]) |
| `/owner` | **gated** | full-detail board — un-masked Actions **secret names** + broken-check/oldest-PR detail |
| `/owner/api/readiness.json` | **gated** | authed JSON, including secret names |
| `/owner/actions/refresh` (POST) | **gated** | clear the in-memory TTL cache (in-process) |
| `/owner/actions/rerun-ci` (POST) | **gated** | re-run the latest FAILED Actions run on a selected repo |

`?refresh=1` on any page bypasses the cache for that load.

## Live-monitoring auto-refresh ([D-0023])

The two **live-monitoring** surfaces — the board `/` and `/fleet` — auto-refresh
client-side so the owner's control glance stays current without a manual reload.
`app/static/autorefresh.js` (a small vanilla-JS module, no dependency) re-fetches
the **current page** over HTTP every `AUTOREFRESH_SECONDS` (default 45s) and swaps
only the server-rendered `#live-content` region into the DOM — no full-page reload
flash, no scroll jump, and **no duplicated render logic** (the server stays the one
renderer, so a soft refresh always matches a hard reload). The fetch omits
`?refresh=1`, so it rides the TTL cache and never hammers the GitHub API. A visible
`auto-refreshing every Ns · last updated <time>` indicator carries a **pause/resume**
toggle (persisted in `localStorage`); polling also pauses while the tab is hidden or
a fetch is already in flight, and the pulse dot honors `prefers-reduced-motion`.
**Only these two monitoring screens auto-refresh** — content/journal pages
(`/journal*`, `/activity`, `/ideas`) stay static. The static dir is served by a
`StaticFiles` mount at `/static` (public, credential-free like the rest of the site).

## Deploy-state drift + `/version` ([D-0018])

Every service (control-plane, botsite, dashboard) exposes an **unauthenticated
`/version`** JSON — `{"service", "sha", "short"}` — reporting the commit it is
actually running. The SHA is read **live from the environment** (no network) in
this order:

1. **`RAILWAY_GIT_COMMIT_SHA`** — Railway injects the deployed commit
   automatically. **Primary source; no wiring needed.**
2. **`GIT_SHA`** — a build arg baked into each service's Dockerfile
   (`ARG GIT_SHA` → `ENV GIT_SHA`) as a **fallback** for local / non-Railway
   builds. Optional (pass `--build-arg GIT_SHA=$(git rev-parse HEAD)`, or a
   Railway service build variable).
3. Neither set → the literal `"unknown"` (honest, never faked or crashed).

The board's **websites-row deploy-state cell** compares each service's deployed
short-sha to the `main` HEAD short-sha it already fetches from the GitHub API.
control-plane knows its own deployed sha directly (env); botsite and dashboard
are read over their public `/version` through the same TTL cache. Because Railway
auto-deploys each service from `main` on merge, `in sync` means the live site
runs the latest merged code and `DRIFT` means a deploy is in progress or has
stalled/failed. **No secret and no Railway account token is involved** — the sha
is public data, so `/version` is public like `/healthz`.

## Public site + gated `/owner` area

The **public site** (every route except `/owner*`) serves without credentials.
It is derived almost entirely from **public** repo data. The one datum that is
not public — the GitHub Actions **secret names** (obtainable only with an
admin-scope token) — is **masked to a count** (`N secret(s)`) on the public
board: the individual names are never rendered in the public board HTML nor
serialized into `/api/readiness.json`. Everything else (rulesets, required
checks, CODEOWNERS presence, auto-merge, open PRs, journal contents) is public
and shown as-is. This masking is enforced by tests and must never regress.

The **`/owner` area** is the single gated corner of the site (`app/owner.py`),
added so the owner can see the full detail the public board hides and take real
action, while the main site stays browsable:

- **Gate:** HTTP Basic (any username), password compared **constant-time**
  (`secrets.compare_digest`) to `SITE_PASSWORD`. No credentials → **401**; a
  correct password → 200. If `SITE_PASSWORD` is **unset**, `/owner*` **fails
  closed with 503** while the public site keeps working. The gate lives only on
  the `/owner` router — it never touches the public routes.
- **`GET /owner`** renders the readiness board **un-masked**: the actual secret
  NAMES per repo (fetched internally with the same `GITHUB_TOKEN`, exposed only
  on this authed path via `readiness.board(reveal_secrets=True)`), plus a
  broken-check list and oldest-PR links.
- **`GET /owner/api/readiness.json`** is the authed JSON with names included.
- **Privileged actions** (POST, same gate, all reversible, using creds already
  on the service):
  - **force cache refresh** — clears the in-memory TTL cache; the next load
    re-fetches live. In-process, no external creds.
  - **re-run CI** — looks up the latest **failed** Actions run on a selected
    repo's default branch and POSTs `rerun-failed-jobs` via `GITHUB_TOKEN`.
    Honest banners for the 403 (token lacks `actions:write`) and no-failed-run
    cases; never 500s.

**Deliberately NOT wired** (separate owner approval): any Railway
account-token action and any **live production-bot** control API. No
`RAILWAY_API_KEY` is present in the service env.

## Env vars

| Var | Required | Meaning |
|---|---|---|
| `SITE_PASSWORD` | for `/owner` | Gates ONLY the `/owner` area (HTTP Basic, any username). The public site never reads it. Unset → `/owner*` fails closed 503; the public site still works. |
| `GITHUB_TOKEN` | yes (for full board) | PAT for the REST API. Plain read scope covers most cells; the Actions **secrets count** and reading `allow_auto_merge` need admin/push scope — without it those cells show `unknown (token lacks admin scope)`. Secret *names* are exposed only through the gated `/owner` area; `actions:write` is needed for the `/owner` re-run-CI action. Also the only credential that can read `menno420/fleet-manager` when its contents aren't anonymously reachable — unset, `/queue`'s fleet-manager half and `/environments` show an honest **not configured** banner ([D-0027]). |
| `PORT` | Railway sets it | bind port (default 8000) |
| `CACHE_TTL_SECONDS` | no | server-side GitHub cache TTL, default `180` |
| `AUTOREFRESH_SECONDS` | no | client poll interval for the board `/` + `/fleet` live-monitoring auto-refresh, default `45` ([D-0023]) |
| `GITHUB_API_BASE` | no | REST base override (testing behind restricted egress) |
| `GITHUB_RAW_BASE` | no | raw-content base override |

## Mobile / responsive ([D-0014])

The owner browses from tablet/phone, so the single inline stylesheet in
`app/templates/base.html` carries a `@media (max-width: 640px)` block: the
readiness board's wide tables get a `min-width` and **scroll horizontally
inside their card** (`.card { overflow-x:auto }`) instead of squashing or
breaking the layout; the header, nav, and the journal **search box** reflow to
full width with tap-friendly targets; the rendered-markdown pages stay within
the viewport. Desktop rules are untouched — the media query only adds. Verified
by CSS inspection at 375 px and 768 px widths.

## Data + caching model ([D-0004])

- Listings/state via the REST API with `GITHUB_TOKEN`; public file *bodies*
  via `raw.githubusercontent.com` **without** the token (a bad/foreign bearer
  makes the raw host 404 — verified live), contents-API fallback.
- Per-URL in-memory TTL cache (180 s default): successes and stable negatives
  (404/403/401) are cached; transient failures (429/5xx/network) are not.
- A full board load is ~30 GitHub calls — with the cache that is well inside
  a PAT's 5000 req/h budget even at aggressive reload rates.

## Run

```bash
pip install -r requirements.txt
GITHUB_TOKEN=… uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Railway: build the `Dockerfile` at repo root (binds `0.0.0.0:$PORT`),
healthcheck `/healthz`, set `GITHUB_TOKEN` and `SITE_PASSWORD` as service
variables (`SITE_PASSWORD` gates only the `/owner` area; the rest of the site is
public).

## Dev without api.github.com egress

Agent containers route HTTPS through a policy proxy that blocks
`api.github.com` (the sanctioned agent path is the GitHub MCP server).
`tools/dev_api_mirror.py` serves previously-captured real API responses from a
directory; point `GITHUB_API_BASE` at it. `raw.githubusercontent.com` is
reachable directly, so file bodies stay genuinely live even in that setup.

## Tests

```bash
python3 -m pytest tests/ -q
```
