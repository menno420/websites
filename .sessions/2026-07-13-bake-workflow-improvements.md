# 2026-07-13 — review-bake workflow: graveyard freshness + bake-PR quality trigger

> **Status:** `in-progress` — branch `claude/bake-workflow-improvements`; flips to `complete`
> + PR number as the deliberate LAST code step.

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

- (in progress — filled at the close-out flip)

⚑ Self-initiated: no — ORDER 022 item 2 / rule 6 (quality floor), standing
night-run mandate.

## 💡 Session idea

(filled at the close-out flip)

## ⟲ Previous-session review

(filled at the close-out flip)
