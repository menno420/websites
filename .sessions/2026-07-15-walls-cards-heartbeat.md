# 2026-07-15 — walls ledger + card model-line grammar + heartbeat refresh

> **Status:** `complete` — PR #346, branch `claude/walls-cards-heartbeat-20260715`;
> three payload slices: `docs/CAPABILITIES.md` walls append, 2026-07-14 card
> `📊 Model:` grammar fixes, `control/status.md` field refresh.

- **📊 Model:** Claude Fable · medium · docs-only (walls ledger + card grammar + heartbeat refresh)

**What this session is about:** three small truing slices in one PR.
(1) `docs/CAPABILITIES.md` — append three walls verified 2026-07-15: the
auto-mode permission classifier denying dispatched control-plane writes
and the close/reopen re-fire ritual (with the measured unblock: the owner
switching the session to accept-edits); EnterWorktree being unavailable to
pinned subagents (manual `git worktree add` substitute); and
workflow-touching PRs being owner-merge-only via
`host-automerge-extras.yml`'s `do-not-automerge` auto-label.
(2) `.sessions/2026-07-14-*` cards — their `📊 Model:` lines emit
advisory `model-line-effort`/`model-line-class` warnings from
`bootstrap.py check`; fix only those lines to the taught grammar, keeping
the family-level model names untouched. (3) `control/status.md` — refresh
the changed fields (stamp, parked/needs-owner, next-2-tasks, main sha) in
the parser-compliant KNOWN_KEYS shape PR #344 established.

⚑ Self-initiated: no — dispatched under the owner's live work grant
(accept-edits session mode).

## Close-out

**Evidence:**

- files touched this branch: `.sessions/2026-07-15-walls-cards-heartbeat.md`
  + `control/claims/claude-walls-cards-heartbeat-20260715.md` (first
  commit; claim deleted at this flip), `docs/CAPABILITIES.md` (three
  2026-07-15 wall entries at the top of the append log; the Status badge
  and the capability-seed fence untouched), fourteen
  `.sessions/2026-07-14-*.md` cards (one `📊 Model:` line each — all the
  non-compliant lines, including the five sitting just outside the
  10-card lint window, so the fix survives window drift;
  `2026-07-14-kit-upgrade-v1.16.0.md` was already compliant),
  `control/status.md` (stamp / main sha / parked-open / baton fields
  only; `control/inbox.md` untouched).
- git: branch `claude/walls-cards-heartbeat-20260715`, based on `main` @
  `f79c3ec`; PR #346. Work done in an isolated `git worktree` (the
  EnterWorktree wall recorded this same PR).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1414 passed, 1 warning**;
  `python3 -m pytest tests/test_own_heartbeat.py -q` — **5 passed**
  (heartbeat shape parses); `python3 bootstrap.py check --strict` — the
  18 `model-line-effort`/`model-line-class` advisories present at branch
  base are **zero** after the fix (remaining advisories — seat-digest-stale
  and orientation-headroom — pre-exist on main `f79c3ec`, verified against
  a pristine baseline worktree); the only red during the session was the
  DESIGNED born-red hold on this card, released by this flip.

**Judgment:**

- Decisions made: (1) fixed all fourteen non-compliant 2026-07-14 model
  lines, not just the nine inside `MODEL_LINE_LINT_WINDOW = 10` — the
  window slides as new cards complete, so a window-only fix re-exposes
  the older cards; (2) mapped `worker` → `medium` effort and prefixed
  each task-class with its PL-004 class, keeping the original wording as
  parenthetical decoration (prefix-match is deliberate per the checker);
  (3) status refresh stayed field-level in the #344 KNOWN_KEYS shape.
- Next session should know: `docs/seat-digest.md` is stale against a
  fresh render (pre-existing advisory, now also missing this PR's three
  new walls) — run `python3 bootstrap.py seat-digest` in a follow-up
  slice; owner clicks pending: land #345 (remove `do-not-automerge` +
  hand-merge) and #343 (approve run 29397321395 or hand-merge).

## 💡 Session idea

**Window-0 model-line drift sweep** — `check_model_line` defaults to the
10 newest completed cards (`MODEL_LINE_LINT_WINDOW = 10`), so a
non-compliant card that ages out of the window is never re-flagged: this
session found five 2026-07-14 cards carrying the exact same `worker`
effort defect as the flagged nine, invisible to the gate purely because
newer cards had buried them. The function already supports `window=0`
("the drift-measurement lane" per its own docstring) — wire a scheduled
whole-history pass (healthcheck wake or the quality sweep) that runs the
lint at `window=0` and reports the count, so the PL-004 harvest stays
clean across ALL history instead of a sliding sample. Deduped against
`docs/ideas/backlog.md`: the "Kit-gate advisory for exact-ID model lines"
bullet covers adding the per-PR advisory (which now exists as this lint),
nothing covers whole-history window coverage.

## ⟲ Previous-session review

`.sessions/2026-07-15-quality-main-sweep.md` was this card's format
reference and its close-out is exemplary — exact run ids, the three-way
idempotence rationale, and an honest "only provable live" caveat on the
dispatch path. Two observations: (1) its own baton was immediately
consumable (this session's status refresh cites its PR #345 park state
verbatim), confirming the baton pattern twice in a row; (2) it shipped a
`.github/workflows/**` diff on an otherwise auto-landable PR, which is
exactly what parked it behind `do-not-automerge` — the wall this session
recorded in `docs/CAPABILITIES.md` suggests the practical rule its card
did not draw: split workflow files into their own PR so the rest of a
slice still auto-lands.
