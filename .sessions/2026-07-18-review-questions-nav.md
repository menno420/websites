# 2026-07-18 — Surface /questions in the review NAV (R1)

> **Status:** `in-progress` — branch `claude/review-questions-nav`; the built
> `/questions` answer-debt ledger page (real reviewer questions asked → where
> the answer landed, with an honest empty state and an answer-debt nag) already
> renders but is reachable ONLY by typing the URL — it is absent from the review
> site NAV, so a reviewer browsing the header never discovers it. R1 adds a
> `/questions` entry to the review NAV (`review/app.py` `NAV` list + the shared
> `base.html` nav loop), mirroring the existing entries' style. NAV/template
> only — no product logic, no serialized JSON/env, no change to
> `data/questions.json` (its empty state is deliberate), no route behaviour
> change; the link is GET, so the CSRF/same-origin floor is untouched.

- **📊 Model:** [[fill: model · effort · task-class]]

**What this session is about:** the review service already ships a full
`/questions` page — the questions-asked → answered ledger, with a closed-without-
an-answer debt nag, an answer-latency median stat, and (by design) an honest
empty state over the deliberately-empty committed `data/questions.json`. The one
gap is discoverability: the page is a first-class surface but the header NAV
(Overview, Process, Growth, Fleet, Reviews, Q&A, Ask AI, Successes, Problems)
never lists it, so it is invisible to a reviewer who does not already know the
URL. R1's safe slice is purely navigation-visibility: add `/questions` to the
NAV so reviewers can reach it. The empty state and the ledger's read-only intake
convention are left exactly as they are.

⚑ Self-initiated: no — coordinator-dispatched backlog slice (R1).

## Close-out

**Evidence:**

- files touched this branch:
  - [[fill: review/app.py NAV entry + active state]]
  - [[fill: review/tests coverage]]
- test coverage: [[fill]]
- git: [[fill: branch base + commit chain]]
- verify: [[fill: four-suite count + both bootstrap checks]]

**Judgment:**

- Decisions made: [[fill]]
- Next session should know: [[fill]]

## 💡 Session idea

[[fill: one genuine session idea, deduped vs recent cards]]

## ⟲ Previous-session review

[[fill: one-line remark on .sessions/2026-07-18-arcade-games-crosslink.md]]
