# 2026-07-11 — Nav-scan glob: the guard drops its own hand-kept list (rung 3)

> **Status:** `complete` — PR #137, branch `claude/nav-scan-glob`.

- **📊 Model:** Claude Fable 5 · worker · routine-fired build slice (continuous mode, slice 30 — 15:07Z nudge) — family from this session's own harness, per ORDER 010.

**What this session was about:** the 15:07Z nudge; ritual clean (no new
orders, no collision; sibling PR #132 re-checked: open, green, updated
13:42Z ~87 min ago — under the 2h threshold, hands off), so rung 3 with
the small designated pick: **nav-scan glob** — the slice-24 self-caught
irony: `tests/test_nav_manifest.py` guards against hand-kept nav lists
via a hand-kept `ROUTE_SOURCES = [main.py, owner.py]` module list, so
splitting routes into a new module would silently exit the scan.

## What was done

- `tests/test_nav_manifest.py` — ROUTE_SOURCES hand list →
  `sorted((REPO_ROOT / "app").glob("*.py"))`; scan stays source-text
  based; comment records the why.
- Premise-checked BEFORE editing: the `active` regex over the whole
  package matches ONLY the ten real keys in main.py (zero false
  positives anywhere in app/*.py); owner.py contributing no keys keeps
  the no-dead-entries direction intact (globbing widens scanned files,
  never manifest keys).
- `docs/ideas/backlog.md` — glob bullet moved to Built; fresh 💡
  captured (hand-kept-list audit sweep, below).

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (regenerated from `git diff origin/main --stat`):**

- tests touched (1): `tests/test_nav_manifest.py` (+6/−2)
- docs touched (1): `docs/ideas/backlog.md` (close-out commit)
- sessions touched (1): `.sessions/2026-07-11-nav-scan-glob.md`
- git: branch `claude/nav-scan-glob`, born-red card first commit
  `c88bf26`, build commit `d0a6c06`, this close-out commit flips the
  gate.
- verify: nav modules 5/5; `python3 -m pytest tests/ -q` → **195 passed**
  (unchanged — a scan-scope widening: the same three assertions now
  cover every module, present and future); `bootstrap.py check --strict`
  before push → only the designed born-red HOLD (flips with this commit,
  PR #137).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: no D-entry — a test-scope fix inside an existing
  guard. Scope decision recorded: deliberately did NOT extend the regex
  or add tests — widening the scanned file set is the whole fix; new
  assertions would be makework.
- Next session should know: remaining buildable = inbox provenance
  advisory (next designated), hand-kept-list audit sweep (this slice's
  💡, a rung-5 candidate), latency-persistence manager ask,
  cross-service clock (dormant). Sibling #132 crosses the 2h stale
  threshold at ~15:42Z if untouched — the ~16:0xZ wake should apply the
  stranded-work check alongside its fire-rescue ritual.

## 💡 Session idea

**Hand-kept-list audit sweep** — captured in `docs/ideas/backlog.md`.
Worth having because this is the SECOND self-referential drift the chain
found in a guard (first: the overflow guard's markup/tuple duplication
that #122 fixed; now the membership guard's own module list): a one-off
rung-5 grep of tests/ and scripts/ for hard-coded path lists that shadow
a globbable truth either clears the class or finds the third instance —
and this failure shape recurs specifically in guards, where drift hurts
most.

## ⟲ Previous-session review

Slice 29 (#135 rollup + heartbeat #136): clean — the honest-None chain
(per-order → rollup → live verification) held at every level, and the
persistence ask on the bus is the right escalation: the remaining gap is
protocol-shaped, not code-shaped. Process note kept from this slice: the
premise check (grep before editing the guard) took 20 seconds and
converted "should be safe" into "verified: zero false positives" — the
cheapest evidence this chain buys.
