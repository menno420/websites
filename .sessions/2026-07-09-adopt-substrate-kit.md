# 2026-07-09 — Adopt substrate-kit

> **Status:** `in-progress`

**What this session is about to do:** adopt substrate-kit into this repo —
fresh-from-kit, never a copy of superbot — per the kickoff brief
(`menno420/superbot` `docs/planning/websites-project-kickoff-2026-07-09.md`,
sequence step 1), mirroring the procedure `menno420/superbot-next` used in its PR #1.

## Provenance

- Source: `menno420/substrate-kit` main @ `08a291f96599d5b7ec1b6a46a381d4e3f88839c0`
- `dist/bootstrap.py` blob `7d2b85c740b952aa8c52d013fdcfa182f395b509` (643694 bytes, stdlib-only)
- Command: `python3 bootstrap.py adopt` from repo root

## What was done

- Planted 17 artifacts: `CONSTITUTION.md`, the binding doc skeletons
  (`docs/architecture.md`, `ownership.md`, `runtime_contracts.md`,
  `collaboration-model.md`, `helper-policy.md`, `repo-navigation-map.md`,
  `ai-project-workflow.md`, `owner-profile.md`), the living ledgers
  (`docs/current-state.md`, `docs/decisions.md`, `docs/question-router.md`,
  `docs/ideas/README.md`), `docs/AGENT_ORIENTATION.md`, `.sessions/` +
  `.session-journal.md`, `project.index.json`.
- Staged 14 artifacts under `.substrate/` (claude/CLAUDE.md, 7 skills, 3 agents,
  hooks settings template + README, ci/quality.yml.example). No live `.claude/`
  tree written (adopt ran without `--include-claude`).
- Decision ledger: D-0001 (kit-seeded adoption entry) + D-0002 (provenance pin,
  via `bootstrap.py ledger`).
- Interview: confirmed `project_name = websites`; mode stays `guided` (kit
  default, same as superbot-next). Language/runtime slot deliberately left for
  the site-build phase — the stack choice belongs to the phase that writes code.
- Verification: `python3 bootstrap.py check --strict` green (exit 0; session-log
  absence was advisory at run time — this log satisfies it).

## Decisions made this session

- Mirror superbot-next's adoption exactly (same kit blob, same minimal-answer
  interview posture) rather than pre-answering slots the build phase owns.
- Branch `claude/adopt-substrate-kit`, forward-only: fresh branch → PR →
  squash-merge; never force-push / branch-delete / amend-after-push.

## 💡 Session idea

The readiness board (this repo's first real deliverable) should include a row
for `websites` itself from day one, even while its settings are all "not yet
configured" — a board that honestly shows its own repo as red is the cheapest
proof the board reports real state rather than curated state.

## ⟲ Previous-session review

Previous session in this repo was the intent-commit seed (`aec1cd5`, README
only). It did its one job well — the README states scope, sequence, and the
Railway separation crisply, so this session needed zero guessing. One
improvement it points at: the README links the kickoff doc on superbot `main`,
but that doc is still on an open superbot PR (#1876) — a link that 404s until
that PR merges. Workflow lesson: when seeding a repo that cites a doc in
another repo, cite the PR too, so the pointer works in the gap.
