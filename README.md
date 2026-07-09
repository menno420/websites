# websites

The permanent consolidated home for SuperBot's web properties.

A sibling rebuild track to the bot rebuild (`menno420/superbot-next`): same
`substrate-kit` foundation, same philosophy — keep the ideas and functionality of
what exists, rebuild the implementation.

## What's landing here

1. **Kernel/foundation**: adopted from [`menno420/substrate-kit`](https://github.com/menno420/substrate-kit).
2. **A control-plane oversight site** (SHIPPED — [`docs/site.md`](docs/site.md):
   routes, env vars, data model) — the first real deliverable: a live per-repo
   readiness board (rulesets, required checks, CODEOWNERS, secrets, auto-merge —
   configured *and* actually working, not just present) plus a cross-repo journal
   and decision-ledger browser, across `superbot`, `superbot-next`, and
   `substrate-kit`. This exists so repo/project state and build quality can be
   checked by looking, not by asking an agent to go find out.
3. **Reworked `dashboard`/`botsite`** — the two sites currently living in
   `menno420/superbot`, rebuilt here with the same ideas and functionality. A
   later, deliberately checkpointed phase, not this repo's first work.

Full plan: `menno420/superbot`'s
[`docs/planning/websites-project-kickoff-2026-07-09.md`](https://github.com/menno420/superbot/blob/main/docs/planning/websites-project-kickoff-2026-07-09.md).

Deployed on its own Railway project, separate from the production bot's project.
