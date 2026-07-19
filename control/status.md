# websites · status

updated: 2026-07-19T06:53:02Z
phase: FAILSAFE WAKE — heartbeat truing. No live coordinator has fired since 2026-07-18T21:52:34Z (~9h gap after a night landing PRs every 10-20 min); this wake found the pacemaker dead, verified the NEXT-2-TASKS baton is fully shipped at HEAD, and is truing the stale heartbeat since it cannot open a PR to land it normally (see blockers).
health: green — re-ran the full tree at HEAD a5fdad4: `pytest review/ dashboard/ app/ botsite/` = 998 passed, `pytest tests/` = 981 passed (1979 total, up from the last-recorded 1947); `python3 bootstrap.py check --strict` = all checks passed (only non-exit-affecting advisories: seat-digest render drift, orientation-headroom at 91 words, two session-card model-line format nits on `.sessions/2026-07-18-release-drift-banner.md`).
last-shipped: a5fdad4 — "botsite: durable /submit intake via DATABASE_URL (ORDER 034)" (PR #425), 2026-07-18T21:52:34Z. No lane activity since.
blockers: this session's GitHub API access (`api.github.com`) returns "GitHub access is not enabled for this session. An org admin must connect the Claude GitHub App for this organization." — `add_repo`/clone/push work via the session's git proxy, but PR creation does not, so this heartbeat truing can only be **pushed unmerged**, not landed normally. Same-shaped wall as the coordinator's own `send_later`/trigger-arming denial below; likely one platform rail, not two.
orders: acked=001-036 done=001-020,022-033,035-036 (021 + 034 open, owner-gated: 034 code-shipped via PR #425, awaiting owner DATABASE_URL paste — ASK-0004; 035 login half built and green, its remaining armed-write half owner-gated on ASK-0002/ASK-0003; 036 unstuck via PR #433, confirmed merged at git log).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` — this wake fired on it. send_later pacemaker chain: confirmed DEAD (last coordinator heartbeat self-reported "trigger/send_later arming is classifier-denied"); this wake attempted to re-arm and hit the PR-API wall above before reaching that step — re-arm not yet retried this wake, see notes.
landing: pushed-unmerged claude/heartbeat-truing-20260719 — this heartbeat-truing commit only (control/status.md, control-only diff); 0 other open coordinator PRs found (main HEAD clean, no dangling branches seen from this session's vantage).
deployed: origin/main at a5fdad4 (baad569 was the previously-recorded deploy sha; four Railway services — control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91 — not re-verified live this wake, no `/version` probe run; treat `deployed:` as last-known-good, not re-confirmed).
claims: control/claims/ empty (only README.md) — no stale or orphaned claims found.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below, unchanged this wake) — PLUS a new one: the session-level GitHub-App/API wall above needs an org admin to connect the Claude GitHub App (or an attended session to open this branch's PR by hand) before any lane can land normal PRs again; until then every wake can at best push branches, never merge them.
notes: NEXT-2-TASKS baton (below) is fully VERIFIED SHIPPED at HEAD — no code changes made this wake, only this heartbeat. This session is a failsafe-wake recovery attempt, not the live coordinator; a future PR-capable session should open/merge `claude/heartbeat-truing-20260719` verbatim (do not re-author its content) per control/README.md's "Landing other sessions' control-only work" rule, then continue the backlog (genuinely dry beyond owner-gated items — ORDER 032's PLANNING MODE fallback applies if no owner-gated item unblocks first).

## NEXT-2-TASKS baton — BOTH VERIFIED SHIPPED 2026-07-19, no code change needed
1. review `/questions` empty-state polish — DONE. `review/templates/questions.html:59` renders "No external reviewer questions on record yet." when the ledger is empty; covered by `review/tests/test_questionnaire.py::test_questions_ledger_honest_empty_state` + an assertion in `test_review_filters.py`.
2. drift-banner parity sweep — DONE. Both remaining surfaces already carry the release-drift indicator baked from review's committed mirror: `app/templates/board.html` (badge, `release_drift_count`) and `dashboard/templates/status.html` (banner + per-entry rows, `dashboard/tests/test_release_drift.py`). Review itself originated the banner (ORDER 033). All three services now have parity; botsite intentionally has no console-style drift surface (public site, not an operator dashboard).

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 12 open
ASK-0001 DECIDED (ORDER 035); ASK-0010 + ASK-0011 satisfied on claude/lumen-drift-live (release published + Pages deployed, both verified live — Decided rows P/Q); ASK-0007 satisfied a prior session. ASK-0002 is the opening step for the shipped login flow (redirect URI + env on the existing SuperBot app). ASK-0004 is code-shipped (PR #425) — one DATABASE_URL paste from live.
- ASK-0002 — add a redirect URI to the existing SuperBot Discord app + copy client id/secret/owner-id/session-secret onto the control-plane Railway env (REUSE, not a fresh app — the ASK-0001 decision). Unblocks the shipped owner login flow.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed this session).
- ASK-0004 — create the botsite submissions PostgreSQL + set DATABASE_URL on botsite. CODE SHIPPED (PR #425); goes live the moment the variable lands (railway.app project 70198ece → New → Database → PostgreSQL; botsite → Variables → DATABASE_URL = ${{Postgres.DATABASE_URL}}). Provisioning attempted via the account API — classifier-walled (docs/CAPABILITIES.md 2026-07-18); owner UI action.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret (only the BAKE_PAT Actions-secret half remains open).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

kit: v1.17.0
