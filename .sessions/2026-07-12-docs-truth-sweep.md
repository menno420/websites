# 2026-07-12 — docs truth sweep: OWNER-ACTIONS Actions-ask strike + current-state refresh

> **Status:** `complete` — branch `claude/docs-truth-sweep`, PR #210.

- **📊 Model:** Claude Fable 5 · build worker · docs sweep

**What this session was about:** contained docs-truth-sweep (coordinator-assigned
slice, not an ORDER): (1) strike the satisfied "Actions: Allow GitHub Actions to
create and approve pull requests" ask in `docs/owner/OWNER-ACTIONS.md` with
verified evidence; (2) minimal factual refresh of `docs/current-state.md`. Every
claim verified against the GitHub API or `git log origin/main` before being
written — nothing copied from the briefing unverified.

## What was done

- **OWNER-ACTIONS strike (Decided row M):** review-bake run `29202721928`
  verified via the Actions API (`event: workflow_dispatch`, actor menno420,
  2026-07-12T17:49:33Z, conclusion success) → PR #194 verified created by
  github-actions[bot] and auto-merged (`merged_by: github-actions[bot]`,
  merged 2026-07-12T19:41:08Z), bake diff on main `a513ff4`
  (review/data snapshot/fleet/stats). Ask struck per the in-file J/K/L
  convention: STRUCK paragraph in place, Decided table row M, ask text kept
  verbatim under the Decided table. Two factual residuals recorded: first
  SCHEDULED (cron) success still unproven (next cron ~2026-07-13 morning),
  and the two orphan bake branches remain (verified still on the remote via
  `git ls-remote`; branch deletion is 403-walled for agents per
  `docs/CAPABILITIES.md`, so owner cleanup).
- **current-state refresh:** kit v1.14.0 → v1.15.0 (verified against the
  vendored `bootstrap.py` header + `substrate.config.json`; landed via
  #199), review Railway service flipped from queued owner-action to LIVE
  (review-production-f027, Decided row J), and the 2026-07-12 shipped wave
  added — #208 prompt-render fix, #194 first successful automated bake,
  #202/#203 environments hub, #199 kit upgrade, #183/#189 owner writeback —
  each merge commit verified on `origin/main` by `git log` before citing.
- **PR #209 collision:** #209 merged mid-session; `origin/main` merged into
  this branch (no rebase), conflict in the recently-shipped section resolved
  keeping both entries (ORDER 016 inventory first, shipped wave second).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 763 passed; `python3 bootstrap.py check --strict` —
  all checks passed (one standing advisory on control/status.md ask
  format, never exit-affecting); `--session-log` on this card showed the
  designed born-red HOLD before this flip.

⚑ Self-initiated: no — coordinator-assigned docs-truth-sweep slice.

## 💡 Session idea

**review-bake self-janitor for stale bake branches** — the review-bake
workflow now provably holds a token that can create branches and PRs; add a
final cleanup step that deletes its own merged/superseded `bake/review-data-*`
branches (and the two 2026-07-11/12 orphans) with that same Actions token.
Worth having because branch deletion is 403-walled for agent sessions
(`docs/CAPABILITIES.md`), so today every failed or merged bake leaves a branch
only the owner can remove — the workflow is the one actor that can keep its
own house clean. Deduped against `docs/ideas/backlog.md` (bake-time entries
there cover questions-sync and staleness banners, not branch cleanup).
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The ORDER 020 card (owner writeback) is a model close-out: its
never-fake-commit contract and exact-evidence style made today's strike
conventions easy to follow, and its six-field PAT ask needed no correction.
Missed nothing this session tripped over; its own honest-edges section
(ephemeral queue) already flags the follow-up its idea proposes.
