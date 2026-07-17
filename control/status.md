# websites · status

updated: 2026-07-17T12:12:53Z
phase: failsafe-wake lane close-out (this session) — appending to the coordinator's #384 close-out heartbeat rather than overwriting it: corrects a stale-branch mixup (below) and hands off cleanly. Aligning with the coordinator's explicit choice not to re-arm fine-grained chains (see routine): this is this lane's LAST self-armed 15-min cycle — reverting to the 2h failsafe cron only, matching the "successor's dead-man bridge" design.
health: green — origin/main @ 12591b2 (#384). Full four-suite run this cycle (36 back): 1713 passed on ecbe2bf; unchanged since (control-only diffs landed after).
orders: acked=001-032 done=001-019,023-031 (020/021 owner-gated; 022 standing; 031 EAP extended to 2026-07-21, routines not re-armed pending owner per-seat go; 032 STANDING — owner live overnight-autonomy order).
open-PRs: none per #384's live-verified count — this lane's own branches were never opened as PRs (no PR-creation tooling, ASK-0017), so they don't show in that count; see below.
correction to this lane's own earlier heartbeats: `claude/arcade-catalog-blockers` and `claude/games-availability-summary` were repeatedly flagged as "independent, worth landing" (including in a push notification sent ~90min ago) — WRONG. Checked just now: both are already landed, functionally duplicated by other sessions under different PRs — arcade-catalog-blockers ≡ #369 (`git log -S "def availability_summary"` finds it there), games-availability-summary ≡ #371 (identical commit messages, session_01Lw5z3gWSFQvP64RWcM2Tbu). Both tracked branches are now orphaned duplicates, same class the claims-drift gate catches for claim files — safe to delete/ignore, NOT to open as PRs (would conflict). Apologies for the earlier bad steer.
this lane's ACTUALLY-still-unique unlanded work (6 branches, none duplicated by the landed PRs above — checked): `claude/pr-tooling-ask-20260716` (files ASK-0017), `claude/fastlane-pin-map-20260716`, `claude/storefront-freshness-pin-20260716`, `claude/claim-pr-fallback-20260716`, `claude/catalog-sha-drift-pin-20260716`, `claude/catalog-drift-review-20260716` (files ASK-0018 — the real the-paper-orange status error, still unaddressed). Plus this lane's own heartbeat branches (2049 through this one) — only the latest matters, rest are superseded, ignore.
landed-this-session: ~12 feature slices, all merged + Railway-live. Console: unblocks-N chips (#368), release-drift (#369), dispatch-readiness chips (#378). Arcade: catalog-blockers (#370), /games launch strip (#371), owner-action-queue panel (#381). Dashboard /ideas: shipped-count (#372), lifecycle filter pills (#382). Review: documented-count (#376), evidence-citation tallies (#383). CI guards: deploy-target guard (#377), arcade-registry integrity guard (#379). Records PR #374 already on main.
planning-menus:
- #373 MERGED — docs/planning/arcade-dashboard-menu-2026-07-16.md (24 proposals, docs-only).
- #375 CLOSED unmerged — console/review menu (37 proposals). Preserved on branch claude/console-review-menu-20260716 + docs/planning/2026-07-16-console-review-menu.md. Owner reland decision pending.
closed-not-landed (were held, now disposed):
- #359 — automated fleet-data bake PR, CLOSED unmerged. Underlying need persists: hands-off nightly bake still blocked on BAKE_PAT PR-write secret (ASK-0008 / docs/owner/OWNER-ACTIONS.md).
- #367 — born-red rescue straggler card (main-boot auto-draft), CLOSED unmerged. Sibling rescue drafts #361/#363 already closed earlier.
landing-mechanism: server-side auto-merge WORKS for READY (non-draft) claude/* PRs via auto-merge-enabler.yml — proven this session: #381/#382/#383 self-landed on flip-to-green, zero human keystroke. Convention going forward: open claude/* PRs READY with the born-red session card as the brake. A draft-gap patch (auto-flip green drafts to ready) is STAGED but OPTIONAL, held by another session pending the owner's first-hand go-ahead (workflow write needs owner provenance).
routine: no new triggers/pacemakers armed by the coordinator; this lane matches that now (see phase line — no more self-armed 15-min chain from this session). The seat FAILSAFE cron "Websites failsafe wake" (45 */2 * * *) stays ARMED as the dead-man bridge — fires ~every 2h.
needs-owner: the 16 ⚑ rows in docs/owner/OWNER-ACTIONS.md (mirror below) PLUS ASK-0017 and ASK-0018, both still unlanded on this lane's own branches (see above) — neither made it into the canonical doc yet since neither has a PR.

## ⚑ OWNER-ACTION mirror (canonical: docs/owner/OWNER-ACTIONS.md)
- ASK-0001 — answer Q-0004: where live bot control lives (or keep /admin dry-run).
- ASK-0002 — create the Discord OAuth app for the future armed panel (after Q-0004).
- ASK-0003 — provision the scoped control-API token + separate armed Railway service (after Q-0004).
- ASK-0004 — create the botsite submissions PostgreSQL + connection string.
- ASK-0005 — set up PayPal Payouts + put its two credentials on the botsite service.
- ASK-0006 — set SITE_PASSWORD on the botsite Railway service.
- ASK-0007 — mint the fine-grained contents-write PAT → GITHUB_TOKEN on control-plane + botsite.
- ASK-0008 — extend that PAT with PR write + store as BAKE_PAT Actions secret (unblocks hands-off nightly bake).
- ASK-0009 — delete the unused SITE_PASSWORD variable from the dashboard service.
- ASK-0010 — publish the lumen-drift-v1.3 release on gba-homebrew (unblocks the arcade Download button; machine-probed — the #365 drift pass now watches it every healthcheck).
- ASK-0011 — flip product-forge Settings → Pages → Source to GitHub Actions (unblocks the games-web Play link; machine-probed — same drift-pass watch).
- ASK-0012 — run the Gumroad publish pass for the ten publish-ready titles/products (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0013 — hand off the full-res photo originals for the two wallpaper packs (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0014 — pick the Ultramarine title: "The Widow's Blue" or keep Ultramarine (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0015 — decide the §5 illustration gate for the two picture books + three Puddle Museum editions (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0016 — arrange the native-speaker Dutch proofread for de-papieren-sinaasappel (details in docs/owner/OWNER-ACTIONS.md).
- ASK-0017 — connect the Claude GitHub App for the org (unlanded — filed on claude/pr-tooling-ask-20260716; without it, sessions of this lane's kind can push branches but never open PRs).
- ASK-0018 — review + apply the catalog.json drift fixes, esp. the-paper-orange's real status error (unlanded — filed on claude/catalog-drift-review-20260716).

## NEXT-2-TASKS baton
1. Owner decision on the #375 reland (console/review menu, preserved on claude/console-review-menu-20260716) — plus any veto of #373's merged picks.
2. Whoever has PR tooling next: open PRs for this lane's 6 still-unique branches (see the correction note above) — each is self-contained, tested, and green. ASK-0017 is the one that stops this recurring.

kit: v1.17.0
