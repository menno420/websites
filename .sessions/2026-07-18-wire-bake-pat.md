# 2026-07-18 — wire BAKE_PAT into review-bake landing step (ASK-0008)

> **Status:** `in-progress` — branch `claude/wire-bake-pat`; flips the
> landing step's `GH_TOKEN` in `.github/workflows/review-bake.yml` to prefer
> the owner-added `BAKE_PAT` secret (falling back to `GITHUB_TOKEN`) so the
> scheduled bake PR is authored by the PAT identity, gets a real
> `pull_request` quality run, and auto-merges on green. Born red; flips to
> `complete` as the deliberate LAST code step.

- **📊 Model:** [[fill: family-only model line at flip]]

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
  — [[fill: N passed at flip]]; `python3 bootstrap.py check --strict` —
  [[fill: verdict at flip]].

**Verify plan:** four-suite (`tests/ botsite/tests dashboard/tests
review/tests`) + `bootstrap.py check --strict` before flip; post-merge, a
manual `workflow_dispatch` of `review-bake.yml` proves the bake PR is now
authored by the PAT identity and gets a real `pull_request` quality run.

## 💡 Session idea

[[fill: genuine one-line idea + why worth having, deduped, at flip]]

## ⟲ Previous-session review

[[fill: one-line remark on release-drift-banner card at flip]]
