# 2026-07-09 — Build the control-plane site

> **Status:** `in-progress`

**What this session is about to do:** build the control-plane / oversight site —
the repo's core deliverable (kickoff sequence step 2): a **readiness board**
(per-repo: superbot, superbot-next, substrate-kit, websites — rulesets, required
checks configured AND currently green, CODEOWNERS, secrets, auto-merge, open-PR
health, fetched live from the GitHub REST API) and a **journal browser**
(.sessions/ logs, decision ledgers, question-routers, PR/commit history across
the repos, deep-linked into GitHub), gated behind a shared-secret auth wall,
packaged for Railway (Dockerfile, 0.0.0.0:$PORT). Branch
`claude/control-plane-site`, forward-only: fresh branch → PR → squash-merge.
