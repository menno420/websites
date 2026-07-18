# 2026-07-18 — Route owner writeback through a branch + auto-PR (O-020, Q2=b)

> **Status:** `in-progress` — branch `claude/writeback-branch-pr`; makes the
> gated owner writeback engine (ORDER 020, `app/writeback.py`) commit to a
> per-submit `claude/owner-writeback-<n>` branch and open an auto-merging PR
> into `main`, instead of a direct Contents-API PUT to `main`. The owner
> decided Q2=b: main-moves-by-PR-only is the repo's doctrine (GH013), and a
> direct PUT to `main` is blocked by the required-`quality` ruleset, so the
> writeback must land the same way every other change does — a reviewable,
> ruleset-safe PR that auto-merges on green. Born red by design: this card
> holds the merge until it flips `complete` at close-out.

- **📊 Model:** [[fill: model family · effort · task-class]]

**What this session is about:** O-020's writeback engine was built to PUT
straight to `main`. That path is structurally dead on this repo — `main` is
protected by a ruleset requiring the `quality` check, so a bare contents PUT
403/422s (branch protection). The fix routes each writeback through the same
branch+PR flow the fleet already uses: commit the append to a fresh
`claude/owner-writeback-<entry-id>` branch (the `claude/*` prefix the
auto-merge-enabler + host-automerge-extras arm), then open a READY PR into
`main`. For the runtime-generated PR to auto-land with **no human and no
session card**, its diff must be **`control/**`-only** (the CI control
fast-lane exempts a control-only diff from the session-card requirement and
short-circuits `quality` green): assist already appends to
`control/inbox.md`; note/complete are relocated from `docs/owner/owner-notes.md`
to `control/owner-notes.md`. The generated assist ORDER is brought into inbox
gate grammar (it was missing `done-when:`, one of the four required fields).
Honest-degrade is preserved end to end: no token / branch-create fail /
PR-open fail → the entry stays `queued` in SQLite with the exact error,
never a claimed commit/PR that did not land. Branch+PR is the DEFAULT; a
`WRITEBACK_DIRECT` env flag keeps the old direct-to-main path as an escape
hatch.

⚑ Self-initiated: no — coordinator-dispatched (O-020 activation, Q2=b).

## Close-out

**Evidence:** [[fill: files touched, git commits, verify lines + exit codes]]

**Judgment:** [[fill: decisions, what next session should know]]

## 💡 Session idea

[[fill: one idea]]

## ⟲ Previous-session review

[[fill: one-line review of the latest complete card]]
