# 2026-07-13 — bake required-check wall: document + route the PAT ask

> **Status:** in-progress

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

- (to be filled at flip)

## Verify

- (to be filled at flip)

⚑ Self-initiated: no — coordinator-assigned slice (bake check wall docs +
PAT ask), follow-on from PR #269.
