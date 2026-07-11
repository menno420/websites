# 2026-07-11 — quality.yml every-card gate port (rung 3, backlog promotion)

> **Status:** `in-progress` — branch `claude/quality-every-card-gate`; flips
> to `complete` + the real PR number after the PR exists.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 23 — 10:55Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 10:55Z nudge; ritual clean (no new
orders, no collision), so rung 3 with the twice-deferred designated pick:
**port the kit v1.10.1 every-card session gate into the live folded
`quality.yml` lane**. The live workflow still derives the PR's card with a
`tail -1` single-card picker — the exact multi-card shadowing shape the
staged `.substrate/ci/substrate-gate.yml` fixed: a PR that ADDS a born-red
card and MODIFIES a later-sorting sibling grades only the sibling and
ships the in-progress card green. CI-integrity slice: quality.yml IS the
required check, so the port is validated on this PR's own runs — and
because this PR both adds a card AND touches the gate file, it exercises
the new gate-regen locked-door branch live (semantics may only tighten
mid-PR).

## What was done

- (work in progress — filled at close-out)
