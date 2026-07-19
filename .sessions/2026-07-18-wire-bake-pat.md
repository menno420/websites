# 2026-07-18 — wire BAKE_PAT into review-bake landing step (ASK-0008)

> **Status:** `complete` — branch `claude/wire-bake-pat`, PR #434; flipped the
> landing step's `GH_TOKEN` in `.github/workflows/review-bake.yml` to prefer
> the owner-added `BAKE_PAT` secret (falling back to `GITHUB_TOKEN`) so the
> scheduled bake PR is authored by the PAT identity, gets a real
> `pull_request` quality run, and auto-merges on green. Born red; flipped to
> `complete` as the deliberate LAST code step.

- **📊 Model:** Claude Opus family · medium · mechanical refactor

**What this session is about:** The scheduled `review-bake` workflow lands its
data-refresh PR with the Actions `GITHUB_TOKEN`. A PR created with that token
does not trigger its own `pull_request` workflows (GitHub's recursion guard),
so the required `quality` context never lands as a real check and the branch
ruleset blocks auto-merge — the symptom is blocked PR #422, which never merges
on its own. The durable fix prescribed in `docs/owner/OWNER-ACTIONS.md`
(ASK-0008) is to create the bake PR with a fine-grained owner PAT instead of
the Actions token. The owner has now added the `BAKE_PAT` repo Actions secret
(live owner action), so this session flips the landing step's `GH_TOKEN` to
`${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}` — a minimal one-line env
change. The `|| secrets.GITHUB_TOKEN` fallback is load-bearing: if the secret
is ever absent the workflow degrades to today's behavior rather than breaking.

Work-ladder rung: order — fm ORDER 048 + live owner action (owner added the
`BAKE_PAT` secret, ASK-0008).

⚑ Self-initiated: no — fm ORDER 048 + live owner action (ASK-0008).

## What was done

- `.github/workflows/review-bake.yml` — the landing step's
  (`Commit and land the refreshed data`) `GH_TOKEN` env flipped from
  `${{ secrets.GITHUB_TOKEN }}` to
  `${{ secrets.BAKE_PAT || secrets.GITHUB_TOKEN }}`. Exactly one line changed;
  the bake step's `GITHUB_TOKEN` (used only for `gen_stats.py` REST headroom)
  is deliberately left untouched.
- `docs/owner/OWNER-ACTIONS.md` — interim dated note on the ASK-0008 row
  recording the workflow line is now flipped in-PR, pending post-merge
  PAT-path proof.
- `control/claims/wire-bake-pat.md` — work claim for this branch (deleted in
  the flip commit so it merges away with the PR).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1969 passed** (exit 0); `python3 bootstrap.py check --strict` — green
  except the DESIGNED born-red hold on this card (confirmed as the single CI
  finding on PR #434, run 29661461089: `[session-card-hold]` — "designed hold,
  not a defect"), released at this flip.

**Verify plan:** four-suite (`tests/ botsite/tests dashboard/tests
review/tests`) + `bootstrap.py check --strict` before flip; post-merge, a
manual `workflow_dispatch` of `review-bake.yml` proves the bake PR is now
authored by the PAT identity and gets a real `pull_request` quality run.

## 💡 Session idea

**A `secrets.BAKE_PAT != ''` self-check line in the review-bake landing step.**
The workflow now silently falls back to `GITHUB_TOKEN` when `BAKE_PAT` is unset
— safe, but invisible: a reverted/expired secret would quietly resume the old
blocked-PR behavior with no signal. Worth having because a one-line
`echo "landing as: ${BAKE_PAT_PRESENT:-GITHUB_TOKEN fallback}"` (guarded so it
never prints the secret) into `$GITHUB_STEP_SUMMARY` turns a silent regression
into a visible run-summary line. Deduped against `docs/ideas/backlog.md` + the
NEXT list: not present. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-18-release-drift-banner.md` did well to keep the ORDER 033
diff product-only and explicitly defer the review-bake **workflow wiring** to
the hub venue (naming this exact follow-up) — a clean scope boundary; it did
trip the PL-004 model-line advisory (`high effort` / a non-taxonomy task-class),
a small format miss this card avoids by using the taught `<effort> · <class>`
form.
