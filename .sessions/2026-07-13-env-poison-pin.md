# 2026-07-13 — self-deriving poison-list pin for the hostile-env smoke

> **Status:** `complete` — PR #290, branch `claude/env-poison-pin-0713`;
> `tests/test_env_poison_pin.py` pins the hostile-env smoke's `ENV_VARS`
> to the env-var names the four services' source actually reads; lands via
> the auto-merge enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

**What this session was about:** promote the captured backlog bullet
"Self-deriving poison list — pin the hostile-env smoke's ENV_VARS against
a live source sweep" (`docs/ideas/backlog.md`, captured 2026-07-13 by the
hostile-env-smoke session 💡, PR #287): the smoke poisons a hand-collected
38-name literal, so a new env-var read added after #287 is silently
unpoisoned — the exact rot class the smoke exists to close, reopened one
variable at a time. Build an AST sweep over the four services (same
discovery/exclusion rules as the smoke) that derives every env-var NAME
the source actually reads and fails, naming the variable and site, when
the poison list misses one.

## What was done

- **`tests/test_env_poison_pin.py`** (new, 8 tests, zero network): an AST
  sweep over the SAME files the smoke discovers — `SERVICE_DIRS`, the
  exclusion rules, and `ENV_VARS` are IMPORTED from
  `tests/test_hostile_env_smoke.py`, one source of truth, no forked
  discovery. Read shapes resolved to names: literal
  `os.environ.get/["X"]/getenv/in/pop/setdefault` (incl. the
  `from os import environ, getenv` spellings); module-constant
  indirection (`ENV_MODEL = "TESTING_AI_MODEL"` — the
  app/owner_assist.py / botsite/testing_ai.py / app/writeback.py /
  botsite/testing_payouts.py pattern); guarded-wrapper call sites (a
  function whose PARAMETER feeds the environ read, e.g. `_env_int`, marks
  a wrapper and its call-site literal names are collected).
- **The pin:** every derived name must be in `ENV_VARS`; failure names the
  variable + read site and points at the smoke's list. One-directional by
  design (the list may poison more than source reads — `PORT` is
  Dockerfile-only).
- **Dynamic reads stay loud:** a non-derivable name expression must sit on
  an explicit per-entry-justified `DYNAMIC_READ_ALLOWLIST` with a
  stale-entry check (the #225/#233 convention). One entry today:
  `app/railway.py` `_committed_services` — a presence-only `bool(...)`
  read of committed-inventory names, never value-parsed, the names
  themselves pinned by `tests/test_inventory_consistency.py`.
- **Meta-test:** the sweep must derive names in all four services, so a
  lost read shape can't silently blank it. Five self-tests pin each
  shape/resolution rung; red-proven on a planted unpoisoned read
  (`TOTALLY_NEW_KNOB` derived and flagged by name).
- **Live sweep result at HEAD:** 49 reads → 37 unique names = exactly
  `ENV_VARS` minus `PORT`; the one dynamic read = the one allowlist entry.
- **`docs/ideas/backlog.md`:** the source bullet flipped `captured` →
  `built` (this PR); this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1252 passed, 1 warning** (1244 at HEAD; +8);
  `python3 bootstrap.py check --strict` — green apart from this card's own
  designed born-red HOLD (flipped by this close-out) and the pre-existing
  `owner-action-fields` advisory (never exit-affecting, not owned here).

**Decisions made:** the pin imports `ENV_VARS`/discovery from the smoke
module instead of copying them — a forked list would be the same rot class
the pin exists to close; wrappers are DETECTED (param feeds the read)
rather than hand-listed, so the next `_env_int`-style helper is covered
automatically; dynamic reads fail loud instead of being skipped, with the
justification in the allowlist entry itself.

**Next session should know:** the pin covers name-reads only — aliasing
(`e = os.environ; e.get("X")`) or a novel access idiom would be invisible
to `_name_expr_of_read`; see this session's 💡 for the completeness leg.

⚑ Self-initiated: no — backlog promotion (`docs/ideas/backlog.md`
"Self-deriving poison list", the #287 💡), landing-worker slice.

## 💡 Session idea

**Environ-mention accounting leg for the poison pin** — a completeness
guard asserting every AST occurrence of `environ`/`getenv` in service
source is accounted for: consumed by a recognized name-read shape, part of
a whole-env use (`{**os.environ}` / `dict(os.environ)`), or explicitly
allowlisted — so aliasing (`e = os.environ` then `e.get("X")`) or a new
access idiom fails loud instead of slipping beneath
`_name_expr_of_read`'s shape list. Worth having because the pin's
guarantee is only as strong as its recognized-shape list, and an
unrecognized idiom today is silently ignored — the same silent-rot class,
one level up. Deduped against `docs/ideas/backlog.md` (the
code-vs-inventory bullets check documentation completeness, nothing checks
the scanner's own shape coverage) and captured there.

## ⟲ Previous-session review

The outbox-grammar-pin session (#289) did well feeding the REAL committed
file through the real parser (parse-the-artifact, zero synthetic drift) —
this session copied its one-source-of-truth discipline by importing
`ENV_VARS` and the discovery rules from the smoke module instead of
duplicating them; what it missed (its own 💡 admits it) is that the fast
lane merge-lags the pin — same honest limitation here: a poison-list gap
lands red only on the PR that adds the read, which is exactly when it
should.
