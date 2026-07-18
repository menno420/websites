# websites · status

updated: 2026-07-18T13:25:00Z
phase: BUILD+LAND — one contained control-plane UX PR on the `/fleet` overview. Two owner-live problems: (1) the fleet-heartbeat summary count badges (`18 lanes`, `12 stale`, `9 outstanding orders`, `1 stranded landing`, `packages incomplete: N`) looked tappable but had no handler — the owner tapped 7 times expecting to see WHICH lanes; (2) at 480px the per-seat status cards clipped long monospace values (heartbeat prose, `done=` lines, trigger IDs, branch/tool names) behind a horizontal scrollbar with a hard-to-read grey label column. FIX: each count is now a server-rendered inline `<details>` drill-down to the exact lanes behind it (data derived in `app/fleet.py` `overview()` alongside the count — one source of truth); informational pills flattened to non-interactive `.tag`; the per-seat key/value table (`.kv`) wraps long values + bumps the label contrast. GET views only — the CSRF/same-origin floor is untouched.
health: green — origin/main advanced (session-ender #403 landed, main @ `7968685`). Four service suites pass (1871 with the new drill-down tests); both strict kit gates green apart from the by-design born-red hold on THIS PR's card, released at the closing flip. Playwright 480px check passed (a count badge expands to its lane list; values wrap with no horizontal scrollbar; label column legible).
last-shipped: `7968685` — B6 close-loop, declare two env vars → drift in-sync (PR #403) on origin/main.
blockers: none
orders: acked=001-032 done=001-019,020,023-031 — this PR (#404) is a coordinator-dispatched owner-live UX ask, not an order; 021/022 remain non-done (021 armed-panel owner-gated; 022 was a reconcile order).
routine: failsafe cron `trig_01FYyvu2EytWF5NSEzLU2qLD` "Websites failsafe wake" (cron `45 */2 * * *`) bound to the coordinator session; a ~15-min `send_later` pacemaker chain is kept alive coordinator-side. Old failsafe `trig_01VRT9F6jYNXym3nn18vVQQK` retiring (not re-armed). Tool wall: the capitalized alias `mcp__Claude_Code_Remote__list_triggers` is classifier-blocked; lowercase `mcp__claude-code-remote__list_triggers` works.
landing: pushed-unmerged claude/overview-mobile-ux — PR #404 READY (overview count-badge drill-downs + mobile legibility); merges via auto-merge-enabler on green.
deployed: origin/main head `7968685` · four Railway services live (control-plane/botsite/dashboard/review). PR #404 touches only control-plane view code (`app/fleet.py` summary, `app/templates/fleet.html`, `app/templates/base.html` CSS) + tests — no new route, no state-changing surface, no behavior change beyond the overview render. O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).
claims: no active claims (no claim filed — committed branch-claims orphan on squash-merge).
notes: the `/fleet.json` summary contract gained nine member-list keys (`stale_lanes`, `live_lanes`, `total_lanes`, `stranded_lanes`, `outstanding_order_lanes`, `broken_lanes`, `errored_lanes`, `no_file_lanes`, `silent_routine_lanes`); the pin in `tests/test_fleet_json_contract.py` was updated in the same PR per contract-pin discipline. Counts are now derived FROM their member lists so a badge and its drill-down can never disagree. Heads-up for the next session: this working directory was concurrently checked out to `claude/owner-auth-ratelimit` by another worker mid-session; my commits stayed intact on the `claude/overview-mobile-ux` ref and are pushed — shared-worktree contention, flagged to the coordinator.
needs-owner: the 15 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) — unchanged this session.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md) — 15 open
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004). RECON 2026-07-18: 0/4 websites-repo services have Discord login; REUSE of the existing SuperBot Discord app is the recommended cheapest path vs a fresh one — pending owner preference. Still OPEN.
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — decide the unwired SITE_PASSWORD on the botsite Railway service (wire or remove).
- ASK-0008 — extend the O-020 PAT with PR write + store as BAKE_PAT Actions secret. NOTE 2026-07-18: the PAT-scope half is already covered — the live control-plane GITHUB_TOKEN holds contents:write + pull-requests:write; only the BAKE_PAT Actions-secret half remains open (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).

## NEXT-2-TASKS baton
1. Post-merge live phone-width re-verify of the `/fleet` overview on the deployed control-plane (control-plane-production-abb0.up.railway.app) — confirm the count drill-downs expand and the status-card values wrap on a real 480px phone against live registry data.
2. OWNER-GATED — ASK-0002 Discord OAuth reuse for the future armed panel (REUSE the existing SuperBot Discord app; add a redirect URI + paste client id/secret into the websites Railway env), still gated on ASK-0001 / Q-0004; and the R10 auto-draft review edition (a hub-venue workflow-touch that won't self-land, depends on R8 + the owner-side hub decision).
- Note: O-020 owner writeback is LIVE; the Railway account API (RAILWAY_API_KEY) is available for self-verifying/setting deployed env (see docs/CAPABILITIES.md).

kit: v1.17.0
