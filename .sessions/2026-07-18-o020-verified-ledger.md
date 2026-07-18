# 2026-07-18 — O-020 owner writeback VERIFIED LIVE: ledger truth + Railway capability

> **Status:** `in-progress` — branch `claude/o020-verified-ledger`; a
> docs/ledger-only truth PR recording that ORDER 020 owner writeback is now
> **LIVE and verified end-to-end** on the deployed control-plane (a live test
> note → auto-PR #399 → merged to `main` as `b12dcd9`), that **ASK-0007 is
> satisfied** (the deployed control-plane `GITHUB_TOKEN` already carries BOTH
> `contents:write` AND `pull-requests:write` — no owner paste or overwrite was
> needed), and that the **Railway account API is available to the seat**
> (`RAILWAY_API_KEY` against `backboard.railway.app/graphql/v2`). No payload
> change — docs/control only.

- **📊 Model:** [[fill: model family · effort · PL-004 task-class]]

**What this session is about:** the O-020 writeback engine (built + routed
through a branch+auto-PR last session, PR #398) has now been **exercised live**
against the deployed control-plane. A real `/owner/queue` note submission
committed to branch `claude/owner-writeback-1` (`0be58459`), opened auto-PR
**#399**, went quality-green, and auto-merged to `main` as **`b12dcd9`** — the
full submit→branch→PR→auto-merge chain proven with a real commit SHA, not
mocks. Two ledger facts follow: ASK-0007 needed no owner action (the live token
already holds both scopes), so the last blocking owner ask on O-020 is
discharged; and the seat can now reach the Railway account API (read/enumerate
projects/services/environments + read/set variables via `variableUpsert`),
which is how `SITE_PASSWORD` was read for the live-verify. This PR records those
truths in the ledger and tidies the one verification artifact left in
`control/owner-notes.md`.

⚑ Self-initiated: no — coordinator-dispatched (O-020 verified-live ledger + the
Railway-API capability finding).

## Close-out

**Evidence:**

- **live end-to-end verify (recorded, not re-run here):** a live `/owner/queue`
  note POST on the deployed control-plane committed to branch
  `claude/owner-writeback-1` (`0be58459`) → auto-PR **#399** → quality green →
  auto-merged to `main` as **`b12dcd9`**. The deployed control-plane
  `GITHUB_TOKEN` already carries **`contents:write` + `pull-requests:write`**
  (the runtime opens the PR itself); no owner PAT paste/overwrite was needed.
- **ledger edits (docs/control only, no payload change):**
  - `docs/owner/OWNER-ACTIONS.md` — **ASK-0007 marked SATISFIED / verified-live**
    and moved to the Decided section as **row O** (matching the file's
    "move to Decided, keep the ask text verbatim below" convention); the
    2026-07-18 status-clarification note was superseded by the satisfied entry.
    ASK-0002 left untouched (stays open with its reuse recon note).
  - `docs/CAPABILITIES.md` — appended a dated **capability** finding: the
    Railway account API (`RAILWAY_API_KEY`) is available to the seat for
    enumerate + read/set variables (values treated as secrets, never printed).
  - `control/owner-notes.md` — **removed** the O-020 live-verify test note
    (a verification artifact; the verify is now recorded in the ledger/cards),
    leaving the file pristine for real owner input.
  - `docs/current-state.md` — added a short current-truth line that O-020 owner
    writeback is LIVE (docs-gate respected: Status badge stays in the first 12
    lines, no new links).
- **ORDER 020 status:** now verified-complete — added to `control/status.md`
  `done=` (020) and reflected in the heartbeat NOTE.
- **files touched:** `docs/owner/OWNER-ACTIONS.md`, `docs/CAPABILITIES.md`,
  `control/owner-notes.md`, `docs/current-state.md`, `control/status.md`, and
  this card.
- **verify:** [[fill: four-suite pytest result + bootstrap strict + strict
  --require-session-log result, with exit codes]]

**Judgment:**

- Decisions made: [[fill: decisions taken this session, or none]]
- Next session should know: [[fill: pointer for the next session]]

## 💡 Session idea

[[fill: one concrete session idea]]

## ⟲ Previous-session review

[[fill: one-line review of .sessions/2026-07-18-writeback-branch-pr.md]]
