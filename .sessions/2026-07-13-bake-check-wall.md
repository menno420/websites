# 2026-07-13 — bake required-check wall: document + route the PAT ask

> **Status:** complete — branch `claude/bake-check-wall`, PR opened READY
> (non-draft) against main; merge is the auto-merge lane / owner's call —
> this worker opens, never merges.

- **📊 Model:** Fable · worker · ci-infra docs

**What this session was about:** PR #269's dispatch-chained quality run was
designed-correct but unproven end-to-end. The first real proof run happened
this session-family: a manual review-bake dispatch (run 29242851190,
conclusion=success) produced bake PR #270 (head `48cef208`), and the chained
quality dispatch (run 29242891214) put a GREEN check run named `quality` on
that head — **but the main-branch ruleset does not count it**: merge attempts
return verbatim `405 Repository rule violations found` / `Required status
check "quality" is expected.`, `mergeable_state` stays `blocked`, and armed
auto-merge never fires. This session documents that wall where agents look
(docs/CAPABILITIES.md), corrects the review-bake.yml comment header to
measured reality, and routes the durable fix (a fine-grained PAT, folded into
the existing ORDER 020 PAT ask) as a paste-ready ⚑ OWNER-ACTION row.

## What was done

- `docs/CAPABILITIES.md` — appended a 2026-07-13 wall entry (top of the
  append log, newest-first) with the full measured chain: (i)
  GITHUB_TOKEN-created PRs get no `pull_request`-event checks (PR #259
  precedent, 0 check runs until a session close/reopened it); (ii) the #269
  dispatch chain puts a green `quality` check run on the bake PR head
  (run 29242891214, `event: workflow_dispatch`, head `48cef208`, associated
  with PR #270) but the ruleset refuses it — 405 verbatim above; (iii)
  interim workaround: a session close/reopens the bake PR → real
  `pull_request` quality run → ruleset satisfied (#270 parked awaiting
  this); (iv) durable fix routed to the OWNER-ACTIONS PAT row.
- `docs/owner/OWNER-ACTIONS.md` — new ⚑ OWNER-ACTION (six-field, paste-
  ready, RISK ↩️ reversible) extending the ORDER 020 fine-grained PAT so ONE
  token carries Contents:write (ORDER 020) + Pull requests:write (bake PR
  creation as a real actor); stored additionally as Actions secret
  `BAKE_PAT`; review-bake's `GH_TOKEN` then switches to
  `secrets.BAKE_PAT || secrets.GITHUB_TOKEN` (explicit fallback keeps
  revocation safe). VERIFY = next scheduled bake's PR shows a
  `pull_request`-event quality run and auto-merges without intervention.
- `.github/workflows/review-bake.yml` — comment header's "Required-check
  chain" section corrected to measured reality (green dispatch run ≠
  required context; interim = session close/reopen or review-merge; durable
  = the PAT row). NO functional YAML change — the dispatch chain stays
  (visible green signal, zero cost); file YAML-parses.
- **Landing #270 from this session-family: permission-denied** — the merge
  attempt was refused by the platform permission layer, so PR #270 stays
  PARKED: open, auto-merge armed, waiting for a sibling session (close/
  reopen) or the owner. Recorded here so the next session doesn't re-derive
  it. Follow-up (not this diff): the inline comment at review-bake.yml's
  `gh workflow run` step still says the dispatch "satisfies the required
  `quality` context" — scoped out (header-only edit was the assignment).

## Verify

- `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — 1206 passed, 1 warning.
- `python3 bootstrap.py check --strict` — green after this card's flip
  (born-red hold released at this commit; claim file deleted same commit).
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/review-bake.yml'))"`
  — parses.

## 💡 Session idea

**Ruleset-source assertion in the bake chain** — the whole #269→#270 arc
cost a day because "a check run named `quality` is green on the head SHA"
and "the required context is satisfied" turned out to be different facts.
The bake job (or the quality dispatch run) could, after going green, read
the PR's `mergeable_state` via `gh pr view --json mergeStateStatus` and
write SATISFIES-RULESET / GREEN-BUT-NOT-COUNTED into the run summary — the
prior session's "bake-chain self-verification" idea, sharpened by this
measurement: polling for the check run is not enough, poll the merge state.
Deduped against `docs/ideas/backlog.md` mentally, not landed there — this
diff is deliberately docs-scoped; add the bullet as a follow-up.

## ⟲ Previous-session review

The bake-workflow-improvements session (.sessions/2026-07-13-bake-workflow-
improvements.md, PR #269) did well: it flagged its own limit honestly
("designed-correct but unproven" + the exact fallback). What it missed:
"required status checks match by check-run/job name on the head SHA, not by
triggering event" was stated as fact from documentation reasoning — the
measurement (PR #270) falsified it for this repo's ruleset. Lesson: a
claim about a merge gate is only proven by a merge.

⚑ Self-initiated: no — coordinator-assigned slice (bake check wall docs +
PAT ask), follow-on from PR #269.
