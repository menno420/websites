# 2026-07-12 — control-plane IA v2: category nav, Overview dashboard, category landings

> **Status:** `complete` — PR branch `claude/control-plane-ia-v2`; one slice,
> lands via the auto-merge-enabler on green.

- **📊 Model:** claude-fable-5 · websites worker · owner-directed (live feedback)

**What this session was about:** owner feedback, verbatim intent — the
console is "a lot of clicking and a lot of scrolling; the ideal interface
would feature a few MAIN CATEGORIES which feature SUBCATEGORIES, and clear
rows and better placed buttons", and cross-cutting concerns like prompts
and environments "belong in a single main section, easy to find, easy to
browse". This slice restructures the flat ~12-item console into a 2-level
hierarchy and finishes the single-canonical-home story for Prompts (the
Environments half landed in the parallel ORDER 021 hub, built on here).

## What was done

- **`app/nav.py` rewritten around `CATEGORIES`** — the whole IA as ONE
  plain-data structure (overview · work · history · console · owner, each
  with subcategory items carrying label / desc / primary action /
  optional sub-view links). Re-grouping a page is a one-line data move.
  `category_for()` drives the header's current-category highlight;
  `all_hrefs()` feeds the reachability test.
- **Header nav = the 5 categories** (base.html; the old "more ▾" overflow
  dropdown deleted — the hierarchy replaces it). Current category
  highlights on every page, including category landings.
- **Overview dashboard at `/`** (board.html + `_attention()` in main.py):
  a what-needs-attention strip (broken checks / deploy DRIFT / stale
  heartbeats — derived from data the home page already fetches, honest
  all-quiet state) + the category → subcategory map. The live readiness
  board still renders below — added-to, not replaced.
- **Category landing pages `/work` `/history` `/console`**
  (templates/category.html): each subcategory as a clear row — name +
  one-line purpose + a fail-soft live count chip where cheap (open queue
  asks, open orders, ideas, open reviews, recent PRs, seats, artifacts,
  directory surfaces; None → honest "—") + the primary action as a
  right-aligned button. Server-rendered, no JS, rows stack on a phone.
- **Prompts = single canonical home**: the two fleet-wide artifacts
  relabeled **Universal Startup** / **Universal Session-Ender** (the owner
  searched "universal session-ender" and the bare label drowned among the
  per-seat bodies) and the Universal group now renders FIRST on /prompts,
  above the per-seat listing; /projects + the dispatch screens link
  "browse all prompts →" instead of forking navigation.
- **Environments = the ORDER 021 hub**: `/owner/environments-hub` (landed
  in the parallel session, merged in) is the console category's canonical
  Environments entry; the public schemas view and live estate detail ride
  as labeled sub-links. This slice only placed it in the nav — no second
  consolidation built.
- **Every pre-existing route preserved** — nothing moved or redirected;
  pages that left the header stay ≤2 clicks away via home map / category
  landings (pinned by test).
- **Tests**: `tests/test_category_ia.py` (5-category nav, landing rows
  link every subcategory, manifest-wide non-404 reachability, Overview
  dashboard, attention-strip unit tests); `test_nav_manifest.py` /
  `test_nav_overflow.py` / `test_console_home.py` rewritten for the
  category world; universal-group-first pinned in `test_prompts.py`.
  Suite 393 green.

## 💡 Session idea

**Category-level Atom/JSON rollups** — worth having because each landing
page already computes per-page counts; exposing `/work.json` would give the
manager one poll for "how much is waiting on the owner" instead of four.

## ⟲ Previous-session review

Built directly on the nav-manifest pattern (#122/#137 — one data module,
templates iterate it, tests hold routes to it) and folded in the same-day
ORDER 021 environments hub rather than duplicating it; the list-IA row/chip
styling reuses the existing badge/card vocabulary, no new CSS system.
