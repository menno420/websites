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
| `/` | public | readiness board (secrets masked to a count) |
| `/api/readiness.json` | public | board data as JSON (no secret names) |
| `/journal` | public | journal overview, all repos |
| `/journal/{repo}` | public | per-repo sessions / ledgers / PRs / commits |
| `/journal/{repo}/file?path=…&ref=main` | public | render a repo file (markdown → HTML) |
| `/healthz` | public | Railway healthcheck |
| `/owner` | **gated** | full-detail board — un-masked Actions **secret names** + broken-check/oldest-PR detail |
| `/owner/api/readiness.json` | **gated** | authed JSON, including secret names |
| `/owner/actions/refresh` (POST) | **gated** | clear the in-memory TTL cache (in-process) |
| `/owner/actions/rerun-ci` (POST) | **gated** | re-run the latest FAILED Actions run on a selected repo |

`?refresh=1` on any page bypasses the cache for that load.

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
| `GITHUB_TOKEN` | yes (for full board) | PAT for the REST API. Plain read scope covers most cells; the Actions **secrets count** and reading `allow_auto_merge` need admin/push scope — without it those cells show `unknown (token lacks admin scope)`. Secret *names* are exposed only through the gated `/owner` area; `actions:write` is needed for the `/owner` re-run-CI action. |
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
