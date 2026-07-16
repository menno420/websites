# 2026-07-16 — Healthcheck flags release drift (askverify probes vs registry blockers)

> **Status:** `complete` — PR #365, branch `claude/release-drift-flag`;
> fifth healthcheck pass `check_release_drift()` shipped: every registry
> blocker joined to its askverify probe by exact ask_id, drift FLAGGED.

- **📊 Model:** Claude Fable 5 · high · feature build (release-drift healthcheck pass)

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

- files touched this branch: `scripts/healthcheck.py` (+146 —
  `check_release_drift()`: blockers collected across the four registries
  via the SAME public loaders the pages render from (each already running
  `botsite/blockers.py`'s normalizer — disk reads of committed JSON only,
  zero new botsite outbound surface); exact ASK-NNNN join via
  `askverify.match` with no headline so the signature fallback never
  fires; probes reuse `askverify.annotate()` unchanged (claim-once,
  concurrent, fail-soft) deduped to ONE probe per ask_id per run (ASK-0012
  alone gates 14 cards); httpx client pair scoped via the `app/main.py`
  lifespan idiom; titled PASS/FAIL block folded into `RESULT:` + exit
  code); new `tests/test_healthcheck_release_drift.py` (+10 tests: real
  join + annotate machinery with monkeypatched probes —
  done-detected→FLAGGED+fail, still-open→PASS, probe-less→not
  machine-checkable no-fail, probe-raise→unknown no-fail, unmatched
  ask_id→ledger-drift FLAGGED, shared ask_id probed exactly once, id-less
  info row, collection-bug degrade, both `main()` exit-code
  integrations); `tests/test_healthcheck_arcade.py` +
  `tests/test_healthcheck_testing.py` (existing exit-code tests stub the
  new pass so `main()` stays network-free under pytest); this card +
  `control/claims/claude-release-drift-flag.md` (first commit; claim
  deleted at this flip); `control/status.md` (close-out heartbeat,
  wholesale, PR board re-verified live); `docs/ideas/backlog.md` (idea
  captured at this flip).
- git: branch `claude/release-drift-flag` from `main` @ `475d41c`; PR
  #365 (ready-for-review, auto-merge squash armed); commits `9854d25`
  (born-red card + claim), `cd318ad` (implementation), `3390421`
  (heartbeat), + this flip.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **1588 passed, 1 warning** (+10 vs main's 1578);
  `python3 bootstrap.py check --strict` — pass at this flip (the only red
  during the session was the DESIGNED born-red hold on this card,
  released here). Live smoke-run of the pass: 24 blockers across the 4
  registries, 7 distinct asks joined, 0 flagged — the two probe-carrying
  asks (ASK-0010/0011) degrade to honest `unknown` in the sandbox
  (proxy-restricted token) and get real verdicts in the deployed
  healthcheck environment.

**Judgment:**

- Decisions made: (1) blockers are read from the committed JSON through
  the public loaders, never fetched from the live botsite — the pass adds
  ZERO new botsite outbound surface, deliberately sidestepping the still
  UNANSWERED #355 SIM-REQUEST on botsite banner doctrine (the live probes
  run from the control-plane's askverify inside this script, which
  already does live fetches by design); (2) exact-ID-only matching — no
  headline is passed to `askverify.match`, so the signature fallback can
  never mis-join a blocker to the wrong ask; (3) only positive drift
  fails the pass: probe-less asks are honestly `not machine-checkable`
  and a probe error is an honest `unknown`, neither fails — never invent
  state; (4) unmatched ask_ids FLAG as ledger drift (a registry pointing
  at a row askverify doesn't know is real drift, not noise).
- Next session should know: the baton (control/status.md NEXT-2-TASKS) is
  the owner-console reverse join ("unblocks N cards" chip) and the
  owner-console release-drift chip reusing this pass's exact ask_id join;
  the #355 SIM-REQUEST (botsite banner doctrine A/B) remains UNANSWERED —
  the botsite-page banner stays unbuilt until the manager answers; the
  deployed 6-hourly healthcheck is now the alert surface for ASK-0010/0011
  clearing (sandbox runs show `unknown` for those two probes, deployed
  runs get real verdicts).

⚑ Self-initiated: no — coordinator-dispatched slice, promoted from PR
#362's close-out baton (`.sessions/2026-07-16-registries-askid.md`,
"Next session should know": the release-drift FLAG is one of the two
joins on the now-proven ask_id key).

## 💡 Session idea

**Shared `drift_report()` renderer — one structured join, three
surfaces.** The healthcheck's new drift pass and the owner console's
verification chips now share verdict logic (askverify probes on ask_id)
but not presentation — and baton task 2 (the console release-drift chip)
plus a future botsite banner (if the #355 SIM-REQUEST answer ever allows
one) would each re-implement the same blocker→probe join. A small helper
returning structured rows (registry, slug, ask_id, verdict, reason) would
let the healthcheck text block, the console chip, and the banner all
render from ONE join. Worth having because the join is subtle to get
right (claim-once probes, one-probe-per-ask dedupe, honest
unknown/not-checkable semantics) and three hand-copies of it is exactly
the drift class this repo keeps closing. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the arcade live-URL
drift probe, the prompts registry-drift chip, and the env-drift bullets
each cover a different drift surface; nothing covers a shared structured
renderer for the ask_id release-drift join (baton 2 names the chip, not
the shared renderer). Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-16-registries-askid.md` (PR #362, the newest previous
complete card) did the two things that made THIS slice cheap: it proved
the exact-ID join across all four registries with a cross-surface pin,
and its baton named this exact build ("zero new botsite network
surface") so the slice started with its design constraint already
settled; one miss: its card says askverify's open-ask pin moved 11 → 16
but doesn't flag that every new row is probe-less — the honest
`not machine-checkable` list this pass renders is doing the disclosure
its ledger rows left implicit.
