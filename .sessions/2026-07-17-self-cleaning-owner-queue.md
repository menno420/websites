# 2026-07-17 — Self-cleaning owner queue (C14)

> **Status:** `in-progress` — branch `claude/self-cleaning-owner-queue`; born-red
> card (this commit). Extends `app/askverify.py` so an open ⚑ owner-action
> auto-clears out of the gated `/owner/queue` the moment its underlying
> condition is POSITIVELY confirmed resolved — and, fail-soft, never on a fetch
> error, timeout, unknown, or ambiguous state. Flips to `complete` as the last
> commit, releasing the designed born-red gate hold.

- **📊 Model:** `[[fill:model-line at flip]]`

**What this session is about:** the launch-preflight machinery (`app/askverify.py`,
2026-07-15) already probes each open owner-action and attaches a read-only
verdict chip — `done-detected` / `still-open` / `not-machine-checkable` /
`unknown`. But a `done-detected` ask still sat in the gated `/owner/queue`
nagging: the probe knew the condition was resolved, yet the queue never shrank.
C14 (console menu **C14**, NEXT-TASKS §1 · P1) closes that loop — a positively
re-verified ask auto-clears into a separate "self-cleaned this pass" section,
out of the active nag list, so the queue shrinks itself and less owner attention
is burned.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (C14) of the standing
overnight ORDER 032.

## Plan

- **`app/askverify.py`** — extend `annotate()` (do NOT rewrite the probe/registry
  machinery): stamp each item `auto_cleared` True only when its verdict is the
  positive `DONE` rung, add a `rollup["auto_cleared"]` count, and add a
  `split_self_cleaned(items)` helper returning `(active, cleared)`.
- **CRITICAL FAIL-SOFT INVARIANT:** `auto_cleared` is set True ONLY on a positive
  `DONE` verdict (the probe POSITIVELY observed the condition resolved). Every
  other rung — `still-open`, `not-machine-checkable`, ambiguous, `unknown`, a
  fetch error, a timeout, a raised probe exception — leaves the ask active. When
  in doubt, keep the ask; a real owner request never silently vanishes.
- **`app/owner.py` `_render_owner_queue`** — split the annotated items and pass
  the active + auto-cleared lists to the template (gated view only; the public
  `/queue` overview stays byte-identical, its contract pin untouched).
- **`app/templates/owner_queue.html`** — main loop renders the active asks; a new
  dim "self-cleaned this pass — ledger update pending" section lists the
  auto-cleared ones with their done-detected chip and a keep-the-mark-complete
  affordance (the human ledger row still moves).
- **`tests/test_askverify.py`** — add the four C14 cases: (a) positively-resolved
  ask auto-clears; (b) still-unmet ask stays; (c) fetch-error / raised-exception /
  unreachable source STAYS (the load-bearing fail-soft case); (d) the split
  helper + rollup shape hold. Contract pins re-checked (no serialized-JSON change).

## Close-out

**Evidence:** `[[fill:evidence — files, SHAs, verify output at flip]]`

**Judgment:** `[[fill:decisions + next-session note at flip]]`

## 💡 Session idea

`[[fill:session-idea at flip]]`

## ⟲ Previous-session review

`[[fill:previous-session review at flip]]`
