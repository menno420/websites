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
   - **Known trap honored:** superbot-next's `report` job (golden-parity
     workflow) is red-until-parity BY DESIGN — the board badges it
     `red-by-design` (purple) and never counts it toward "broken checks".
   - Any signal the token can't read renders `unknown (reason)` — the board
     degrades per-cell, it never fakes a value.
2. **Journal browser** (`/journal`) — session logs (`.sessions/`), decision
   ledgers (`docs/decisions.md`), question-routers, recent PRs and commits
   across the repos, rendered readably and deep-linked back to GitHub.
   substrate-kit has no docs/.sessions tree — it shows PR/commit history.

## Routes

| Route | Auth | What |
|---|---|---|
| `/` | public | readiness board |
| `/api/readiness.json` | public | board data as JSON |
| `/journal` | public | journal overview, all repos |
| `/journal/{repo}` | public | per-repo sessions / ledgers / PRs / commits |
| `/journal/{repo}/file?path=…&ref=main` | public | render a repo file (markdown → HTML) |
| `/healthz` | public | Railway healthcheck |

`?refresh=1` on any page bypasses the cache for that load.

## Auth — none (public site)

The site is **public**: every route serves without credentials (owner decision 2026-07-09, "Yes drop the auth"). The former HTTP Basic gate — and its fail-closed
503-when-unset behaviour — was removed. `SITE_PASSWORD` is no longer read.

The board is derived almost entirely from **public** repo data. The one datum
that is not public — the GitHub Actions **secret names** (obtainable only with an
admin-scope token) — is **masked to a count** (`N secret(s)`): the individual
names are never rendered in the board HTML nor serialized into
`/api/readiness.json`. Everything else on the board (rulesets, required checks,
CODEOWNERS presence, auto-merge, open PRs, journal contents) is public and shown
as-is.

## Env vars

| Var | Required | Meaning |
|---|---|---|
| `SITE_PASSWORD` | no (unused) | Formerly the Basic-auth secret; the gate was removed (2026-07-09 auth-drop decision) and the app no longer reads it. |
| `GITHUB_TOKEN` | yes (for full board) | PAT for the REST API. Plain read scope covers most cells; the Actions **secrets count** and reading `allow_auto_merge` need admin/push scope — without it those cells show `unknown (token lacks admin scope)`. Secret *names* are never exposed regardless of scope. |
| `PORT` | Railway sets it | bind port (default 8000) |
| `CACHE_TTL_SECONDS` | no | server-side GitHub cache TTL, default `180` |
| `GITHUB_API_BASE` | no | REST base override (testing behind restricted egress) |
| `GITHUB_RAW_BASE` | no | raw-content base override |

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
healthcheck `/healthz`, set `GITHUB_TOKEN` as a service variable
(`SITE_PASSWORD` is no longer used — the site is public).

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
