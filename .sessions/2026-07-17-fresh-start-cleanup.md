# 2026-07-17 — fresh-start cleanup: docs, owner-steps, next-tasks

> **Status:** `complete` — branch `claude/fresh-start-cleanup`; PR opened ready
> (non-draft) as the deliberate last step. Documentation only; no `app/` source,
> no workflow files, no secret values touched.

- **📊 Model:** Claude Opus 4.8 · medium · docs-only

**What this session was about:** an owner-authorized fresh-start cleanup ahead
of the EAP read-only cutoff (2026-07-21) and the Project recreation. The
autonomous apparatus is being wound down and the ~2026-07-15 permission
classifier froze autonomous merges. Rung: owner-directed order (fleet-wide
wind-down pass). Goal: leave `main` with an accurate current-state, a
classifier-safe landing doctrine, a curated next-task set, and names-only owner
console steps — so the recreated project boots clean.

## What was done

- `docs/current-state.md` — trued the header (EAP read-only 2026-07-21; frozen
  drafts #371–#380 cleared 2026-07-17; apparatus wind-down; recreate; main
  `ecbe2bf` #383; open PRs none). Rewrote the stale "In flight" section, pointed
  "Next steps" at the new curated docs, and **replaced the merge doctrine** in
  "Review rhythm" with the classifier-safe landing rule: open PRs READY and let
  the server-side `auto-merge-enabler` land on green; agents do NOT
  ready-flip/REST/MCP-merge (classifier-denied since 2026-07-15).
- `docs/NEXT-TASKS.md` (new) — curated the two overnight veto menus (24 arcade/
  dashboard on `main` + the 37 console/review proposals from the closed PR #375
  branch) into a ranked 5–8-step set grouped by the four services, plus an
  already-shipped prune list (#371/#381/#382/#383/#377) and a wind-down /
  retirement inventory.
- `docs/OWNER-STEPS.md` (new) — the three console-only steps at **names-only**
  level: set `SITE_PASSWORD` on control-plane (`/owner` gate; public site
  credential-free by design), provision the `BAKE_PAT` Actions secret for the
  nightly bake, and drop the two orphan password variables (dashboard
  set-but-unused, botsite unwired). No secret value written anywhere.
- `CONSTITUTION.md` — fixed the services rail to name `review/` as the 4th
  Railway service (was under-counted at three).
- `control/status.md` — overwritten with the accurate wind-down heartbeat
  (cleared open-PR set, no active claims, retirement note); `control/README.md`
  and `docs/ROUTINES.md` — added `⚠ RETIRING` banners pointing at the retirement
  inventory.
- Verified: docs-only change; no `app/`, workflow, or secret touched. Stale
  claims: none to clear (`control/claims/` holds only its README).

⚑ Self-initiated: no — owner-authorized fresh-start cleanup order, delivered
via the coordinator; documentation-only and reversible.

## 💡 Session idea

**Ship a `docs/OWNER-STEPS.md` names-only console-step doc as standard kit
furniture** — a per-repo curated list of console-only owner actions stated as
variable/secret NAMES with the value entered in the console, never in git.
Worth having because it cleanly separates "agent can do this" from "only the
owner can, in a console" and structurally prevents secret values from leaking
into committed docs. Deduped against `docs/ideas/backlog.md` + the menus:
not present. Captured here; promote to a backlog bullet on recreation.

## ⟲ Previous-session review

The 2026-07-16 records/hygiene session correctly landed the owner's overnight
order and refreshed the heartbeat, but it **parked eight green PRs as drafts**
waiting for an auto-merge patch the classifier had already made moot — the
right call would have been to recognize the frozen-draft signal as a doctrine
problem, not a workflow-patch problem. System improvement: the landing doctrine
now lives truthfully in `docs/current-state.md` so no future session re-parks
finished work behind a self-service merge that agents can no longer perform.
