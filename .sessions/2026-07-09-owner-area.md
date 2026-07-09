# 2026-07-09 — Gated /owner area (public site unchanged; privileged overlay)

> **Status:** `complete` — shipped as PR #14 (`claude/owner-area`); live deploy
> evidence captured in `docs/deployment.md` and the follow-up evidence PR.
>
> Add a password-gated `/owner` area to the control-plane app while keeping every
> existing public route byte-identical. `/owner` un-masks the secret NAMES the
> public board hides and exposes real privileged actions (cache refresh, re-run
> latest failed CI). Owner-directed ("add a password to a secure part of the
> site … but the main site should always be browsable"). Deploy + verify live.

## What was done

- **Gate on `/owner*` only** (`app/owner.py`, an included `APIRouter(prefix="/owner")`).
  HTTP Basic (any username), password compared constant-time
  (`secrets.compare_digest`) to `SITE_PASSWORD`. No/wrong creds → 401; correct →
  200; `SITE_PASSWORD` unset → the `/owner` routes fail closed with 503. The gate
  is a per-route FastAPI dependency, so `app/main.py`'s public routes (`/`,
  `/journal*`, `/api/readiness.json`, `/healthz`) are byte-identical and never
  touch it. `app/config.py` reads `SITE_PASSWORD` again (only the owner router
  uses it).
- **Full-detail owner view.** `GET /owner` renders the readiness board UN-masked:
  the real Actions secret NAMES per repo, plus broken-check and oldest-PR detail.
  Names are threaded exclusively through a new `readiness.board(reveal_secrets=True)`
  path — the public `board()` call never sets it, so the public output cannot
  regress. `GET /owner/api/readiness.json` is the authed JSON with names.
- **Privileged actions** (POST, same gate, reversible): `POST /owner/actions/refresh`
  clears the in-memory TTL cache (`github.clear_cache()`, in-process, no external
  creds); `POST /owner/actions/rerun-ci` looks up the latest FAILED Actions run on
  a selected repo's default branch and POSTs `rerun-failed-jobs` via the existing
  `GITHUB_TOKEN` (`github.rerun_latest_failed` + `github.api_post`), degrading
  honestly on 403 / no-failed-run.
- **Not wired (separate owner approval):** Railway account-token actions + live
  production-bot control API. No `RAILWAY_API_KEY` in the app env; no bot
  control-API URL/token anywhere.
- Added `python-multipart==0.0.32` (pinned runtime dep) for the POST form.
- **Tests** (`tests/test_app.py`, now 15): `/owner` 401 without creds, 503 when
  `SITE_PASSWORD` unset (public stays 200), the invariant pair (public HTML+JSON
  zero secret names AND authed `/owner` HTML+JSON contain them), `reveal_secrets`
  threading, both POST actions authed+unauthed, and the no-failed-run branch.
- **Docs:** `docs/site.md` (public-vs-`/owner` split, the gate, the actions, env
  vars), `docs/current-state.md`, `[D-0012]` appended to `docs/decisions.md`
  (supersedes `[D-0011]`, which is stamped `superseded-by: D-0012`).

## Verification

- Local, `SITE_PASSWORD=localtestpw`: public `/` → 200, **no** `www-authenticate`,
  `grep -c ANTHROPIC_API_KEY` on public HTML = 0; `/owner` no creds → 401; wrong
  pw → 401; correct pw → 200; `POST /owner/actions/refresh` authed → 200;
  `/healthz` → 200.
- Local, `SITE_PASSWORD` UNSET: public `/` and `/api/readiness.json` → 200;
  `/owner` → 503 (fail closed); `/healthz` → 200.
- `python3.12 bootstrap.py check --strict` green; `tests/test_app.py` 15 passed.
- Live production evidence recorded in `docs/deployment.md` and below.

## 💡 Session idea

Add an **audit trail** for the `/owner` privileged actions: a small in-memory
(or committed-nowhere log) ring that records each `refresh` / `rerun-ci` with a
timestamp + result, rendered at the top of `/owner`. Right now a real write
action (re-run CI) leaves no trace on the site itself — the owner would have to
check GitHub to confirm what fired. A visible "last 10 owner actions" panel makes
the power surface self-documenting and is the natural place to hang any future
gated action (so each new lever inherits the audit line for free).

## ⟲ Previous-session review

The drop-auth session (PR #12) did the right thing structurally: when it went
public it turned "does a secret name reach the HTML?" into a tested invariant
rather than a comment, which is exactly why THIS session could add an authed
un-masking path with confidence — the public-masking test already pins the wall
the new `reveal_secrets` path must not breach. Its own `💡` idea (a
public-surface leak *checker* in `bootstrap.py check`, beyond the one unit test)
is still unbuilt and is now more valuable, not less: with a second code path that
DELIBERATELY emits the names, a template edit that accidentally renders
`r.secrets.names` on the public `board.html` would be a real regression a grep-
style checker would catch structurally. **Workflow improvement surfaced:** the
"enforce, don't exhort" instinct wants that leak-guard promoted from a session
idea to an actual checker — recommend a follow-up session builds it, since the
public/`/owner` split this session introduced is precisely the condition that
makes the guard load-bearing.
