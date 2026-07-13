# 2026-07-13 — env-guard gate: CI fails on module-level bare int()/float() over env vars

> **Status:** `complete` — PR #285, branch `claude/env-guard-gate-0713`;
> the int("") crash class PR #282 fixed by hand is now structurally
> unshippable — a static gate in the suite fails CI with file:line on any
> import-time bare numeric cast over env vars.

- **📊 Model:** Claude Fable 5 · worker · gate-slice

**What this session was about:** backlog promotion — the "Structural
no-bare-numeric-env-parse gate" bullet in `docs/ideas/backlog.md`
(captured by the env-hardening session, PR #282 era). PR #282 fixed six
sites by hand via `_env_int`, but nothing stopped the seventh: a
module-level `int(os.environ.get(...))` with a bad/empty value crashes
the service at import — before it binds a port, only ever caught in
prod. This session closed the discipline-vs-structure gap the same way
the clarity gate (PR #241) did for page headers.

## What was done

- `tests/test_env_guard_gate.py` — AST-scans every `*.py` under app/,
  botsite/, dashboard/, review/ (excluding `bootstrap.py`, `.substrate/`,
  tests dirs, and the `review/gen_*.py` offline bakers, per the repo's
  search-hygiene convention) and fails with `file:line  <source line>` on
  any IMPORT-TIME bare `int(`/`float(` whose arguments involve
  `os.environ`/`os.getenv` (all four spellings incl. `from os import
  environ/getenv`), pointing to `_env_int` in `app/config.py` as the fix.
  Import-time means module scope, top-level `if`/`try`/`with` bodies,
  class bodies, and function decorators/argument defaults; function and
  lambda BODIES are exempt — exactly what lets `_env_int`-guarded sites
  pass. Style follows the `tests/test_time_discipline.py` precedent
  (AST guard + meta-tests).
- Self-tests prove detection without touching real service modules:
  a seeded tmp-file violation (`PORT = int(os.environ.get("PORT",
  "8080"))`) is caught with the exact message, a guarded pattern inside
  a function def passes, import-time reach (if/try/defaults flag, bodies
  don't) and all env spellings are pinned as meta-tests.
- `docs/ideas/backlog.md` — the source bullet flipped from `captured` to
  the file's shipped convention (shipped 2026-07-13, PR #285); this
  session's new 💡 captured as a fresh bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1226 passed, 1 warning (+5 over main's 1221);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — backlog promotion (env-guard-gate bullet in
`docs/ideas/backlog.md`, source `.sessions/2026-07-13-env-hardening.md`).

## 💡 Session idea

**Hostile-env import smoke — dynamically import every service module
under a poisoned environment** — the dynamic complement to this session's
static gate: a test that sets every documented env var (the envhub
manifest already knows the names) to "" and "garbage", then
`importlib.import_module`s every module in all four services, proving no
import-time crash of ANY kind. Worth having because the static gate only
sees `int()`/`float()` — `json.loads`, date parsing, `.split()[0]`, or
`Path(...).read_text()` over an env var at module level are the same
crash class and invisible to an AST cast-scan; a real import under
hostile values catches them all. Deduped against `docs/ideas/backlog.md`
+ the queue-state NEXT list: `test_env_parse_hardening.py` reloads only
`app.config` with hostile INT_VARS; the healthcheck bullets probe live
`/healthz`, never imports; nothing walks modules under a poisoned env.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
curated with per-title honesty derived from each packet's own Status
blockquote and a registry-honesty test pinning the exact 1/12/2/7
breakdown; what it missed: that pin hard-couples the test to the data
file, so every legitimate upstream catalog change now requires editing
test and JSON in lockstep — its own sha-drift 💡 mitigates staleness but
not the coupling.
