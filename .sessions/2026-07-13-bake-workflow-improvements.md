# 2026-07-13 — review-bake workflow: graveyard freshness + bake-PR quality trigger

> **Status:** `complete` — branch `claude/bake-workflow-improvements`, PR
> opened READY (non-draft) against main; merge is the auto-merge lane /
> owner's call — this worker opens, never merges.

- **📊 Model:** Fable · worker · ci-infra

**What this session was about:** ORDER 022 item 2 (keep executing the
existing plan to completion) + rule 6 (quality floor: merge=deploy). Two
improvements to the nightly review-bake Actions workflow: (a) the bake
refreshes `review/data/*.json` nightly but `botsite/data/graveyard.json`
ages silently — add `gen_graveyard.py` to the bake; (b) bake PRs created
with the Actions `GITHUB_TOKEN` do not trigger their own `pull_request`
workflows (verified on PR #259: 0 check runs on head; a session had to
close/reopen it), so the required `quality` check never reports and every
bake PR sits red until a hand intervenes.

## What was done

- `.github/workflows/review-bake.yml` — (a) the scheduled bake now also
  runs `python3 botsite/gen_graveyard.py` (verified this session: exact
  invocation from repo root, stdlib-only, anonymous raw fetch + ls-remote,
  wrote 566 runs, exit 0; fail-soft by design — on any fetch failure it
  keeps the committed file and exits 0, so it can never break the bake)
  and stages `botsite/data/graveyard.json` alongside the review/data
  files. The nothing-to-commit and PR-creation-refused exit-0 paths are
  preserved unchanged and cover the graveyard file (single staged-diff
  check gates all four files).
- (b) **Option chosen: dispatch-chained quality run** (Option 2). Option 1
  (close/reopen own PR) rejected: the reopen event is created with the
  same `GITHUB_TOKEN`, so the recursion guard still suppresses the
  `pull_request` run — same wall, no progress. Option 2 uses GitHub's
  documented exception ("events triggered by the GITHUB_TOKEN, with the
  exception of workflow_dispatch and repository_dispatch, will not create
  a new workflow run"): after opening the bake PR, review-bake runs
  `gh workflow run quality.yml --ref "$branch"` (best-effort — a refused
  dispatch never fails the job, the run summary says what to do by hand);
  `permissions:` gains exactly `actions: write`, nothing broader.
- `.github/workflows/quality.yml` — accepts `workflow_dispatch`; its three
  diff-range derivations (control fast lane, inbox append-only gate,
  every-card session gate) gain an event-agnostic branch: when no event
  range exists, `range="$(git merge-base origin/main HEAD)..HEAD"` — so a
  dispatch run grades the branch's real diff vs main exactly like a
  `pull_request` run would (simulated locally on this branch: correct
  files, `control_only=false`). The required-check name matches because
  required status checks match by check-run/job name on the head SHA
  (job `quality`), not by triggering event.
- **Honest limits — what could NOT be verified from this environment:**
  the dispatch exception is verified from GitHub's documentation plus
  local simulation of every changed shell path, NOT end-to-end — proving
  that a token-created dispatch run actually satisfies the required
  `quality` context on a bake PR needs the next real bake (cron ~05:23Z
  daily, or a manual `Run workflow` on review-bake). Until that run, the
  chain is designed-correct but unproven; the fallback if it misfires is
  the same one used for PR #259 (manual dispatch of quality.yml on the
  bake branch, or close/reopen by a non-author hand).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1192 passed; `python3 bootstrap.py check --strict` —
  green apart from this card's designed born-red hold (released at this
  flip) + the standing advisory owner-action-fields warning; both workflow
  files parse (`yaml.safe_load`; actionlint not installed in this
  environment).

⚑ Self-initiated: no — ORDER 022 item 2 / rule 6 (quality floor), standing
night-run mandate.

## 💡 Session idea

**Bake-chain self-verification step** — after dispatching quality.yml, the
bake job could poll (bounded, ~2 min) for a check run named `quality` on
the PR head SHA and write CONFIRMED/UNCONFIRMED into its run summary.
Worth having because the whole chain's weak point is silence — a dispatch
that is accepted but races the branch head would today look identical to
success until the PR sits checkless again. Deduped against
`docs/ideas/backlog.md`: no bake/dispatch/check-run bullet exists there.
Not captured in the backlog this session — this diff is deliberately
scoped to the two workflow files + card + claim; add the bullet as a
follow-up (same pattern as the webhook-analyzer card's queued capture).

## ⟲ Previous-session review

The webhook-analyzer session (.sessions/2026-07-13-webhook-analyzer.md,
PR #266) did well: verified grounding tier-by-tier and scoped its diff
tightly; what it missed is that its queued backlog-capture follow-up is
still unclaimed — the "scoped diff defers backlog capture" pattern needs
an eventual sweep session or the bullets never land.
