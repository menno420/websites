# Control-plane site (readiness board + journal browser)

> **Status:** `reference` — shipped in PR #2, 2026-07-09. Stack/model provenance: [D-0003], [D-0004].

The owner-facing oversight site: check every repo's working quality and progress
by *looking*, instead of asking an agent to go fetch GitHub state. Two halves:

1. **Readiness board** (`/`) — one row per repo (`superbot`, `superbot-next`,
   `substrate-kit`, `websites`), each signal shown as **configured?** AND
   **working now?**, fetched live from the GitHub REST API:
   ruleset/branch-protection, required checks + the exact check runs on the
   `main` head commit, CODEOWNERS present/enforced, Actions secrets (names
   only), auto-merge + enabler-workflow presence, open-PR health (count +
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
| `/` | Basic | readiness board |
| `/api/readiness.json` | Basic | board data as JSON |
| `/journal` | Basic | journal overview, all repos |
| `/journal/{repo}` | Basic | per-repo sessions / ledgers / PRs / commits |
| `/journal/{repo}/file?path=…&ref=main` | Basic | render a repo file (markdown → HTML) |
| `/healthz` | none | Railway healthcheck |

`?refresh=1` on any page bypasses the cache for that load.

## Auth

HTTP Basic on every route except `/healthz`: any username, password must equal
`SITE_PASSWORD` (constant-time compare). If `SITE_PASSWORD` is unset the site
returns 503 — it fails **closed**, never open.

## Env vars

| Var | Required | Meaning |
|---|---|---|
| `SITE_PASSWORD` | yes | shared secret for the Basic-auth gate (never committed) |
| `GITHUB_TOKEN` | yes (for full board) | PAT for the REST API. Plain read scope covers most cells; listing Actions **secrets** and reading `allow_auto_merge` need admin/push scope — without it those cells show `unknown (token lacks admin scope)` |
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
SITE_PASSWORD=… GITHUB_TOKEN=… uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Railway: build the `Dockerfile` at repo root (binds `0.0.0.0:$PORT`),
healthcheck `/healthz`, set `SITE_PASSWORD` + `GITHUB_TOKEN` as service
variables.

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
