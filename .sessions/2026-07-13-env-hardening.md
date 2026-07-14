# 2026-07-13 — env hardening: int("") import-crash fix + SITE_PASSWORD docs

> **Status:** `complete` — PR #282, branch `claude/env-hardening-0713`; the
> six module-level int env parses across three services now fall back to
> their documented defaults on empty/unset/malformed values instead of
> crashing at import; SITE_PASSWORD documented in botsite's env table; the
> botsite-copy ANTHROPIC_API_KEY question recorded honestly as
> "not measured — walled"; lands via the auto-merge enabler on green.

- **📊 Model:** fable-class · worker · order-slice

**What this session was about:** order rung — ORDER 026 follow-through
(`control/inbox.md` § "ORDER 026 · 2026-07-13T10:45Z"). The ORDER 026
discovery recorded in `docs/CAPABILITIES.md` (2026-07-13 wall entry) found
that an empty-string env var crashes three services at import via `int("")`
on the TTL vars, and that Railway variable writes are harness-denied. This
session hardened every module-level numeric env parse across app/, botsite/,
dashboard/, review/ to fall back to the documented default, documented
SITE_PASSWORD in the env-var docs home, and recorded a bounded read-only
finding on ANTHROPIC_API_KEY for the parallel botsite Railway copy
(variable NAMES only, never values).

## What was done

- Task 1 — `_env_int(name, default)` local helper (one per module, no
  cross-service imports; mirrors the `daily_cap()` try/except idiom in
  `botsite/testing_ai.py`/`app/owner_assist.py`) now guards all six
  module-level int parses: `app/config.py` (CACHE_TTL_SECONDS 180,
  AUTOREFRESH_SECONDS 45, FLEET_STALE_HOURS 12, CLAIM_STALE_HOURS 24),
  `botsite/data_source.py` (SITE_CACHE_TTL_SECONDS 180),
  `dashboard/data_source.py` (DATA_CACHE_TTL_SECONDS 180). Fallback-to-
  default chosen over fail-loudly: it is the repo's measured convention
  (degrade honestly, never crash). review/ has no such sites; no
  module-level float() env parses exist.
- 15 new tests (`tests/`, `botsite/tests/`, `dashboard/tests/`
  `test_env_parse_hardening.py`): empty → default, unset → default,
  garbage → default, valid wins, + `importlib.reload` proof each module
  survives import with hostile values set.
- Task 2 — SITE_PASSWORD: dashboard does NOT read it (set-but-unused
  Railway drift, row updated in `docs/dashboard.md` citing the ORDER 026
  confirmation); the missing documentation was botsite's — new row in
  `docs/botsite.md` § Environment variables (`botsite/testing.py:186`
  gates `/testing/owner*`, HTTP Basic, fail-closed 503 unset).
- Task 3 — ANTHROPIC_API_KEY on the parallel botsite copy: **not
  measured — walled**, no probe attempted. The only documented Railway
  read path is scoped to `superbot-websites`; `docs/RAILWAY-SAFETY.md`
  bans the ambient production-bot IDs in ANY call, reads included.
  Recorded in `docs/botsite.md`'s ANTHROPIC_API_KEY row (names only).
- `docs/ideas/backlog.md`: this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1221 passed, 1 warning (+15 over main's 1206);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — ORDER 026 follow-through (env-hardening prework
dispatched by the coordinator).

## 💡 Session idea

**Structural no-bare-numeric-env-parse gate — make the int("") class
unshippable, not just fixed** — a small static test (repo-wide scan of
app/, botsite/, dashboard/, review/, excluding bootstrap.py/.substrate)
failing on any MODULE-LEVEL `int(`/`float(` wrapped directly around
`os.environ`/`os.getenv` that doesn't go through an `_env_int`-style
guard. Worth having because this session fixed six sites by hand, but
nothing stops the seventh — the same discipline-vs-structure gap the
clarity gate (PR #241) closed for page headers. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the code-vs-inventory
bullets (#227 line and its generalization) check env-var NAME
documentation completeness, never parse SAFETY; nothing scans for numeric
env parses. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 hand-curated
entries each carrying honest per-packet status plus a registry-honesty pin
test locking the exact 1/12/2/7 breakdown; what it missed: its own 💡
admits the catalog decays silently the moment venture-lab moves past the
pinned `2c039e3` — the drift guard was captured, not built.
