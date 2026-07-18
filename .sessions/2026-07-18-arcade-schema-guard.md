# 2026-07-18 — Arcade JSON schema CI guard (A4)

> **Status:** `complete` — branch `claude/arcade-schema-guard`; a new
> read-only schema guard over the committed `botsite/data/arcade.json`, added
> to `botsite/tests/test_arcade_registry_integrity.py`. Test-only: no product
> code or data changes. Asserts every arcade entry through the shipped
> `botsite.arcade` schema constants (required fields, `maturity` /
> `availability` enums, blocker shape, link-URL presence, unique slugs, no
> unknown top-level keys) plus an inline malformed-sample assertion proving the
> validator has teeth.

- **📊 Model:** Claude Opus · high · test writing (arcade schema guard)

**What this session is about:** the Fleet Arcade renders the public front door
for the fleet's playable games from a committed JSON registry
(`botsite/data/arcade.json`), read at request time by `botsite/arcade.py`. The
loader is deliberately fail-soft (the "never fake data" doctrine): an entry
missing a required field, or carrying an out-of-enum `maturity` / `availability`
value, is silently *skipped* — it does not crash, it just quietly disappears
from the arcade with no signal. A game marked `availability: "live"` (or
`"download"`) but with a null/blank `url` is likewise silently demoted out of
its link-bearing state (`has_link` false). That is the right *runtime* behaviour
but it means a malformed *committed* entry fails silently: a new game could be
added to the registry and never show up, with nothing red to catch it. A4
closes that gap with a CI guard: a schema/enum/blocker/url violation in
`arcade.json` now reds the build. Test-only — no route, no template, no
serialized payload, no env, no product code touched.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (A4).

## Close-out

**Evidence:**

- files touched this branch: `botsite/tests/test_arcade_registry_integrity.py`
  (extended in place — the existing blocker-integrity guard already owns the
  committed-registry-shape story; A4 adds arcade-specific schema assertions
  beside it rather than duplicating a second module) — a per-entry schema guard
  that loads the real committed `arcade.json` and asserts, for every entry:
  each `botsite.arcade._REQUIRED` field is a present non-empty string;
  `maturity ∈ arcade.MATURITIES`; `availability ∈ arcade.AVAILABILITIES`;
  `url` is null-or-string and, when `availability ∈ arcade.LINKED_AVAILABILITIES`
  ("live"/"download"), a non-empty well-formed `http(s)://` URL (the exact
  silent-demotion the loader would otherwise swallow); no unknown/typo
  top-level key (allowed = `_REQUIRED` ∪ {`url`, `status_note`, `blocker`});
  blocker sub-keys ⊆ {`owner_action`, `unblocks`, `ask_id`} when present; and
  slugs unique. All invariants are imported from `botsite.arcade` /
  `botsite.blockers` — never re-stated — so the guard cannot drift from the
  code the service actually runs. A committed `_MALFORMED_ARCADE_SAMPLES` table
  drives a parametrized negative test asserting the validator REJECTS each
  known-bad entry (bad enum, missing field, live-with-null-url, unknown key),
  so the negative case ships as a real committed assertion. This card +
  `control/status.md` heartbeat.
- git: branch `claude/arcade-schema-guard` from `origin/main` @ `258343f`
  (#389); commits `a71c020` (born-red card), `89dba99` (guard build + committed
  malformed-sample teeth), `454b6ec` (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests
  -q` — **1763 passed, 1 warning** (exit 0); `python3 bootstrap.py check --strict` (and
  `--require-session-log`, the CI form) — the only red during the session was
  the DESIGNED born-red hold on this card, released at this flip. No serialized
  JSON payload / env / contract changed — the guard is a test that reads the
  committed registry, so no contract-pin (`test_json_contracts` /
  `test_fleet_json_contract` / `test_hostile_env_smoke` / `test_env_poison_pin`)
  moved and no new env read was added.
- guard-has-teeth: confirmed the parametrized negative test FAILS the validator
  on each malformed sample and the positive test PASSES on the real committed
  `arcade.json` (both reported to the coordinator).

**Judgment:**

- Decisions made: (1) EXTEND `test_arcade_registry_integrity.py` rather than add
  a new module — that file already is the committed-registry-shape guard (it
  owns the blocker/ask-id/duplicate-slug story across all four registries); the
  arcade schema guard is the same read-only, import-the-shipped-schema discipline
  applied to arcade's own field/enum/url invariants, so it belongs beside them.
  (2) Import every invariant from `botsite.arcade` (`_REQUIRED`, `MATURITIES`,
  `AVAILABILITIES`, `LINKED_AVAILABILITIES`) and `botsite.blockers` — the guard
  reflects REAL code invariants, never re-stated guesses, so a future schema
  change moves both the loader and the guard together. (3) The link-URL
  assertion targets `LINKED_AVAILABILITIES` specifically — a "live"/"download"
  entry with a null/blank url is the precise silent demotion (`has_link` false)
  the loader swallows, and is exactly the "new game silently drops from the
  arcade" failure A4 exists to catch; an "unavailable" entry with a null url is
  legitimate and left alone. (4) Ship the negative case as a committed
  parametrized assertion over an inline malformed-sample table rather than by
  mutating the real file — the validator's teeth become a permanent regression
  test, not a one-off manual check. (5) Test-only: no product code, no data,
  no payload/env — nothing to contract-pin.
- Next session should know: `test_arcade_registry_integrity.py` now carries
  BOTH the cross-registry blocker guard and arcade's per-entry schema guard;
  the allowed top-level key set is derived from `arcade._REQUIRED` plus the
  three optional keys the loader reads — a NEW optional field added to the
  arcade schema must be added to that allow-set or the guard will red it (that
  is the guard working, but it is the one line to update deliberately).

## 💡 Session idea

**Promote the arcade `_valid`/schema check into a shared registry-schema
descriptor the loader and the guard both consume.** Today the guard re-lists
which keys are allowed/required by reading `arcade._REQUIRED` and hand-adding
the three optional keys (`url`, `status_note`, `blocker`); the loader knows the
same shape implicitly in `_valid` + `load_games`. A small declarative schema
object on `botsite/arcade.py` (required fields, optional fields, per-field
validator) that BOTH `_valid` and this guard import would make "what is a valid
arcade entry" single-source instead of split across a loader function and a test
allow-set — the same catalog/products/museum registries could adopt the same
descriptor, turning four ad-hoc `_valid`s into one enforced schema and letting
the integrity guard cover every registry's field-shape the way it already
covers every registry's blocker-shape.

## ⟲ Previous-session review

`.sessions/2026-07-18-console-honest-counts.md` (C1) turned four silently-faked
`0` counts into an honest `—` by reusing each source's OWN error signal rather
than inventing a new one — the same reflect-real-code-invariants discipline this
A4 guard follows: it asserts through `botsite.arcade`'s shipped schema constants
instead of re-deriving them, so the guard can never claim an invariant the
loader does not actually enforce. C1's closing note explicitly recommended A4 as
the next slice; this card is that slice.
