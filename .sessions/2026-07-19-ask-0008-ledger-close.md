# 2026-07-19 — finalize ASK-0008 ledger — BAKE_PAT landing path proven E2E

> **Status:** `complete` — branch `claude/ask-0008-ledger-close`, PR #439;
> flipped from `in-progress` as the deliberate LAST code step.

- **📊 Model:** Claude Opus family · medium · docs-only

**What this session is about:** ASK-0008's remaining half — mint the `BAKE_PAT`
secret and flip review-bake's landing `GH_TOKEN` to it — was still open on the
ledger, with the interim note recording only that the workflow line was flipped
in-PR pending post-merge PAT-path proof. That proof has now landed end-to-end,
so this session finalizes the ASK-0008 row to **satisfied-with-evidence** and
records the evidence bundle. Work-ladder rung: order — fm ORDER 048 + live owner
action (owner added the `BAKE_PAT` secret, ASK-0008).

⚑ Self-initiated: no — fm ORDER 048 + live owner action (ASK-0008).

## What was done

- `docs/owner/OWNER-ACTIONS.md` — the ASK-0008 row finalized to
  **satisfied-with-evidence** (dated 2026-07-19); the existing interim note is
  kept and a final-resolution note appended citing the evidence below. No other
  ask touched; file not restructured.

### Evidence bundle (all verified this session)

- PR **#434** (wire `BAKE_PAT` into review-bake landing step) MERGED to main as
  commit `403a91de`; the landing step now reads
  `GH_TOKEN: ${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}`.
- Proof dispatch: review-bake.yml run **29678801173** (`workflow_dispatch` on
  main, actor menno420) → success.
- It created bake PR **#438** on branch `bake/review-data-20260719-075148`,
  **author login `menno420`** (the BAKE_PAT identity — NOT github-actions[bot]);
  the PR received a real `pull_request`-event `quality` check and had auto-merge
  armed (squash) — proving the PAT landing path works end-to-end. The old-token
  direct push still hit GH013 and correctly fell back to the PAT PR + auto-merge
  path (by design).
- Related cleanup: stale pre-fix bot bake PRs **#422** and **#437** closed
  (superseded, no-limbo rule).

- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1979 passed** (exit 0); `python3 bootstrap.py check --strict` — green
  except the DESIGNED born-red hold on this card (`[session-card-hold]` —
  designed hold, not a defect), released at this flip. Pre-existing advisories
  only otherwise (seat-digest-stale, orientation-headroom, a PL-004 model-line
  note on the unrelated 2026-07-18 release-drift card) — none introduced here.

## 💡 Session idea

**Auto-close superseded bake PRs when a newer bake lands.** The `review-bake`
run leaves stale earlier bake PRs open (this session hand-closed #422 and #437);
a small step that closes any open `bake/*` PR older than the one just created
would enforce the no-limbo rule mechanically. Worth having because superseded
bake PRs otherwise accumulate as false "open work" that every fleet scan must
re-triage by hand. Deduped against `docs/ideas/backlog.md` + the queue-state
NEXT list: not present; captured here on the card (no backlog write this
session to avoid a two-writer collision).

## ⟲ Previous-session review

`.sessions/2026-07-18-wire-bake-pat.md` did well to land the one-line workflow
flip with the load-bearing `|| secrets.GITHUB_TOKEN` fallback and to name the
exact post-merge PAT-path proof as the remaining gate — this session simply
executed that named check and closed the ledger row; nothing was missed.
