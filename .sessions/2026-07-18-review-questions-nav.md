# 2026-07-18 — Surface /questions in the review NAV (R1)

> **Status:** `complete` — branch `claude/review-questions-nav`; the built
> `/questions` answer-debt ledger page (real reviewer questions asked → where
> the answer landed, with an honest empty state and an answer-debt nag) already
> renders but was reachable ONLY by typing the URL — it was absent from the
> review site NAV, so a reviewer browsing the header never discovered it. R1
> adds a `/questions` entry to the review NAV (`review/app.py` `NAV` list,
> rendered by the shared `base.html` nav loop) and gives the route its own
> active state. NAV/template only — no product logic, no serialized JSON/env, no
> change to `data/questions.json` (its empty state is deliberate), no route
> behaviour change; the link is GET, so the CSRF/same-origin floor is untouched.

- **📊 Model:** Claude Opus · high · feature build — review /questions NAV visibility

**What this session is about:** the review service already ships a full
`/questions` page — the questions-asked → answered ledger, with a closed-without-
an-answer debt nag, an answer-latency median stat, and (by design) an honest
empty state over the deliberately-empty committed `data/questions.json`. The one
gap is discoverability: the page is a first-class surface but the header NAV
(Overview, Process, Growth, Fleet, Reviews, Q&A, Ask AI, Successes, Problems)
never listed it, so it was invisible to a reviewer who did not already know the
URL. R1's safe slice is purely navigation-visibility: add `/questions` to the
NAV so reviewers can reach it. The empty state and the ledger's read-only intake
convention are left exactly as they are.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (R1).

## Close-out

**Evidence:**

- files touched this branch:
  - `review/app.py` — added `("questions", "Answer log", "/questions")` to the
    `NAV` list, placed directly after the `Q&A` (`/questionnaire`) entry as its
    ledger companion; and changed the `/questions` route's `_base_ctx` active
    arg from `"questionnaire"` to `"questions"` so the header highlights the
    ledger link (its own `aria-current="page"`) rather than its Q&A sibling.
    The shared `review/templates/base.html` nav loop renders the new entry
    automatically in both the desktop bar and the mobile drawer — no template
    edit needed.
  - `review/tests/test_questionnaire.py` — extended + added coverage (below).
- test coverage (2): `test_nav_covers_all_sections` extended to also require
  `href="/questions"` in the rendered header; new `test_nav_surfaces_questions_
  ledger` asserts the home NAV links `/questions`, that `/questions` still
  returns 200 with its honest empty state ("No external reviewer questions on
  record yet"), and that on the ledger page its own NAV entry carries
  `aria-current="page"` (the active-state half). A regression on the NAV
  visibility OR the active-state fix is now caught.
- git: branch `claude/review-questions-nav` from `origin/main` @ `38066c4`
  (#393); commits `11159cd` (born-red card), `2ee8f6f` (the NAV + active-state
  change), `1360976` (the 2 tests), `1c068b4` (heartbeat status), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1807 passed, 1 warning** (exit 0; 1806 + 1 new NAV test); `python3
  bootstrap.py check --strict` and `--require-session-log` — both exit 0, the
  only red the DESIGNED born-red hold on this card, released at this flip. The
  one advisory warning is pre-existing and on another session's card, not this
  work — this card files the valid `feature build` PL-004 class.

**Judgment:**

- Decisions made: (1) Label — `Answer log`, not another "Q&A": the existing
  `Q&A` entry is the curated FAQ (`/questionnaire`), while `/questions` is the
  live ledger of real asked questions and their answer debt; two near-identical
  labels adjacent would confuse, so the ledger gets a distinct name that reads
  as its function. (2) Active state — gave `/questions` its OWN active id
  (`"questions"`) rather than leaving it piggy-backed on `"questionnaire"`, so
  the header highlights the page you are actually on; a side effect is the
  page's prefilled ask-issue topic now reads "questions page" instead of
  "questionnaire page" (more accurate — no test pinned the old wording, and it
  is not a serialized payload). (3) Scope — did NOT touch `data/questions.json`
  or the empty-state markup: the ledger starts empty on purpose, so R1 is purely
  a reachability add, not a content or design change.
- Next session should know: the review NAV is a single hand-maintained list in
  `review/app.py` (`NAV`), and adding a page there is the whole ceremony — but
  nothing FAILS when a new built page is left out (R1 was exactly that: a
  first-class page invisible for want of one list entry). The session idea below
  proposes a route-introspection guard so the next such orphan is caught
  automatically rather than by backlog-spotting.

## 💡 Session idea

**A NAV-completeness guard for the review service.** R1 fixed a page that
existed and returned 200 but was silently missing from the header NAV — nothing
failed, it was just undiscoverable until a human noticed. A lightweight review
test could introspect the FastAPI router (`app.routes`), collect every `GET`
route that returns an HTML page, and assert each is either present in the `NAV`
manifest OR on a small explicit allow-list of detail/sub-pages that are reached
by link rather than nav (`/fleet/{repo}`, `/reviews/{slug}`, error/probe
routes). It is the INVERSE of the existing `test_nav_covers_all_sections` (which
proves the NAV entries render) — a registration-completeness check that a newly-
built top-level page cannot ship orphaned from the nav. Distinct from the
arcade card's rendered-link-graph "no internal dead end" idea: that walks
in-body `href` anchors across botsite pages to find one-way dead ends; this is a
static check of the review router's DECLARED routes against the NAV list, needing
no rendering — the two are complementary (declared-vs-manifest here, rendered-
reachability there).

## ⟲ Previous-session review

`.sessions/2026-07-18-arcade-games-crosslink.md` (A2) added the missing reverse
cross-link so botsite's `/arcade` and `/games` became mutually reachable — the
same discoverability instinct as R1: a built surface that already worked but
could not be reached from where a visitor actually browses. A2 fixed an in-page
dead-end link; R1 is the header-NAV cousin (a page absent from the nav manifest),
and both pin the fix with a test that asserts the reachability property directly
rather than trusting the surface.
