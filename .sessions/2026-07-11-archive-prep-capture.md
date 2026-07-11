# 2026-07-11 — Archive-prep capture: landing the chat-only load-bearing context before the project chat archives

> **Status:** `in-progress`

- **📊 Model:** claude-5 · worker · owner-directed archive-prep close-out (the
  project chat is being archived; this session makes the repo self-sufficient).

**What this session was about:** the project chat that directed this repo's
2026-07-10→11 run is being archived. Everything load-bearing that existed
ONLY in that chat — owner rulings, the wake-reliability ledger, coordination
lessons, the consolidated ⚑ owner-action list, cross-project debts, and the
resume pointer — was verified against what is already durable at HEAD
(verify-then-capture: cite, don't duplicate) and the genuinely chat-only
remainder landed durably.

## What was done

- `docs/retro/archive-ready-2026-07-11.md` (new) — the archive note:
  verified current state (PR count corrected 86+ vs the chat's "~50";
  #141 watchdog state; #145 merged 19:40Z; #151/#153 chain park absorbed
  mid-session), three chat-only owner rulings recorded (review site =
  standing continuous channel; dashboard armed-control deferred to
  Q-0004; owner personally merges workflow-file PRs), the mid-hold
  coordination failure (#143/#146) + drift-watchdog pattern, the
  owner-action roll-up, cross-project debts, resume pointer, and the
  closing confirmation that nothing load-bearing remains chat-only.
- `docs/owner/OWNER-ACTIONS.md` — four missing six-field asks appended
  (squash-merge PR #141; one manual review-bake run post-merge; botsite
  `DATABASE_URL`; control-plane `GITHUB_TOKEN` PAT), anchored below the
  historical-record paragraph, clear of #141's/#145's edit regions; no
  history deleted.
- `docs/ideas/merge-hold-at-head-2026-07-11.md` (new) + backlog bullet —
  the session 💡 (below).
- Claim ritual: claimed BEFORE build via fast-lane PR #149
  (`control/claims/claude-archive-prep-capture.md`); claim file deleted in
  this PR at session close per `control/claims/README.md`.

## Close-out (auto-drafted 2026-07-11 — edit, don't author)

<!-- substrate:auto-draft -->

**Evidence (auto-draft corrected — the draft diffed against a pre-merge
base and listed the sibling chain's files; real session diff below):**

- docs touched (4): `docs/retro/archive-ready-2026-07-11.md` (new),
  `docs/owner/OWNER-ACTIONS.md` (+4 six-field asks),
  `docs/ideas/merge-hold-at-head-2026-07-11.md` (new),
  `docs/ideas/backlog.md` (one bullet).
- control touched (1): `control/claims/claude-archive-prep-capture.md`
  (deleted at close; landed via fast-lane PR #149).
- sessions touched (1): this card.
- code/tests touched: none — docs-only capture by design.
- git: branch `claude/archive-prep-capture`, born-red card first commit
  `6072d01`; catch-up merges of origin/main absorbed #147/#148/#150/#145
  and #151/#153 mid-session; close-out commit flips the gate.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → see PR (green before push); `python3 bootstrap.py
  check --strict` → green after the flip (born-red HOLD before it, by
  design).

**Judgment (the half only the session knows — resolve every slot):**

- Decisions made: cite-don't-duplicate held throughout — PR #151's
  `continuous-mode-lessons-2026-07-11.md` landed mid-capture and absorbed
  the wake-ledger + build-and-hold material, so the archive note shrank
  §7 to a pointer + the one chat-only addendum (00:02Z fire OK) instead
  of a twin table. OWNER-ACTIONS additions anchored outside every
  in-flight PR's edit region (verified against #141's and #145's diffs
  before writing).
- Next session should know: read `docs/retro/archive-ready-2026-07-11.md`
  §6 first — if PR #141 is still open, take over the drift-watchdog;
  after the owner merges it, verify the review Railway deploy + first
  bake. The project chat is gone; the repo is the whole record now.

## 💡 Session idea

**Merge holds announced in a file at HEAD, not in session messages**
(`docs/ideas/merge-hold-at-head-2026-07-11.md` + backlog bullet, deduped
against the backlog first — nothing there covered hold coordination).
Worth having because the day's realized failure (#143/#146 merged
mid-hold by wakes that never saw the chat-coordinated hold) has a
mechanical fix: a `HOLD-<scope>.md` claim file at HEAD reaches every
future session via the mandatory session-start pull, by construction.

## ⟲ Previous-session review

Route-clock-freeze (#130): clean and complete — `clock.now()` as the
single wall-clock read plus the source guard genuinely closed the 08:45Z
failure class's route-level blind spot, and its card's "next session
should know" pointers were accurate when checked this session (the
backlog bullets it named were since built or remain routed). Workflow
improvement kept from watching this day's races: re-verify shared-file
anchor regions against every OPEN sibling PR's diff before editing, not
just against HEAD — it kept this session's OWNER-ACTIONS edits
conflict-free through four mid-session main advances.
