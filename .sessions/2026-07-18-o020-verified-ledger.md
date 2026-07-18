# 2026-07-18 — O-020 owner writeback VERIFIED LIVE: ledger truth + Railway capability

> **Status:** `complete` — branch `claude/o020-verified-ledger`; a
> docs/ledger-only truth PR recording that ORDER 020 owner writeback is now
> **LIVE and verified end-to-end** on the deployed control-plane (a live test
> note → auto-PR #399 → merged to `main` as `b12dcd9`), that **ASK-0007 is
> satisfied** (the deployed control-plane `GITHUB_TOKEN` already carries BOTH
> `contents:write` AND `pull-requests:write` — no owner paste or overwrite was
> needed), and that the **Railway account API is available to the seat**
> (`RAILWAY_API_KEY` against `backboard.railway.app/graphql/v2`). No payload
> change — docs/control only.

- **📊 Model:** Claude Opus 4.8 · medium · docs-only — verified-live ledger truth + contract-pin

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
- **verify:** `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **1839 passed, 1 warning** (exit 0; the pre-existing
  Starlette/httpx TestClient deprecation is the only warning). Two askverify
  contract-pins first went red on the ledger edit (`test_real_ledger_has_the_
  sixteen_open_asks…` and `…matches_land_on_the_intended_probes`) — expected,
  since ASK-0007 moved out of the Open section — and were updated to 15 +
  order-020-pat dropped, then green. `python3 bootstrap.py check --strict` and
  `--require-session-log` → the only red is the DESIGNED born-red hold on THIS
  card, released at this flip (gating on exactly 1 card — mine; no other red).

**Judgment:**

- Decisions made: (1) **Move ASK-0007 to Decided (row O), don't just flip a
  status line** — the file's established convention for a satisfied ask is
  strike-in-place + a Decided table row + the six-field ask kept verbatim below
  (rows J/K/L/M set the precedent); I matched it rather than inventing a
  lighter edit. (2) **Restore `control/owner-notes.md` byte-identical to
  `NOTES_HEADER`** — my first pass left a human placeholder line, but the
  writeback engine deliberately seeds this file byte-for-byte equal to
  `NOTES_HEADER` (`app/writeback.py:90`) so the runtime create-on-404 and
  append paths converge; removing the test note back to the exact header keeps
  that invariant (verified `disk == NOTES_HEADER`, 556 bytes). (3) **Update the
  two askverify count-pins rather than route around them** — they legitimately
  pin the Open-section ask count, which genuinely dropped 16→15; the update IS
  the contract-pin discipline each ask-satisfaction requires. (4) **Left the
  two untracked substrate-kit auto-draft boot cards** (`2026-07-17-session.md`,
  `2026-07-18-session.md`, detached-HEAD "nothing committed yet") out of the
  tree so the born-red gate HOLDs only on my card — moved to scratchpad,
  reversible, never staged.
- Next session should know: O-020 is now fully discharged (built + branch+PR
  routed + verified LIVE end-to-end); the last owner ask on it (ASK-0007) is
  satisfied with no owner action, because the deployed control-plane
  `GITHUB_TOKEN` already carried both scopes. ASK-0008's PAT-scope half is
  therefore also already covered on the Railway token — only its `BAKE_PAT`
  Actions-secret half remains. New lever for future sessions: the Railway
  account API is reachable from the seat (`RAILWAY_API_KEY`, CAPABILITIES
  2026-07-18) for enumerate + read/set variables, so deployed env/config can be
  self-verified without owner console steps (values are secrets — never
  print/log). Next baton: B6 names-only config-drift check (Q1=a), then a
  remaining-backlog assessment.

## 💡 Session idea

**Auto-reconcile a done-detected owner ask straight into a Decided-row draft.**
`app/askverify.py` already POSITIVELY detects when an ask's condition has
resolved (the `DONE`/self-cleaning ladder) and the owner queue already
self-cleans it from the active list — but the *ledger* edit that this session
did by hand (strike ASK-0007 in Open, add Decided row O, keep the six fields
verbatim, drop the count-pin) is still fully manual and easy to forget, which
is exactly how a satisfied ask lingers as a false open row. A cheap durable
win: when `annotate()` flags an ask `done-detected` with a *machine* verdict
(not a guess), have the self-cleaning pass emit a ready-to-commit ledger-diff
draft (the strike note + a Decided-row stub + the verbatim block relocation),
surfaced on `/owner/queue` for one-click adoption. The detection already
exists; only the write-back-to-the-ledger half is missing — the same
"generator already knows, wire it to the writer" instinct the previous card's
idea raised for the ORDER-field list.

## ⟲ Previous-session review

`.sessions/2026-07-18-writeback-branch-pr.md` (O-020, Q2=b) built the writeback
engine's branch+auto-PR path and closed with the honest caveat that the LIVE
end-to-end verify was still pending the deploy + a token paste. This session is
the discharge of exactly that open thread: the live submit→branch→PR→merge
chain ran for real (PR #399 → `b12dcd9`), and the token paste turned out to be
a no-op because the deployed `GITHUB_TOKEN` already held both scopes — so the
previous card's "still pending" is now "verified done", recorded in the ledger
rather than left as tribal knowledge.
