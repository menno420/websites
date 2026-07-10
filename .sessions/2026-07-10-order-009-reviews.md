# 2026-07-10 — ORDER 009 increment (3): /reviews — the fleet review-queue + findings links

> **Status:** `complete` — PR #75 (`claude/order-009-reviews`),
> squash-merge on `quality` green. (Flipped after the PR existed — a sibling
> took #74 in the gap, so predicting would have lied again.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 5 — 21:40Z nudge)

**What this session was about:** the 21:40Z send_later continuation of the
20:00Z continuous-mode wake. Inbox at HEAD has no order past 009; the
`planned` backlog top pick is **ORDER 009 increment (3)** ("closed or
honestly ledgered" allowed ledgering — now closing it for real): surface
`fleet-manager docs/review-queue.md` rows and link the launch-readiness /
economics findings docs. Implementer's-call placement (the order offers
/fleet, /queue, or a small docs panel): a small dedicated page **`/reviews`**
— the review queue is fleet quality debt, not an owner to-do, and a separate
page keeps /fleet's fetch fan-out unchanged.

## What was done

- **`app/reviews.py`** (new): fetches `docs/review-queue.md` over the shared
  TTL-cached raw path (anonymously readable — verified live); `parse_rows`
  reads the ledger's markdown table by HEADER NAME (the manifest parser's
  lesson) into `{repo#N → real PR deep-link, what-to-re-check, why-risky,
  drain-path/status}`; struck `~~…~~` rows classify as reviewed; a doc with
  no tables yields zero rows, never an invented one.
  `extract_findings_links` pulls every markdown link into the manager's
  `findings/`/`planning/` trees, resolves relative to `docs/`, dedups — the
  launch-readiness / economics / launch-record links come from the doc
  itself, so an upstream rename can't strand them. Degradation ladder as
  `/projects`: **empty** (404) / **not-configured** / **unavailable**;
  always 200.
- **`app/templates/reviews.html`** + routes (`/reviews`, `/reviews.json`
  with rendered HTML dropped) + nav link after `/projects`; open/reviewed
  roll-up badges; the FULL ledger rendered below the cards (nothing hidden
  by the parse).
- **Live-data verification pre-merge**: parsed the REAL upstream ledger —
  8 rows (all open: venture-lab#9, superbot-games#16/#5,
  trading-strategy#21/#36, superbot#1920, pokemon-mod-lab#8,
  gba-homebrew#12), all 3 findings links extracted and resolving 200.
- **Convergence check (coordinator step 4)**: all three services' `/version`
  == then-main HEAD `44a9fa6` (botsite, dashboard, control-plane — curled
  21:4xZ). No stale service; nothing to diagnose.
- **Docs:** D-0031 in the ledger; `docs/site.md` § 3e + Routes rows;
  backlog increment-(3) bullet `planned` → Built.
- The first `quality` run on this PR (head bde47572) concluded FAILURE **by
  design** — the born-red session gate holding the merge while this card was
  in-progress; this flip commit drives it green (coordinator FYI answered).

## Close-out (auto-drafted 2026-07-10 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `app/reviews.py` (new), `app/templates/reviews.html` (new),
  `app/main.py`, `app/templates/base.html`, `tests/test_reviews.py` (new),
  `docs/site.md`, `docs/decisions.md` (D-0031), `docs/ideas/backlog.md`,
  this card.
- git: branch `claude/order-009-reviews`, HEAD bde475720 at draft time (this
  flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **173 passed** (+8, `tests/test_reviews.py`); `python3 bootstrap.py check
  --strict` — **all checks passed** with this card complete.

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: D-0031 (`/reviews` as a dedicated small page; findings
  links extracted from the ledger rather than hardcoded — home:
  `docs/site.md` §§ 3e/Routes + the ledger).
- Next session should know: ORDER 009 is now FULLY closed (inc 1 `/projects`
  #72 live; inc 2 verified-covered; inc 3 this PR) — the wave's leftover
  captures live in `docs/ideas/backlog.md` (inbox-ORDER visibility;
  meta.md state-line convention). ALSO: the manager owes review-queue rows
  for websites#67 and websites#72 (>50 runtime lines each, the ledger's
  binding rule — this lane cannot write fleet-manager; flagged in the
  heartbeat notes).

⚑ Self-initiated: no — ORDER 009 increment (3) (P1; order claimed via
PR #71, increments 1–2 closed via PR #72, this closes the wave).

## 💡 Session idea

**Review-queue row auto-check for THIS repo's own PRs** — a small script (or
quality-job advisory step) that computes a merged PR's runtime/product
changed-line count against the ledger's binding 50-line rule and prints
"this PR needs a review-queue row" when it qualifies. Worth having because
the rule is BINDING fleet law ("appended by its own session before close")
but enforcement is memory — 116 merged PRs / zero rows was the documented
failure state, and this wake's own #67 (+300 runtime lines) qualified while
no session flagged it (row appending is a fleet-manager write this lane
can't do — but KNOWING a row is owed can be mechanical). Deduped against
`docs/ideas/backlog.md` + queue-state NEXT: nothing covers the 50-line rule.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 4 (same wake, PR #72) handled an order that landed mid-session
correctly — claim-first on main, empty-state-as-first-class-citizen, live
verification within minutes of merge; what it missed: ORDER 009's parent
review-queue LAW — #67 and #72 are both >50 runtime lines and neither got a
review-queue row (the ledger lives in fleet-manager, which this lane cannot
write — but the need was never even surfaced). Workflow improvement, applied
this slice: the heartbeat notes now ask the manager to append rows for
websites#67 and websites#72, and the 💡 idea proposes making the check
mechanical.
