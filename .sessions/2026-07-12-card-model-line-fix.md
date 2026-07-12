# 2026-07-12 — housekeeping: family-level model line on the env-chip card

> **Status:** `in-progress` — branch `claude/card-model-line-fix`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · housekeeping fix

**What this session was about:** post-merge verification of PR #223 caught
its session card (`.sessions/2026-07-12-owner-readiness-env-chip.md`)
carrying an exact model ID string on the `📊 Model:` line. Fleet rule:
family-level names only (e.g. "Fable 5" / "Claude 5 family"), never an
exact model ID. This slice fixes just that one token — coordinator-assigned
housekeeping, not a work-ladder rung.

## What was done

- `.sessions/2026-07-12-owner-readiness-env-chip.md`: the `📊 Model:` line's
  model segment changed from the exact ID string to `Claude Fable 5` —
  matching how the sibling feature-slice cards of the same day phrase it
  (`2026-07-12-envhub-group-chips.md`, `2026-07-12-arcade-download-probe.md`:
  `Claude Fable 5 · worker · feature-slice`). No other content touched.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — [[fill: run at close]]; `python3 bootstrap.py check
  --strict` — [[fill: run at close]].

⚑ Self-initiated: no — coordinator-assigned post-merge verification pass
flagged the line; the fix is one token, contained and reversible.

## 💡 Session idea

**Align `.sessions/README.md`'s own model-line examples with the
family-level rule** — the README's ender checklist and template say
"FAMILY level only" but give `claude-fable-5` / `claude-opus-4-8` as the
examples, i.e. the exact-ID shape this very fix removes; many historical
cards copied that shape verbatim. Updating the two example strings to
"Fable 5" / "Opus 4.8" phrasing would stop the template from seeding the
exact-ID form into every future card. Worth having because the doc that
defines the rule currently demonstrates its violation, and agents copy
templates literally. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: nothing there touches the session-card template or
model-attribution examples. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The env-chip session (#223) did well — honesty ladder held end-to-end and
its one capture-miss (the #219 backlog bullet) was self-repaired; its one
miss was the `📊 Model:` line carrying the exact model ID instead of a
family-level name, fixed here.
