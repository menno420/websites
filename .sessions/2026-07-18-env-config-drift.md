# 2026-07-18 — B6 config-drift flags: code-referenced vs declared env NAMES

> **Status:** `complete` — branch `claude/env-config-drift`, PR **#401**. B6
> from the backlog (owner-decided **Q1=a**: a CONTAINED, NAMES-ONLY, STATIC
> check — never a value, never a live Railway/secret call in the running
> service). Adds the third env-name view the gated `/owner/environments` page
> was missing: **code-referenced-vs-declared** drift.

- **📊 Model:** Claude Opus 4.8 · high · feature build

**What this session is about:** the gated `/owner/environments` page already
held two of the three env-name views it needs — the COMMITTED per-service
declared manifest (`app/railway.py` `SERVICES`: names + a one-line purpose
each) and the LIVE Railway variable NAMES, DIFFED against each other by
`app/envdrift.py` (committed-vs-live). B6 adds the missing THIRD axis:
**code-referenced-vs-declared** drift. A static AST scan of each service's
runtime source (`app/gen_env_coderefs.py`, the `review/gen_*.py` build-time
idiom) records the env-var NAMES the code actually reads into a committed
names-only snapshot (`app/data/env_coderefs.json`); a pure diff
(`app/codedrift.py`) then flags two classes per service:
**referenced-but-undeclared** (code reads a var the manifest omits → a deploy
silently gets an empty value, no warning) and **declared-but-unreferenced** (the
manifest lists a var no code reads → stale/unused). Names only, both halves
static/committed — the deployed control-plane never scans source (its image
ships only `app/`) nor calls Railway; it reads the baked snapshot.

⚑ Self-initiated: no — coordinator-dispatched (B6, Q1=a).

## Close-out

**Evidence:**

- **surface chosen after verifying where an env surface actually lives:** the
  control-plane `/owner/environments` page (app/owner.py), which already
  renders the per-service declared manifest + the committed-vs-live drift — NOT
  the dashboard `/env` (that renders the Discord BOT's env usage from superbot
  JSON, a different domain). The B6 menu said "dashboard /env"; the real env-
  manifest surface is `/owner/environments`, so that is what B6 extends.
- **source (i), code-referenced names — a committed static snapshot, not a
  runtime scan:** `app/gen_env_coderefs.py` AST-scans each service's runtime
  source and writes `app/data/env_coderefs.json` (names only). It resolves the
  three real reference shapes: direct literals
  (`os.getenv`/`os.environ[…]`/`os.environ.get`), `_env*` helper-wrapped args
  (`_env_int("CACHE_TTL_SECONDS", 180)`), and module-constant indirection
  (`ENV_API_KEY = "ANTHROPIC_API_KEY"` then `os.environ.get(ENV_API_KEY)`).
  `tests/` and `gen_*.py` are excluded (not the deployed service). A committed
  snapshot (not a request-time scan) is REQUIRED because the control-plane
  Dockerfile ships only `app/` (`COPY app ./app`) — a runtime scan of the other
  three services' source would silently see nothing.
- **source (ii), declared manifest — REUSED, not reinvented:** the existing
  `app/railway.py` `SERVICES` list (names + purpose) is the declared side, the
  same source `app/envdrift.py` diffs against live.
- **drift computation:** `app/codedrift.py` — a pure `compute_drift(referenced,
  declared)` set-diff (the two classes per service) + a fail-soft `annotate()`
  that mutates the `railway.overview()` payload in place (per-service
  `code_drift` block + page rollup), honest `unknown`-with-reason if the
  snapshot is missing/absent. Wired into the route after `envdrift.annotate`;
  rendered as a new "code ↔ declared name drift" section (page rollup + a
  per-service line) in `owner_environments.html`.
- **signal over noise (consistent with envdrift):** `PORT` (launch-command
  consumed, never a Python read) is declared-but-unreferenced by design →
  informational; `GIT_SHA` / `RAILWAY_GIT_COMMIT_SHA` / other `RAILWAY_*`
  (Railway/build injected metadata) are referenced-but-undeclared by design →
  informational; `RAILWAY_TOKEN` is the owner-set exception (real drift). Only
  genuine config debt trips the badge.
- **the feature's first real finds (surfaced on live committed data):**
  control-plane `WRITEBACK_BRANCH_PREFIX` (read in `app/writeback.py`) and
  dashboard `ARCADE_JSON_URL` (read in `dashboard/data_source.py`) are read by
  runtime code but ABSENT from the manifest → referenced-but-undeclared;
  botsite and review are in sync. Left visible on the page (not silently
  patched) — surfacing them to the owner is the feature's purpose; correcting
  the two manifest omissions is a clean self-contained follow-up.
