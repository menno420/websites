# 2026-07-18 — Declare the two env vars B6's drift panel surfaced (→ in-sync)

> **Status:** `in-progress` — branch `claude/declare-env-vars`, PR **[[fill: PR#]]**.
> The clean close-the-loop follow-up B6 named: declare the two env vars that are
> READ by runtime code but ABSENT from the committed manifest, so the gated
> `/owner/environments` code-vs-declared drift panel reads **in-sync**. Owner-
> nodded, decide-and-flag (a contained, reversible config correction).

- **📊 Model:** [[fill: model line]]

**What this session is about:** B6 (PR #401, merged `a63546a`) added the
code-referenced-vs-declared env-name drift view to `/owner/environments` and its
first real finds were two genuine manifest omissions: control-plane
`WRITEBACK_BRANCH_PREFIX` (read in `app/writeback.py` — the owner-writeback
branch-prefix knob, O-020) and dashboard `ARCADE_JSON_URL` (read in
`dashboard/data_source.py` — B1's arcade-counts feed source). Both are read by
runtime code with a code default but never declared in the manifest, so the
drift panel flagged them **referenced-but-undeclared**. This session declares
BOTH — names + one-line purpose, optional-with-default (no value) — so the panel
reads in-sync and the config debt is closed.

⚑ Self-initiated: no — coordinator-dispatched (owner-nodded follow-up to B6).

## Close-out

**Evidence:**

- **the change — two `_var(...)` rows added to `app/railway.py` `SERVICES`:**
  `WRITEBACK_BRANCH_PREFIX` under the control-plane service and `ARCADE_JSON_URL`
  under the dashboard service, each names+purpose only, the has-default semantics
  carried in the purpose text exactly as the ~15 existing optional-with-default
  vars already are (the direct sibling `WRITEBACK_BRANCH`, "default main", was
  already declared this way). No value anywhere.
- **the second committed inventory kept in sync — `app/data/environments.json`:**
  the same two names added to the `superbot-websites` group's control-plane and
  dashboard surfaces, because `tests/test_inventory_consistency.py` pins
  `railway.SERVICES` and the envhub registry to agree per service in BOTH
  directions (declaring in only one would trip that pin). Names only — the
  registry's value-guard forbids value-like fields.
- **why declaring is correct, not a new false-positive (the STOP-gate cleared):**
  the manifest has no dedicated "optional" field, but the established convention
  encodes has-default in the purpose string and already declares ~15 optional
  control-plane vars (`WRITEBACK_BRANCH`, `CACHE_TTL_SECONDS`, `OWNER_ASSIST_*`,
  …). `envdrift` (committed-vs-live) treats every declared optional var
  identically, so adding these two creates the SAME kind of entry the sibling
  `WRITEBACK_BRANCH` already has — not a new drift category. No structural
  blocker; declaring is the clean close-the-loop.
- **drift now reads in-sync:** [[fill: confirm compute_drift no longer lists them]]
- **B6 test updated:** [[fill: which test + how]]
- **files:** `app/railway.py`, `app/data/environments.json`,
  `tests/test_code_env_drift.py`, `control/status.md`, and this card.
- **verify:** [[fill: four-suite count + strict + require-session-log]]

**Judgment:**

- Decisions made: [[fill: decisions]]
- Next session should know: [[fill: baton]]

## 💡 Session idea

[[fill: one genuine idea]]

## ⟲ Previous-session review

[[fill: remark on env-config-drift.md]]
