# 2026-07-20 — committed signal-registry data file (cross-repo signal → baker → raw-URL → consumers)

> **Status:** `in-progress` — branch `claude/signal-registry-data-file`; flips
> to `complete` + PR number as the deliberate LAST code step. Born red: this
> card's in-progress Status holds the `quality` gate red until the registry +
> its schema/consumer-reachability test land green; the flip to `complete`
> releases the `[session-card-hold]`.

- **📊 Model:** opus-4.8 · low · data registry + test

**What this session is about:** the four services now bake / mirror several
cross-repo signals into `*/data/*.json` and re-render them on sibling surfaces —
three raw feeds fetched from `menno420/superbot` (the botsite marketing
`site.json`, the dashboard inventory `dashboard.json`, the console board
`console.json`), review's baked release-drift mirror (`review/data/releases.json`),
and the two in-repo registries the drift guard already joins (the fleet-arcade
`botsite/data/arcade.json` and the web-presence directory
`app/data/web_presence.json`). Nothing records, in one committed place, WHICH
file bakes each signal, WHERE consumers fetch it, and WHICH surfaces re-render
it — so each new drift/parity fan-out (like the release-drift parity in
`.sessions/2026-07-18-release-drift-parity.md`) is a code hunt across services.
This session commits that lookup as data (`docs/signal-registry.json`) and pins
it with a schema + consumer-reachability test that generalises the join pattern
`tests/test_registry_drift.py` already proves for the arcade↔web-presence pair.

Work-ladder rung: coordinator-assigned build — plan slice 4 of
`docs/plans/next-cycle-2026-07-19.md` (also the standing NEXT-2 baton item and
the 💡 of `.sessions/2026-07-18-release-drift-parity.md`).

⚑ Self-initiated: no — coordinator-assigned slice, promoting the release-drift
parity card's 💡 ("a tiny committed signal registry — name → baker → raw URL →
consumers") from a flagged idea into committed data + a guard.

## Plan

- Commit `docs/signal-registry.json` — a cross-cutting registry (docs is the
  cross-service home; the signals span all four services, so it lives in no
  single service's `data/` dir). One row per baked/mirrored cross-repo signal,
  each carrying: `name`, `description`, `producer_repo`, `baker` (in-tree
  generator path, or `null` for a PR-maintained / cross-repo-baked signal),
  `committed_mirror` (in-tree committed JSON path, or `null` when the mirror
  lives in another repo), `raw_url` (the raw.githubusercontent URL consumers
  fetch), and `consumers` (in-tree files that re-render / read the signal).
  Rows are REAL, verified against the tree — no invented entries.
- Add `tests/test_signal_registry.py` (the cross-service test dir, alongside
  `test_registry_drift.py`): a schema test (required keys per row, types,
  non-empty, unique names, well-formed raw_url) and a consumer-reachability test
  (every `consumer`/`baker`/`committed_mirror` path resolves in the tree, and
  every consumer file actually references the signal by its mirror basename —
  the join generalisation, so a declared consumer that stopped consuming the
  signal fails the guard).

## What was done

- `docs/signal-registry.json` — the committed registry, one row per cross-repo
  signal (superbot `site.json` / `dashboard.json` / `console.json` feeds,
  review's `releases.json` release-drift mirror, the `arcade.json` +
  `web_presence.json` in-repo registries). Each row's `baker`,
  `committed_mirror`, `consumers` verified present in the tree.
- `tests/test_signal_registry.py` — schema validation + consumer-reachability
  join test over the JSON (each consumer file references its signal's mirror
  basename, generalising `test_registry_drift.py`'s registry join).
- Verified (CI-equivalent, `DATABASE_URL` unset):
  `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — <fill at flip: N passed>; `python3 bootstrap.py check --strict` —
  <fill at flip: verdict>.

## 💡 Session idea

**Make the drift/parity guards READ the registry instead of hardcoding consumer
paths.** `tests/test_registry_drift.py` and `tests/test_release_drift_parity.py`
each hardcode the pair of surfaces they join; now that `docs/signal-registry.json`
lists every signal's consumers as data, a successor could have those guards
DERIVE their consumer set from the registry row — so adding a new parity fan-out
(a fourth surface that re-renders release-drift, say) is a single registry edit
that automatically extends the drift guard, rather than a registry edit PLUS a
hand-patched test. Worth having because it closes the loop the registry opens:
the registry stops being passive documentation and becomes the single source the
guards enforce against, so a consumer listed-but-not-guarded (or guarded-but-not-
listed) can't silently diverge. Deduped against `docs/ideas/backlog.md` + the
NEXT-2 baton (slice 5 is the vendored-copy AST guard — unrelated): not present.
To capture in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-askverify-discord-submit-probes.md` (#451, plan slice 3)
did the honest thing by keeping the askverify registry STRUCTURE untouched —
converting two `probe=None` slots and prepending a Discord-302 signal to the
existing SITE_PASSWORD probe rather than minting new entries — so every registry
invariant (open-ask count, unique ids, distinct signatures) held with no
rebind, and it derived each done/still-open verdict from a real live status code
(302 vs 200, live-badge vs stub body) instead of inferring it. The lesson this
slice carries forward: that card proved the value of a signal being *observed,
not invented* — and this registry applies the same discipline to the committed
side, where every row's baker/mirror/consumer is VERIFIED present in the tree
(and each consumer proven to actually reference its signal) rather than asserted,
so the registry can never quietly list a consumer that stopped consuming.
