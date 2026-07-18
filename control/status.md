# websites · status

updated: 2026-07-18T13:30:00Z
phase: backlog build — X2 the pure test/guard coverage bundle: a TEST-ONLY PR that raises the safety floor by pinning three existing-but-untested behaviours so a regression fails the build instead of shipping silently. C9 — the open-PR truncation flag (`readiness.repo_readiness` `prs.capped`, the board / owner "(capped)" marker); C11 — the `app/github.py` TTL-cache poison guard (successes + stable 404/403/401 cached; transient 429/5xx/network never poison the cache); R7 — the tie between the `gen_questions` bake's closed-without-answer `ADVISORY:` log lines and the answer-debt nag rendered on `/questions` (`review/story.answer_debt`). R6 (the three review bake generators) already landed #391, so X2 covers the still-open three. Branch `claude/test-coverage-bundle`; a NEXT-TASKS slice of the standing overnight ORDER 032. No product code, serialized JSON/env, or workflow touched — tests only.
health: green — origin/main advanced: C14 self-cleaning owner queue (#386), the orphan-claim cleanup (#387), B1 arcade live/blocked counts on dashboard /status (#388), C1 honest counts on /work /history /console (#389), A4 arcade JSON schema CI guard (#390), R6 review bake-generator unit tests (#391), C15 durable ask ids on the owner-action queue (#392), A2 /arcade↔/games cross-link (#393), and R1 surface /questions in the review NAV (#394 landing) all landed. Last full four-suite run 1828 (2026-07-18, this session — 1807 + 21 new coverage tests: C9 ×4, C11 ×13, R7 ×4).
last-shipped: #394 — origin/main head ede6221.
orders: acked=001-032 done=001-019,023-031 — unchanged. X2 ships as a backlog slice of the standing overnight ORDER 032, not an order completion.
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min send_later pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
blockers: none
landing: pushed-unmerged claude/test-coverage-bundle — PR #395 READY (X2 test-only coverage bundle: C9 pagination-truncation, C11 cache-eviction, R7 advisory-debt parity); merges via server-side auto-merge-enabler on green (agents cannot self-merge, classifier since 2026-07-15). Open PRs: this one.
deployed: ede6221 · four Railway services live (control-plane/botsite/dashboard/review). X2 is test-only — three new test files (`tests/test_pr_truncation_cap.py`, `tests/test_github_cache_eviction.py`, `review/tests/test_questions_advisory_debt_parity.py`) + this session card + this heartbeat. No product code, env, workflow, or serialized JSON touched; every test ADDS coverage for behaviour that already exists.
claims: no active claims (no claim filed — no active contention; committed branch-claims orphan on squash-merge, so the branch-named claim would outlive its branch and red main post-merge — the #387 cleanup class).
notes: WIND-DOWN standing — the Claude Code Projects EAP goes READ-ONLY 2026-07-21; the autonomous apparatus is being retired and the Project recreated (inventory: docs/NEXT-TASKS.md → "Wind-down / retirement"). X2 is a contained, reversible test-only slice, independent of the retirement set.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — none resolved this session.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 16 open, none resolved this session
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## NEXT-2-TASKS baton
1. B6 — config-drift flags on the dashboard /env surface (NEEDS a design call: a names-only committed manifest vs the live env the dashboard cannot read).
2. The remaining NEXT-TASKS slices once the high-value ones are exhausted.
- Blocked-not-mine: O-020 / O-021 (gated on owner credentials — the ASK-0001..0009 provisioning set); R10 (workflow-touch / hub-venue — needs the owner-side hub decision).
- Standing owner-side: recreate the Project from `main` once the EAP successor is chosen + strip the retired routine/heartbeat/coordinator apparatus (this file included) — EAP goes read-only 2026-07-21.

kit: v1.17.0
