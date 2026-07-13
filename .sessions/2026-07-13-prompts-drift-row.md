# 2026-07-13 — /prompts: deployed-vs-canonical drift row (ORDER 022 item 3)

> **Status:** `complete` — PR #234, branch `claude/prompts-drift-row`;
> reviewed (honest-state ladder, degrade paths, TTL-cache reuse, template
> self-containment re-verified against the diff — no fixes needed); lands
> via the pre-armed auto-merge on green.

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

**Surface source-header supersession warnings on /prompts artifact
cards** — the recon behind this session found /prompts pins and serves fm
`docs/prompts/v3/universal-startup.md` as a paste body while that file's
OWN header says "v3.3 (2026-07-12): SUPERSEDED AS THE GENERATION SOURCE —
historical template… Do not paste this file". The page presents the 26
artifacts as THE paste source, yet one of them self-declares do-not-paste
and the site renders it indistinguishably from the pasteable 25. Parse the
already-fetched body's header lines for supersession markers ("SUPERSEDED",
"Do not paste", "historical template") and render a loud warning chip on
that artifact's card, labeling its copy flow accordingly — zero new
network, same honest-degrade rules. Worth having because the drift row
just shipped keeps deployed-vs-canonical honest, but says nothing when the
canonical copy ITSELF disclaims being pasteable — an owner pasting from
/prompts today would paste a file whose own header forbids it, presented
as authoritative. Deduped: no supersession/do-not-paste/paste-source entry
in `docs/ideas/backlog.md`, and no supersession handling anywhere in
`app/`.

## ⟲ Previous-session review

`.sessions/2026-07-13-inventory-consistency-pin.md` (PR #225): strong
evidence discipline — it proved its new pin RED on the pre-fix drift via a
stash test before trusting the green, and let committed evidence (row K +
the real consumer) decide which inventory was right instead of assuming.
Its "895 passed (+4 new)" convention made this session's baseline a
subtraction, and its 💡 (code as the third inventory) was captured with
scope and dedupe already done — genuinely promotable. Nothing misleading
found; its never-silent-exemptions allowlist is the same honesty principle
this session's never-green-from-prose rule applies.
