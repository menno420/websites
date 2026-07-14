# 2026-07-13 — single source of truth for link-bearing arcade availabilities

> **Status:** `complete` — branch `claude/arcade-link-truth-0713`; PR opened
> ready (non-draft) right after this flip and lands via the auto-merge
> enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion-slice

**What this session was about:** backlog promotion — the
`docs/ideas/backlog.md` bullet "Single source of truth for link-bearing
arcade availabilities" (`captured` 2026-07-12, arcade download-probe session
💡). The /arcade page's `has_link` hardcoded `("live", "download")` in
`botsite/arcade.py` and the drift probe duplicated the same tuple as
`arcade_probe.PROBED_AVAILABILITIES` — two copies of the doctrine "which
availabilities carry outbound links" that nothing pinned together; the next
link-bearing availability value added to one and not the other would have
silently dropped out of probe coverage, exactly like the `download` gap
PR #220 closed.

## What was done

- `botsite/arcade.py`: new `LINKED_AVAILABILITIES = ("live", "download")`
  constant next to `AVAILABILITIES` — the ONE definition of which
  availabilities carry an outbound link; `has_link` (load_games) now
  consumes it instead of its inline literal.
- `botsite/arcade_probe.py`: `PROBED_AVAILABILITIES` is now defined AS
  `arcade.LINKED_AVAILABILITIES` (identity, not a second literal), with the
  comment updated to name the single source of truth. No behavior change —
  the tuple's value is identical.
- `botsite/tests/test_arcade_probe.py` (+3): the pin
  `test_probe_coverage_is_the_pages_linked_set` asserts
  `PROBED_AVAILABILITIES is arcade.LINKED_AVAILABILITIES` (and set-equality);
  `test_linked_availabilities_are_valid_and_exclude_unavailable` pins the
  constant as a duplicate-free non-`unavailable` subset of `AVAILABILITIES`;
  `test_probe_partitions_registry_exactly_by_linked_availabilities` proves
  the probed/skipped partition tracks the constant for every registry
  availability (no list hardcoded in the test).
- `botsite/tests/test_arcade.py` (+1):
  `test_has_link_covers_exactly_the_linked_availabilities` proves a
  URL-bearing entry gets `has_link`/`link_url` for EVERY linked availability
  and for NO other one.
- `docs/ideas/backlog.md`: the source bullet flipped `captured` → `built`
  (only that bullet's lines touched — PR #286 also edits this file at EOF).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1232 passed, 1 warning (+4 over main's 1228);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on control/status.md
  (not owned here).

⚑ Self-initiated: no — backlog promotion of the captured 2026-07-12 bullet
(`docs/ideas/backlog.md` "Single source of truth for link-bearing arcade
availabilities"); contained (botsite/arcade.py + botsite/arcade_probe.py +
botsite/tests + the backlog bullet flip) and reversible.

## 💡 Session idea

**Store buy-link drift probe — cold-fetch products.json + catalog.json
buyable URLs in the healthcheck** — the fleet now runs TWO fail-soft URL
drift probes (`arcade_probe`, `testing_probe`, both riding the 6-hourly
`scripts/healthcheck.py`), but the store surfaces (`botsite/products.py` +
`botsite/catalog.py`, whose buyable entries render real Gumroad buy links)
have none: reuse the shared `arcade_probe.probe_url` verdict logic (the
`testing_probe` pattern — import, don't fork) over every `buyable` entry's
URL. Worth having because a dead BUY link burns money and trust faster than
a dead game link, and today nothing re-verifies the store's one live Gumroad
URL after its card ships. Deduped against `docs/ideas/backlog.md` (including
today's two fresh rows) + the queue-state NEXT list: the storefront-freshness
bullet is TIME-based (`as_of` horizon), the catalog sha-drift bullet compares
provenance pins, and the tester-task host-pinning bullet covers
`testing_tasks.json` hosts — nothing cold-fetches store buy links. NOT yet
captured as a backlog bullet in this PR: open PR #286 appends to
`docs/ideas/backlog.md` at EOF, so this session deliberately touched only its
own bullet's lines — capture this idea as a new row in a follow-up
`control`-lane pass once #286 lands.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 packets
hand-curated with each status derived from its packet's own Status/Verdict
text plus a committed-registry pin freezing the 1/12/2/7 breakdown; what it
missed: everything it shipped decays silently against venture-lab HEAD — it
saw this itself (its sha-drift-pin 💡) but landed no guard, so the catalog's
honesty currently has a shelf life with no alarm.
