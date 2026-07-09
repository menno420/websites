# 2026-07-09 — Wire the durable GitHub PAT into the control-plane service

> **Status:** `in-progress` — setting the token on Railway, verifying the board goes live, updating docs.

**What this session is about:** Close the one outstanding owner TODO from the
Railway deploy session — set the durable owner GitHub PAT as the
`control-plane` service's API token so the board's auth-gated cells (actions
secrets, auto-merge, CODEOWNERS enforced) render live instead of `unknown`.
Then update `docs/deployment.md`, `docs/current-state.md`, and the decision
ledger to reflect that the token is now set and the board is fully live.

## What is being done

- Upsert the token as a Railway service variable on `control-plane` in the
  `superbot-websites` project (public GraphQL API, `RAILWAY_API_KEY` only;
  ambient production-bot IDs never passed; no destructive mutation).
- Confirm the variable change triggers a redeploy to SUCCESS.
- Verify live: `/healthz` 200, and the three previously-degraded board cells
  now render real GitHub data.
- Docs: rewrite the `docs/deployment.md` owner-TODO section (token now set),
  close the gap in `docs/current-state.md`, append a decision-ledger entry.
