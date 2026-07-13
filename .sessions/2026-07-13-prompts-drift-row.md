# 2026-07-13 — /prompts: deployed-vs-canonical drift row (ORDER 022 item 3)

> **Status:** `in-progress` — branch `claude/prompts-drift-row`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker (order execution) · feature-build

**What this session was about:** ORDER 022 item 3 — /prompts
deployed-vs-canonical drift row. Add a per-seat drift row comparing the
canonical registry prompt vs the recorded deployed state, with an honest
"not recorded" where deployment isn't tracked. Rung: order — ORDER 022
item 3.

## What was done

- `app/prompts.py` — NEW `deployed_drift()` + `_build_deployed()`: one
  drift row per pinned artifact (8 seats × 3 families + the 2 universals =
  26 rows). CANONICAL side parses the already-fetched registry copy's
  version identity (in-paste `v3.5 <seat> CI …` line and/or `Provenance:`
  line, header-provenance fallback; honest "version line missing" when
  absent). DEPLOYED side uses the fleet's only committed deployment
  records, fetched over the same TTL-cached raw-content pattern: per-seat
  `projects/<seat>/meta.md` "Deployed-state per part" tables (both
  committed shapes parsed best-effort — the 4-column restructure-seat
  table and fleet-manager's 2-column one; prose can prove staleness,
  never byte-equality, so its best state is `recorded: <claim>` with
  verdict `stale`/`unverified`, NEVER "in sync") and
  `telemetry/triggers-snapshot.json` (ONE TTL-cached fetch, per-seat
  trigger lookup by squashed name; failsafe prompts are deliberately
  unstamped per registry doctrine §3, so the snapshot body vs the registry
  copy's "## Prompt text" fenced block is whitespace-normalized
  byte-compared → `in sync`/`drift`, as-of the snapshot's `captured_at`).
  Universals: `not recorded` by design (per-session pastes; the recon
  found no deployed record anywhere). Honest state ladder per row:
  in sync / drift / stale / unverified / not recorded / unreachable —
  404 = not recorded, network failure = unreachable, route always 200,
  equality never invented.
- `app/templates/prompts.html` — self-contained "Deployed vs canonical"
  card (`id="deployed-drift"`, inserted after the header card; the page
  header itself untouched — the PR #229 clarity session was editing
  headline blocks tonight): honesty-ladder explainer, per-state count
  chips, snapshot captured-at stamp, and the 26-row table (seat /
  artifact / canonical stamp / deployed record + as-of + reason / state
  chip).
- `tests/test_prompts.py` — 8 new offline tests (module 16 → 24), fixtures
  copied from the REAL committed shapes (fleet-manager@4124d7d meta.md
  tables + triggers-snapshot.json record shape): meta table parse →
  recorded/stale, 2-column shape → unverified, missing/unparseable
  meta.md → not recorded, snapshot byte-match → in sync + captured_at
  surfaced, snapshot body differs → drift + seat-missing-from-snapshot →
  not recorded, fetch error → unreachable (route stays 200), universals →
  not recorded, template smoke (section + chips + canonical stamps).
- Rendered against the real fleet-manager@4124d7d data (offline fixture
  run): 8 in sync (all 8 failsafes byte-match their snapshot triggers),
  5 stale, 1 unverified, 12 not recorded — e.g. websites Custom
  Instructions: canonical `v3.5 websites CI …` vs `recorded: DEPLOYED,
  but an OLDER text: the fm gen-2 fitted version … (as of 2026-07-10)` →
  stale.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **940 passed** (+8 new); `python3 bootstrap.py check
  --strict` — "all checks passed" (advisory warnings only, pre-existing).

⚑ Self-initiated: no — ORDER 022 item 3.

## 💡 Session idea

(pending — captured with its "worth having because" line and deduped
against `docs/ideas/backlog.md` before the close-out flip; honest
"nothing" if no idea earns its keep.)

## ⟲ Previous-session review

(pending — written at close-out.)
