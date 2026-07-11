# 2026-07-11 — Nav manifest: one list drives the nav and its membership test (rung 3)

> **Status:** `complete` — PR #122, branch `claude/nav-manifest`.

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 24 — 11:30Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 11:30Z nudge; ritual clean (no 12:00Z
fire visible, no new orders, no collision), so rung 3 with the designated
pick: **nav manifest** — the slice-19 idea. The "which pages live under
more ▾" decision existed twice by hand (template markup in base.html +
GROUPED/PRIMARY tuples in tests/test_nav_overflow.py); page 12 could be
added top-level with nobody noticing the overflow guard was the point.
One `(href, label, key)` manifest now drives both the template and the
membership test, and a test asserts every `active` key the routes
actually pass appears in the manifest.

## What was done

- `app/nav.py` (new) — the single manifest: `PRIMARY` (5) + `GROUPED` (5)
  entries of `(href, label, key)`, plus `keys()`.
- `app/main.py` — manifest registered as Jinja globals
  (`NAV_PRIMARY`/`NAV_GROUPED`); import added.
- `app/templates/base.html` — nav markup iterates the manifest;
  `more_active` derives from the grouped keys; rendered structure
  identical (overflow tests unchanged and green).
- `tests/test_nav_overflow.py` — hand-kept tuples replaced with imports
  from the same manifest the template renders.
- `tests/test_nav_manifest.py` (new, +3) — every `active` key the routes
  pass (regex scan of app/main.py + app/owner.py) must be in the
  manifest; keys/hrefs unique + entries complete; no dead manifest
  entries (a key no route uses fails too).
- `docs/ideas/backlog.md` — nav-manifest bullet moved to Built; fresh 💡
  captured (glob the scan sources, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (corrected — the auto-collected list was tree-wide/polluted by
sibling merges; regenerated from `git diff origin/main --stat`):**

- code touched (2): `app/nav.py` (new), `app/main.py`
- templates touched (1): `app/templates/base.html`
- tests touched (2): `tests/test_nav_manifest.py` (new, +3),
  `tests/test_nav_overflow.py` (retargeted to the manifest)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-nav-manifest.md`
- git: branch `claude/nav-manifest`, born-red card first commit `6dbb4a8`,
  build commit `fdb8948`, this close-out commit flips the gate.
- verify: `python3 -m pytest tests/ -q` → **182 passed** (179 + 3 new);
  nav tests 5/5; `python3 bootstrap.py check --strict` run BEFORE the
  first push → only the designed born-red HOLD on this card (flips with
  this commit, which carries the real PR number #122).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — presentation/test-infrastructure change
  inside the existing routes→templates layer; no route, payload, or
  JSON-contract impact (contracts explicitly untouched per the nudge).
  Manifest shape decision (two lists + keys(), dicts not tuples for
  template readability) recorded here.
- Next session should know: the nav is manifest-driven — add pages in
  `app/nav.py`, never in base.html markup; the membership test also
  fails on DEAD manifest entries, so removing a page means removing its
  manifest entry in the same PR. Dashboard's nav already iterates a
  manifest (checked — no port needed there). Remaining buildable:
  fast-lane control gates port, route-level clock freeze, order-ack
  latency line, + this slice's glob-scan bullet.

## 💡 Session idea

**Nav membership scan should glob `app/*.py`, not a hand list** —
captured in `docs/ideas/backlog.md`. Worth having because
`tests/test_nav_manifest.py` scans a hand-kept
`ROUTE_SOURCES = [main.py, owner.py]` for active keys: the guard against
hand-kept nav lists itself contains a hand-kept module list, and
splitting routes into a new module would silently exit the scan —
self-maintaining guards should not carry the exact failure mode they
guard against.

## ⟲ Previous-session review

Slice 23 (#120 every-card gate + heartbeat #121): clean — the port's
live validation across its own three runs (gate-regen HOLD, flip green,
main-push green) is the strongest evidence pattern this chain has used;
this slice benefited directly: the born-red first run printed the new
per-card added-card banner exactly as documented. Workflow improvement
kept: strict gate BEFORE first push again cost zero fixup commits. One
premise-check win to repeat: this slice's first idea candidate
("dashboard nav manifest port") died on a 30-second source check — the
dashboard nav already iterates a manifest; check the premise before
capturing an idea.
