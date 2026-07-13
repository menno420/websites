# 2026-07-13 — structural clarity-bar gate: every HTML route proves its headline + lede

> **Status:** `complete` — branch `claude/clarity-structural-gate`; PR #241.

- **📊 Model:** Claude Fable 5 · worker · structural test gate

**What this session was about:** ORDER 022 item 1 follow-through, dispatched
by the coordinator — make tonight's clarity bar STRUCTURAL instead of
page-by-page. Both clarity sessions captured the same idea independently
(`.sessions/2026-07-13-clarity-control-plane.md` 💡 and
`.sessions/2026-07-13-clarity-botsite-dashboard.md` 💡; backlog bullet
"Structural clarity-bar gate" in `docs/ideas/backlog.md`): the ledes pinned
in `tests/test_clarity_ledes.py` and the PR #231 pins protect existing pages
only — a brand-new route can still ship below the bar. This session builds
one route-walking suite per service (tests/, botsite/tests/,
dashboard/tests/, review/tests/), shaped like
`review/tests/test_privacy_lint.py` (PR #233): route introspection over
`app.routes`, PARAM_EXPANDERS with two-way completeness guards, an explicit
documented classification for structurally-different responses, zero
network. Small in-idiom template lede fixes where a walked page genuinely
misses the bar.

## What was done

- **Four new suites**, one per service, each self-contained (no
  cross-service imports): `tests/test_clarity_structure.py` (5 tests),
  `botsite/tests/test_clarity_structure.py` (5),
  `dashboard/tests/test_clarity_structure.py` (4),
  `review/tests/test_clarity_structure.py` (4). Each introspects GET routes
  (recursing FastAPI's include_router wrapper so /owner and /testing are
  walked), expands parameterized routes from committed/fixture data, and
  asserts the service's own header idiom via a small HTML parse (class-SET
  matching, never attribute order): app/ = h2 + `p.dim.small` inside
  `div.card`; botsite = hero h1 + `p.sb-lead` (detail pages
  `div.sb-detail-head` h1 + `p.tagline`); dashboard + review =
  `section.sb-page-hero` h1 + `p.sb-lead`.
- **Routes walked**: app/ 50 concrete HTML URLs (22 plain incl. 5 gated
  /owner + 28 expanded: 9 projects, 9 prompt-history seats from roster, 4
  journal repos, 1 journal file, 5 envhub manifests) / 14 classified
  non-page (13 JSON twins + activity.xml); botsite 27 (13 plain incl. gated
  /testing/owner + 8 committed tasks + 2 features + 2 commands + the 2
  runtime-token pages reached via a REAL offline claim POST) / 5 non-page
  (healthz, version, palette.json, gated export.json, gated binary
  screenshots — ids not enumerable from committed data); dashboard 18 / 3
  non-page (healthz, version, palette.json); review 28 (10 plain + 17 fleet
  lanes + 1 edition, derived programmatically) / 5 non-page (healthz,
  version, story.json, fleet.json, feed.xml). /static exempted with reason
  + a serves-a-real-file check, all four services. 404 shapes pinned per
  service (control-plane: default JSON detail, documented; review's
  private-lane probes reference `fleetdata.PRIVATE_LANES`, never a literal).
- **Completeness both directions**: an unregistered parameterized route
  fails; a stale expander/registry entry fails; page/non-page overlap
  fails; mounts must equal the exemption set; per-service walk floors
  (30/20/15/20).
- **Misses found + FIXED (never allowlisted)**: 3 — botsite
  `testing_task.html`, `testing_submission.html`, `testing_guide.html` had
  a headline but no visible purpose lede; each gained a plain-words
  `p.sb-lead` in the hero.
- **Tamper-proof**: removed the sb-lead from
  `dashboard/templates/functions.html` locally → `CLARITY MISS —
  /functions: no visible <p class='sb-lead'> purpose lede inside
  section.sb-page-hero`, 1 failed; restored → green. Not committed.
- Backlog: "Structural clarity-bar gate" flipped `captured` → `built`
  (PR #241, all four services).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1006 passed, 1 warning** (after merging
  origin/main, which landed #239 mid-session — the new gate absorbed its
  new surfaces green); `python3 bootstrap.py check --strict` — green except
  this card's own designed born-red hold (cleared by this flip; one
  pre-existing never-exit-affecting owner-action advisory on
  control/status.md, untouched by scope).
- Evidence: commits `df66c54` (rails), `5b41348` (gate + fixes + flip),
  merge `031ca71`; PR #241.

⚑ Self-initiated: no — coordinator-dispatched ORDER 022 item 1
follow-through.

## 💡 Session idea

**Unify the hero-container idiom so the gate can tighten** — the walk
exposed real container drift the gate had to tolerate: botsite's home page
uses `section.hero` while every other page uses `section.sb-page-hero`,
and review's `not_found.html` renders headline+lede with no hero section at
all. Converge those two templates on `sb-page-hero` and the four suites can
drop their variant branches and assert ONE container idiom everywhere —
smaller tests, stricter gate, and a 404 page that finally matches its
siblings. Worth having because every tolerated variant is a place the next
copy-paste diverges further. Deduped against `docs/ideas/backlog.md` (the
clarity-gate bullet is now `built` and mentions no container unification;
nothing else touches hero/idiom convergence) and the queue-state NEXT list.

## ⟲ Previous-session review

The ORDER 041 prompt-surfacing session (PR #239, merged mid-way through
this one) is reuse discipline done right: both new surfaces ride the
EXISTING `prompt_history.history()` / `deployed_drift()` data paths (no
second fetch semantics, no stored prompt copies), degradation is stated on
the page rather than hidden, and its card names every plumbing addition
precisely. Two honest quibbles: its +10 pins report "984 passed" but no
negative control — nothing shows any pin was ever seen red, the very
evidence habit the #225 session modeled; and the card's "What this session
is about" stayed in present tense after the flip. Concrete cross-check from
this session: my gate walked its two new surfaces (`/projects/{package}`
strip, `/owner` rollup card) post-merge and both carry the full header
idiom — the merge absorbed cleanly.
