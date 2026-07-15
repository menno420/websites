# 2026-07-15 — Reboot truing: EAP extension ack (ORDER 031) + state truing

> **Status:** `complete` — PR #344, branch `claude/reboot-truing-20260715`;
> control/status.md rewritten wholesale (ACTIVE, EAP through 2026-07-21) and
> docs/current-state.md trued to main `3cac461`.

- **📊 Model:** Claude Fable · medium · docs-only (reboot truing: control/status.md + docs/current-state.md)

**What this session was about:** first rebooted wake after the 2026-07-14
dormancy record. Provenance: **ORDER 031**, `control/inbox.md` @ commit
`3cac461` (2026-07-15T03:36:57Z): "the v3.6 reboot prompt IS that go";
done-when = seat acknowledges on its first rebooted wake. The order extends
the EAP through **2026-07-21** and supersedes the 2026-07-14 dormancy
orders. This branch is that acknowledgement — it trues the two state
surfaces to the order's reality:

- `control/status.md` — wholesale rewrite: phase ACTIVE (EAP extended per
  ORDER 031, acked this wake), current health (main `3cac461`, suite 1414,
  strict check pass), orders ledger 001-031, routine (failsafe cron +
  pacemaker), parked/open PRs and rescue branches, open ⚑ asks, next-2-tasks
  baton, kit `v1.17.0`.
- `docs/current-state.md` — trued to main `3cac461`: suite count, open PRs
  #342/#343, EAP extension, kit version; durable claims kept (4 Railway
  services live, review-bake 405 GITHUB_TOKEN wall + BAKE_PAT ask, quality
  = required check).

⚑ Self-initiated: no — ORDER 031 (`control/inbox.md` @ `3cac461`), done-when
= seat acknowledges on its first rebooted wake.

## Close-out (auto-drafted 2026-07-15 — edited at the flip)

<!-- substrate:auto-draft -->

**Evidence (auto-collected — verified and corrected):**

- files touched this branch: `.sessions/2026-07-15-reboot-truing.md` +
  `control/claims/claude-reboot-truing-20260715.md` (first commit; the
  claim deleted at this flip), `control/status.md`, `docs/current-state.md`.
- git: branch `claude/reboot-truing-20260715`, based on `main` @ `3cac461`;
  PR #344. Session-boot churn rescued separately to
  `claude/rescue-20260715-c` @ `bce5b09` (lifeboat, no PR).
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1414 passed, 1 warning**; `python3 bootstrap.py
  check --strict` — green except the DESIGNED born-red hold on this card
  (released by this flip). One real catch during verify:
  `tests/test_own_heartbeat.py` went red on the first status draft (the
  routine line lacked the literal "armed"; `parked:`/`asks:` are not in
  `fleet.KNOWN_KEYS` and folded into the routine value) — fixed to the
  parser-compliant shape in commit `bddcf30`, suite then fully green.

**Judgment (the half only the session knows):**

- Decisions made: the status heartbeat keeps ONLY `fleet.KNOWN_KEYS` lines
  (parked/open PRs + the baton live under `notes:`, asks under
  `needs-owner:`); the routine line states "armed" explicitly so `/fleet`
  classifies it armed instead of prose.
- Next session should know: baton in `control/status.md` `notes:` — (1)
  investigate the missing push-event quality runs on main since `214ed0f`
  (ee47f8d, 6fafc1a, 68ad331, 3cac461 have none); (2) re-verify the 9 open
  ⚑ asks in `docs/owner/OWNER-ACTIONS.md` and resume ladder work.

## 💡 Session idea

**Auto-draft evidence collector: diff against merge-base with
`origin/main`** — the kit's close-out auto-draft appended to this card
initially listed "code touched (68) … sessions touched (195)" for a branch
that touches four files: on a detached/rescue boot it diffs against the
wrong base, so the auto-collected "evidence" inflates to most of the repo
and every card author must hand-delete it (noise in the PL-004 record and
a drift surface). Computing touched-files against `git merge-base HEAD
origin/main` would make the auto-evidence trustworthy on every boot shape.
Worth having because auto-evidence that must be manually corrected trains
sessions to ignore it. Deduped against `docs/ideas/backlog.md`: no
auto-draft/evidence-collector bullet exists (the two `merge-base` hits
there are CI gate lanes, unrelated).

## ⟲ Previous-session review

The ORDER 030 close-out card (`.sessions/2026-07-14-order-030-closeout.md`)
did one thing this session leaned on directly: its finalize pass re-trued
the walkthrough's #334/#330 one-liners from "being resolved" to merged
facts, so today's truing could cite the EAP close-out set without
re-deriving PR outcomes from `git log`. Workflow improvement it points at:
its `📊 Model:` line (`worker · order close-out (…)`) is one of the twelve
2026-07-14 cards now firing `model-line-effort`/`model-line-class`
advisories under the v1.17.0 taxonomy — a small follow-up sweep would clean
the PL-004 dataset (not done here; out of this slice's scope).
