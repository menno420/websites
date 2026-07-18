# websites · status

updated: 2026-07-18T20:32:28Z
phase: Discord OAuth owner login flow landed on the control-plane (PR #426, ORDER 035 / ASK-0001 DECIDED). Branch brought up to date with origin/main (HEAD c27d01c) and the session card flipped complete.
health: green — four service suites green (1947 passed); kit check --strict green once the session card flip releases this branch's designed born-red hold. Orphaned nav-reachability-guard claim cleared by the main merge (PR #421 merged).
last-shipped: Discord OAuth owner login flow on the control-plane — PR #426 (app/discord_auth.py + app/templates/owner_login.html + the require_owner gate wiring + tests/test_discord_auth.py; fail-closed when env-unset). Branch merged current main c27d01c (next-cycle planning #423 + doc hygiene), which deleted the orphaned control/claims/nav-reachability-guard.md.
blockers: none
orders: acked=001-033,035 done=001-020,022-033,035 (021 open, owner-gated — the ORDER 021 owner-environments hub; 035 login half built and green this session, its remaining armed-write half owner-gated on ASK-0002/ASK-0003; 034 unused).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" `45 */2 * * *` ARMED, still bound to the predecessor session (successor bridge by design); rebind rides the hub venue (this coordinator's trigger/send_later arming is classifier-denied 2026-07-18). send_later chain: none pending.
landing: pushed-unmerged claude/discord-oauth-owner-gate — Discord OAuth login PR #426; auto-merge (squash) armed, lands on green; 0 other open coordinator PRs.
deployed: origin/main at c27d01c · four Railway services live (control-plane-…-abb0 / botsite-…-cfd7 / dashboard-…-a91b / review-…-fc91, the superbot-websites project). Discord OAuth env still owner-unset → owner login stays fail-closed until ASK-0002.
claims: control/claims/discord-oauth-owner-gate.md is this branch's own in-flight claim (removed at the closing flip per claims README step 4); nav-reachability-guard orphan removed by the main merge.
needs-owner: the ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below). ASK-0001 is now DECIDED (ORDER 035); ASK-0002 narrowed to the SuperBot-app redirect URI + control-plane Railway env; ASK-0003 unblocked but owner-gated.

## NEXT-2-TASKS baton
1. B6 — dashboard `/env` config-drift flags (M · seat · no gate). Cross-check `/env` usage against a committed manifest, flag referenced-but-unset / set-but-unused vars. `dashboard/app.py` `env_page` currently renders only `data_source.env_usage(data)` with no manifest cross-check. Groomed detail: docs/plans/next-cycle-2026-07-18.md §1.
2. review `/questions` empty-state polish (S · verify-first). Confirm `/questions` renders a graceful "no questions answered yet" empty state (`questions.json` is intentionally `[]`); add one if missing. Consistent with the honest-empty design. Groomed detail: docs/plans/next-cycle-2026-07-18.md §4.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 14 open
ASK-0001 DECIDED this session (ORDER 035); ASK-0007 satisfied a prior session. ASK-0002 is the opening step for the shipped login flow (redirect URI + env on the existing SuperBot app). ASK-0010 (publish lumen-drift-v1.3) is the release the ORDER 033 drift banner surfaces.
- ASK-0002 — add a redirect URI to the existing SuperBot Discord app + copy client id/secret/owner-id/session-secret onto the control-plane Railway env (REUSE, not a fresh app — the ASK-0001 decision). Unblocks the shipped owner login flow.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (the armed bot-control write path, stubbed this session).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret (only the BAKE_PAT Actions-secret half remains open).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

kit: v1.17.0
