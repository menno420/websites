# 2026-07-19 — finalize ASK-0008 ledger — BAKE_PAT landing path proven E2E

> **Status:** `in-progress` — branch `claude/ask-0008-ledger-close`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** [[fill: model · effort · task-class — resolve at flip]]

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
  — [[fill: N passed — resolve at flip]]; `python3 bootstrap.py check --strict`
  — [[fill: verdict — resolve at flip]].

## 💡 Session idea

[[fill: one genuine idea — resolve at flip]]

## ⟲ Previous-session review

[[fill: one line on the previous session — resolve at flip]]
