# 2026-07-13 — clarity bar audit: control-plane pages state what they are, do, and offer

> **Status:** `complete` — PR #229, branch `claude/clarity-control-plane`;
> adversarial cross-check verdict SHIP; lands via auto-merge on green.

- **📊 Model:** Claude Fable 5 · worker · clarity audit + fixes

**What this session was about:** OWNER ORDER 022 (night run — dispatched by
coordinator; note: order text not yet at this repo's inbox HEAD at boot,
proceeding on coordinator dispatch) — clarity bar on every control-plane
page: each page immediately shows WHAT it is, WHAT it does, and its most
important features; audit all app/ pages, fix every miss. Scope: app/
templates+routes + tests/ only.

## What was done

- **Audit**: all 24 control-plane pages checked against the clarity bar
  (live pages + their templates) — 19 PASS / 5 MISS. The five misses:
  `/activity`, `/reviews`, `/journal/search`, `/journal/{repo}`,
  `/journal/{repo}/file` — all missing a visible plain-words purpose lede
  (help text existed only behind pagehelp); `journal_repo` additionally
  missing a page-type headline, jump pills, and a back-link.
- **Fixes** (all 5 misses): `app/templates/activity.html` +
  `app/templates/reviews.html` + `app/templates/journal_search.html` +
  `app/templates/file.html` gained visible one-line plain-words ledes under
  the h2; `app/templates/journal_repo.html` gained a purpose h2, a
  back-link to `/journal`, a visible lede, jump pills with section ids
  (#sessions/#docs/#prs/#commits), and its note demoted below the lede.
- **Contained extras**: `board.html` tab title aligned with the overview h2
  (+ readiness.json link); headright JSON feed links added on board, fleet,
  queue, projects (the activity idiom); `orders.html` h2 heartbeat clause
  swapped for plain words.
- **Pins**: `tests/test_clarity_ledes.py` — 10 new offline tests pinning
  every lede, the journal_repo anchors/pills/back-link, and the feed links.
- Adversarial cross-check verdict: **SHIP** — contexts, anchors, feed
  routes, and copy all verified against `app/main.py` + `app/journal.py` +
  `app/reviews.py`.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 905 passed, 1 warning; `python3 bootstrap.py check
  --strict` — green (card hold released by this flip).
- Evidence: commits `eaf922e` (rails: born-red card + claim) + `f776d2e`
  (fixes, 11 files, +191/−12); PR #229.

⚑ Self-initiated: no — OWNER ORDER 022 night run, dispatched by the
coordinator.

## 💡 Session idea

**Structural clarity-bar gate** — a test that walks every registered page
route on the control-plane app and asserts the header idiom (h2 with
em-dash purpose + `p.dim.small` lede), so a NEW page can never ship below
the clarity bar. Worth having because it turns tonight's one-off manual
24-page audit into a permanent structural gate — the 10 ledes pinned in
`tests/test_clarity_ledes.py` protect existing pages only; a route-walking
assert protects pages that don't exist yet. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: nothing there touches
the clarity bar or a header-idiom gate. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The inventory-consistency-pin session (#225) did exemplary evidence work —
it proved its pin red on pre-fix main before trusting it green, and its
allowlists check (service, variable) pairs so an exemption can't silently
widen; its card even surfaced a third-inventory gap as the idea. One miss:
its `📊 Model:` line uses the exact-ID shape (`claude-fable-5`) the README
mandates against — the very drift PR #226 later swept.
