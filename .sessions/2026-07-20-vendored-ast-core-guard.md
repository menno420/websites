# 2026-07-20 — auto-discovering vendored-copy AST core guard

> **Status:** `complete` — branch `claude/vendored-ast-core-guard`, PR #454.
> Born red: this card's in-progress Status held the `quality` gate red
> (`[session-card-hold]`) until the meta-test landed green; this flip to
> `complete` is the deliberate LAST step and releases the hold →
> merge-on-green lands it.

- **📊 Model:** opus-4.8 · medium · test writing

**What this session is about:** plan slice 5 of
`docs/plans/next-cycle-2026-07-19.md` — generalise the per-module vendored-copy
drift guards (`listfilter.py` byte-identity in `botsite/tests` + `review/tests`,
and the `discord_auth.py` shared-security-core guard `tests/test_discord_auth_vendored.py`
from #445) into ONE auto-discovering meta-test. It walks the four service dirs
(`app/`, `botsite/`, `dashboard/`, `review/`), discovers every same-basename
`.py` module living in more than one dir, and — for each group declared in a
small in-file manifest — asserts the declared shared core stays identical across
copies (whole-file bytes for `listfilter`, a docstring-stripped AST symbol core
for `discord_auth`). Every discovered same-basename group must be ACCOUNTED FOR
in the manifest (guarded, or explicitly marked coincidental) so a newly vendored
copy can't ship uncovered — it fails the accounting assertion until someone
declares it, instead of silently drifting until a human remembers to hand-write
its guard.

Work-ladder rung: coordinator-assigned build — plan slice 5, the 💡 of
`.sessions/2026-07-19-discord-auth-drift-guard.md`, filed to
`docs/ideas/backlog.md` (`Auto-discovering vendored-copy shared-core guard`).

⚑ Self-initiated: no — coordinator-assigned slice, promoting the discord-auth
drift-guard card's 💡 from a captured backlog idea into a committed meta-test.

## What was done

- Added `tests/test_vendored_core_guard.py` — the auto-discovering meta-test:
  - discovers same-basename `.py` modules across `app/ botsite/ dashboard/ review/`;
  - a declarative in-file manifest (`VENDORED_GROUPS` + `KNOWN_COINCIDENTAL`)
    says which basenames are genuine vendored copies and how to compare them —
    `byte` mode (whole-file identity, for `listfilter.py`) or `symbol` mode
    (docstring-stripped AST unparse of a declared function/constant core, for
    `discord_auth.py`, reusing #445's idiom);
  - an accounting test asserts every discovered same-basename group is either
    guarded or explicitly declared coincidental (`app.py` service entry points,
    `data_source.py` independent decoupled data layers) — a new undeclared
    vendored copy reddens this test.
- Left the existing per-module guards in place (belt-and-suspenders); the
  meta-test now also covers the same assertions from data.
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  → **2128 passed** (exit 0; 2098 baseline + 30 new: 2 accounting/liveness + 1
  byte-mode `listfilter` + 14 symbol-core functions + 13 symbol-core constants
  for `discord_auth`). Bite-tested: a semantic change to `_sign` in one
  `discord_auth.py` copy reddened exactly
  `test_symbol_core_function_does_not_drift[discord_auth.py-_sign]` and nothing
  else; a stray same-basename module reddened `test_no_undeclared_vendored_group`;
  both reverted → back to green.
  `python3 bootstrap.py check --strict` → exit 1 solely on THIS card's born-red
  `[session-card-hold]` (released at this flip); the remaining output is
  pre-existing advisories on unrelated cards (seat-digest-stale,
  orientation-headroom, seven model-line notices on the four 2026-07-19 cards) —
  never exit-affecting and not introduced here. The new test file adds zero
  findings.

## 💡 Session idea

**Promote `data_source.py`'s shared httpx-cache plumbing to a guarded core.** The
`botsite/` and `dashboard/` `data_source.py` copies are independently-authored
decoupled data layers (different feeds), but they already share a byte-for-byte
identical plumbing core — `_env_int`, `_get_client`, `_norm`, `set_client`,
`clear_cache`, and the `_cache`/`_client` module globals — inherited from the
same fetch-cache pattern. Today the meta-test declares `data_source.py`
coincidental; a successor could add a `symbol`-mode manifest entry for just that
plumbing subset so a cache/TTL bugfix in one copy that skips the other reddens,
exactly as the discord_auth core does. Worth having because it is a real shared
core (verified identical at HEAD) currently guarded by nothing, and the meta-test
now makes adding it a one-line manifest edit rather than a new hand-written test.
Deduped against `docs/ideas/backlog.md` + the queue-state NEXT list: the existing
vendored-copy-core-guard bullet is the meta-test THIS slice builds; a
`data_source`-specific promotion is not present. To capture in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-20-signal-registry-data-file.md` (#453, plan slice 4) landed
the committed signal registry with the right discipline — every row's
baker/mirror/consumer VERIFIED present in the tree and each consumer proven to
actually reference its signal, so the registry can't quietly list a dead
consumer. This slice carries that lesson forward to the vendoring side: the
meta-test's manifest entries are all VERIFIED against the tree (the discovered
dirs and the declared symbol core are asserted present in every copy, not merely
listed), and the accounting test guarantees the manifest can't silently omit a
newly vendored module.
