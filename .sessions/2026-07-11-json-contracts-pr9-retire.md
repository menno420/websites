# 2026-07-11 — JSON shape pins for the four sibling endpoints + PR #9 salvage re-check retired

> **Status:** `complete` — PR #88 (`claude/json-contracts-and-pr9-retire`),
> squash-merge on `quality` green. (Flipped after the PR existed.)

- **📊 Model:** claude-fable-5 · worker · routine-fired build slice (continuous mode, slice 11 — 01:40Z nudge)

**What this session was about:** the 01:40Z send_later continuation.
Collision check: heartbeat at HEAD is this chain's own 01:24Z stamp, no open
PRs — clear. Inbox at HEAD has nothing past 009. Work-ladder rung 3, two
coordinator picks bundled: **(a)** the parametrized same-shape contract pins
for `/orders.json` / `/queue.json` / `/projects.json` / `/reviews.json`
(closing slice 9's own admitted generalization gap — the pattern file
exists), and **(b)** the **PR #9 `claude/rework-dashboard` salvage
re-check** (UNRESERVED), which the investigation resolved to a
retire-with-evidence: nothing to salvage. Pick (c) (healthcheck cron run-2
verdict) is not yet due (~02:17Z) — left for the next slice.

## What was done

- **(a) `tests/test_json_contracts.py`** (+4, suites 203 → 207): pinned key
  sets for all four sibling machine endpoints on a mocked happy path rich
  enough to reach every nested structure — `/orders.json` (top / summary /
  card / per-order, `body_html` absent), `/queue.json` (top / summary /
  item / source / fleet_manager, `body_html` absent), `/projects.json`
  (top / package / file, `meta_html` absent), `/reviews.json` (top / row /
  link, `body_html` absent). Named-key drift messages; same
  contract-change protocol as the /fleet.json pin (update the sets in the
  same PR that changes a payload).
- **(b) PR #9 salvage re-check — RETIRED with evidence** (backlog Retired
  entry): the remote branch shares NO merge base with main
  (parallel-checkout root, `git diff origin/main...` refuses); its only
  unique hardening commit `a0b459f` ("drop literal control-API env-var
  name from served HTML; extend denylist test to templates") is fully
  superseded on main by PR #10 — verified: main's
  `test_no_control_api_token_or_url_anywhere` scans `*.py` AND `*.html`
  with the same denylist, and a repo-wide grep finds ZERO forbidden
  literals in shipped dashboard files. The branch's other commits are the
  superseded parallel dashboard build PR #8 replaced. Branch prune left to
  someone with delete rights (branch deletion = the documented 403 wall);
  nothing on it is needed. The launch-readiness flag that asked this
  question is answered: no hardening was lost.
- No decision-ledger entry — test pins + an investigation verdict recorded
  at the idea's home (backlog Retired), no product-surface decision.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verify, then keep or correct):**

- files touched: `tests/test_json_contracts.py` (new),
  `docs/ideas/backlog.md`, this card — the auto-draft had no session-start
  anchor; list verified by hand against `git diff origin/main --stat`.
- git: branch `claude/json-contracts-and-pr9-retire`, HEAD 747586060 at
  draft time (this flip commit supersedes it).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests -q` —
  **207 passed**; `python3 bootstrap.py check --strict` — **all checks
  passed** with this card complete (kit v1.8.0).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: retire-not-salvage for the PR #9 branch (evidence above;
  home: the backlog Retired entry). No ledger entry — no product-surface
  decision.
- Next session should know: healthcheck cron run-2 verdict due ~02:17Z —
  check `actions_list` for workflow `healthcheck.yml` run 2 and record
  success/failure in the heartbeat (a silent no-show at 02:17Z means the
  SCHEDULE is dead even though run 1 passed via dispatch — treat as a bug).
  Remaining backlog picks: open-PR-awareness script, review-row auto-check,
  wait-deploy.py, ladder-rung telemetry, nav overflow guard, /ideas state
  filter (this slice's 💡).

⚑ Self-initiated: no — coordinator picks (a)+(b), both from the backlog
(rung 3).

## 💡 Session idea

**Retired/Built backlog entries as a `/ideas` state filter** — the websites
`/ideas` page renders every repo's ideas but treats the backlog as one
blob; now that `docs/ideas/backlog.md` has meaningful Built/Retired
sections with evidence, surfacing state counts (captured/planned/built/
retired per repo) would show at a glance how much of each repo's idea flow
actually ships — the conveyor health metric the kit's economy band wants.
Worth having because the fleet files ideas everywhere and nobody can see
conversion; the parse is one section-header scan over already-fetched
files. Deduped against `docs/ideas/backlog.md` + queue-state NEXT: nothing
covers idea-state surfacing. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 10 (same chain, PR #86) handled a mid-flight environment change
correctly — re-running the strict gate under the sibling's new kit v1.8.0
before flipping rather than trusting the pre-upgrade green; what it missed:
its born-red first commit carried a typo'd session URL in the commit
trailer (claude.a/ instead of claude.ai/) that squash-merge preserved in
the merged message body — trailers are write-once in practice, so proofread
them like code (this slice's trailers verified before each commit).
