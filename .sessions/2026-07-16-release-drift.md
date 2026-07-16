# 2026-07-16 — Healthcheck flags release drift (askverify probes vs registry blockers)

> **Status:** `in-progress` — branch `claude/release-drift-flag`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · high effort · implementation (release-drift healthcheck pass)

**What this session is about:** the release-drift FLAG parked at PR #349
and promoted by PR #362's baton ("buildable with zero new botsite network
surface"). Today a cleared owner ask — e.g. the lumen-drift release tag
going live — is invisible to `scripts/healthcheck.py`: the four botsite
registries keep showing the blocker while the askverify probe already
detects the ask as done. This slice adds a FIFTH healthcheck pass,
`check_release_drift()`, that:

- collects every normalized blocker across the four botsite registries
  (arcade, catalog, products, puddle museum) via the public loaders +
  `botsite/blockers.py` — no hand-parsed JSON, no new botsite outbound
  surface (probes run from the control-plane's askverify inside this
  script, which already does live fetches by design);
- joins each blocker's `ask_id` to `app/askverify.py`'s REGISTRY by exact
  ID and reuses its probe machinery, deduped one probe per ask_id per run;
- FLAGs drift (probe says done-detected but the registry still gates the
  card) and ledger drift (ask_id matching no askverify entry) — the pass
  FAILS on either; still-open probes PASS; probe-less asks
  (ASK-0012..0016 class) are honestly listed `not machine-checkable`; a
  probe error is `unknown` — neither fails the pass (never invent state).

## Close-out

**Evidence:**

- files touched this branch: [[fill: files + load-bearing specifics]]
- git: [[fill: branch base, commits, PR number]]
- verify: [[fill: real pytest count + bootstrap check verdict]]

**Judgment:**

- Decisions made: [[fill: decisions taken this session, or none]]
- Next session should know: [[fill: the handoff pointer — where to pick up]]

⚑ Self-initiated: no — coordinator-dispatched slice, promoted from PR
#362's close-out baton (`.sessions/2026-07-16-registries-askid.md`,
"Next session should know": the release-drift FLAG is one of the two
joins on the now-proven ask_id key).

## 💡 Session idea

[[fill: one idea genuinely believed in, with its "worth having because",
deduped against docs/ideas/backlog.md]]

## ⟲ Previous-session review

[[fill: one line — what the last session did well and what it missed]]