- **files:** `app/gen_env_coderefs.py`, `app/data/env_coderefs.json`,
  `app/codedrift.py`, `app/owner.py` (import + wire + docstring),
  `app/templates/owner_environments.html` (rollup + per-service line),
  `tests/test_code_env_drift.py`, `tests/test_env_coderefs_snapshot.py`,
  `control/status.md`, and this card.
- **verify:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1858 passed, 1 warning** (exit 0; the pre-existing
  Starlette/httpx TestClient deprecation is the only warning — 1839 prior + 19
  new). `python3 bootstrap.py check --strict` and `--require-session-log` →
  the only red is the DESIGNED born-red hold on THIS card, released at this
  flip (gating on exactly 1 card — mine; no other red). NAMES ONLY confirmed:
  a sentinel env VALUE planted in the process never reaches the payload or the
  HTML (`test_route_leaks_no_value_looking_strings`), and every string the
  annotation adds is env-name-shaped.

**Judgment:**

- Decisions made: (1) **Surface on `/owner/environments`, not dashboard
  `/env`** — the B6 menu named the dashboard, but the real env-manifest surface
  (declared names + committed-vs-live drift) is the control-plane page; the
  dashboard `/env` is the Discord bot's env usage, an unrelated domain. Using
  the real surface makes B6 the natural third axis beside envdrift. (2) **Bake
  a committed snapshot rather than scan source at request time** — the deployed
  control-plane image ships only `app/`, so a runtime scan would report the
  other three services as reading nothing (silently wrong). The
  generator→committed-JSON→service-reads-it shape is exactly the review
  service's `gen_*.py` idiom, and a freshness contract-pin
  (`test_env_coderefs_snapshot.py`) makes the snapshot unable to drift silently.
  (3) **Exclude `tests/` and `gen_*.py` from the scan** — only deployed-runtime
  code counts for "will a deploy get an empty value"; a fixture's
  `monkeypatch.setenv` or `review/gen_questions.py`'s CI-time `GITHUB_TOKEN` is
  not a deploy var, and including them added a false review/`GITHUB_TOKEN`
  find. (4) **Reuse envdrift's platform carve-outs** (`RUNTIME_INJECTED`, the
  `RAILWAY_*`/`RAILWAY_TOKEN` rule) so the two drift views agree and the badge
  flags only genuine debt. (5) **Leave the two real finds visible, don't
  silently patch the manifest** — showing them proves the feature works on live
  data and surfaces the debt to the owner; correcting `app/railway.py` SERVICES
  is a separate reversible follow-up (and would touch the envhub completeness
  pins).
- Next session should know: `/owner/environments` now carries all three
  env-name views (declared manifest · committed-vs-live · code-vs-declared).
  Two genuine manifest omissions are live on the page —
  `WRITEBACK_BRANCH_PREFIX` (control-plane) and `ARCADE_JSON_URL` (dashboard);
  adding those two `_var(...)` rows (names + purpose) to `app/railway.py`
  SERVICES is the clean close-the-loop follow-up (re-run
  `python3 -m app.gen_env_coderefs` is NOT needed for that — the snapshot is
  the code side; only the declared side changes). Any new `os.getenv`/`_env_*`
  reference in a service now requires regenerating the snapshot or the pin
  fails — that IS the contract-pin discipline working.

## 💡 Session idea

**Fold the three env-name views into one per-variable "provenance" row.** The
page now computes three independent diffs over the same name universe —
declared (manifest) · live (Railway) · referenced (code) — but renders them as
three separate sections. A higher-signal view is one table per service keyed by
NAME, with three columns (declared? · live? · read-by-code?) and a single
verdict per row: `healthy` (all three), `deploy-empty-risk` (code+no-declared,
possibly no-live), `stale` (declared, no-code), `undocumented-live`
(live+no-declared), `injected` (the PORT/RAILWAY_* carve-outs). The three
annotate passes already produce every cell; only a small join + a verdict
function would be new. It turns "read three lists and cross-reference" into
"scan one column of verdicts", and it makes the two current finds
(`WRITEBACK_BRANCH_PREFIX`, `ARCADE_JSON_URL`) jump out as a single red
`deploy-empty-risk` cell instead of a name buried in a rollup.

## ⟲ Previous-session review

`.sessions/2026-07-18-o020-verified-ledger.md` (O-020, docs-only) recorded that
owner writeback is now verified LIVE end-to-end (PR #399 → `b12dcd9`), that
ASK-0007 was satisfied with no owner action (the deployed `GITHUB_TOKEN` already
held both scopes), and that the Railway account API is reachable from the seat
— closing the last open thread on O-020 in the ledger rather than leaving it as
tribal knowledge. Its baton named B6 next; this session builds exactly that,
and its "names only, never a value, never a live secret call in the running
service" discipline is the same honesty bar the O-020 card set for the live
verify.
