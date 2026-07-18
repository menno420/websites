# 2026-07-18 — Arcade goes fully live: lumen-drift + games-web flip (ASK-0010 / ASK-0011)

> **Status:** `complete` — branch `claude/lumen-drift-live`. This flip releases
> the born-red gate: it kept the `quality` check red until the arcade flip, the
> refreshed release-drift bake, the ledger update, and the repointed tests all
> landed green.

- **📊 Model:** Claude Opus · high · feature build

**What this session is about:** two long-standing arcade launch blockers cleared
in one owner sitting. The owner (a) published the GitHub Release
`lumen-drift-v1.3` on `menno420/gba-homebrew` (satisfying **ASK-0010**) and (b)
ran product-forge's "Deploy games-web to Pages" workflow so
`https://menno420.github.io/product-forge/` now answers 200 with the real
character-sheet app (satisfying **ASK-0011**). This session records both in
`botsite/data/arcade.json` — lumen-drift → `download`, games-web → `live`, both
blockers dropped — rebakes `review/data/releases.json` (lumen-drift drift flips
to false), marks both ledger rows satisfied, and repoints the tests that pinned
the blocked state.

## Plan

- Verify both landings independently (release tag over git transport; the Pages
  site over HTTPS with a real-content snippet).
- Flip both `arcade.json` entries to a resolved shape (match the mineverse
  entry: availability set, url set, no `blocker` key).
- Rebake `review/data/releases.json` via `python3 review/gen_releases.py`;
  lumen-drift drift → false (expected tag == live tag).
- Mark ASK-0010 + ASK-0011 satisfied in `docs/owner/OWNER-ACTIONS.md`.
- Repoint `botsite/tests/test_arcade.py` (the whole arcade is now reachable:
  3 live, 0 blocked, 0 owner clicks; retire the games-web dead-URL pin).
- Full gate green, then flip this card.

⚑ Self-initiated: no — coordinator-dispatched, executing the recorded owner
clicks for ASK-0010 and ASK-0011.

## What was done

- **Verified both landings independently.** `git ls-remote --tags` reads the
  live tag `lumen-drift-v1.3` on gba-homebrew (SHA
  `e64651ce4dbb5e99f31adf370da23f31716ef849`); the release-drift bake then
  confirmed it end-to-end (expected == live → `drift: false`). The product-forge
  Pages site returns HTTP 200 with real content (`<title>games-web · Character
  Sheet (phase 1 · mock data)</title>` — not a Pages 404 placeholder).
- **Flipped `botsite/data/arcade.json`** to the resolved (blocker-less) shape:
  lumen-drift → `availability: download`, url = the published release page;
  games-web → `availability: live`, url = the Pages site. The arcade is now
  fully reachable (mineverse live, games-web live, lumen-drift download).
- **Rebaked `review/data/releases.json`** (`python3 review/gen_releases.py`):
  `drift_count` 1 → 0, lumen-drift reason now "expected release lumen-drift-v1.3
  matches the live latest tag" (the tag token kept in the new status_note so the
  bake's regex still detects the expected tag).
- **Marked ASK-0010 + ASK-0011 satisfied** in `docs/owner/OWNER-ACTIONS.md`
  (Decided rows P/Q; the six-field ask text kept verbatim per "do not delete,
  move"). Open asks 15 → 13.
- **Repointed the tests.** `botsite/tests/test_arcade.py` — the games-web
  dead-URL pin is retired to a live Play-link assertion, lumen-drift now asserts
  a Download affordance, and the summary/queue/blocker tests reflect 3-live /
  0-blocked. `tests/test_askverify.py` — the open-ledger count drops to 13 and
  the arcade registry no longer carries the launch-blocker join (the probe
  registry entries survive for any future re-open).
- **`app/askverify.py` needed NO code change** (confirmed): its
  `lumen-drift-release` and `product-forge-pages` probes read live endpoints
  directly (now 200), independent of `arcade.json` — no data pointer was wrong.
- **Heartbeat refreshed** (`control/status.md`) to the post-flip state.
- **Gate:** full suite (`tests/ botsite/tests dashboard/tests review/tests`)
  **1924 passed, 1 warning** (the pre-existing Starlette/httpx testclient
  deprecation); `bootstrap.py check --strict` clean but for the designed
  born-red hold on this card, released by this flip.

**Honest wall (headline):** the direct `.gba` asset URL could NOT be
HTTP-verified from this session — github.com web/API access to gba-homebrew is
walled by the session egress policy (only git transport is allowed; the release
page and api.github.com both returned session-scoped 403s). So the recorded
download target is the **published release page**
(`.../releases/tag/lumen-drift-v1.3`), which is guaranteed-live and never a dead
link — the task's explicit no-asset fallback. If the owner/coordinator confirms
the attached asset filename, a one-line repoint to the direct asset URL follows.

## 💡 Session idea

**A cross-registry availability-drift guard.** This flip updated
`botsite/data/arcade.json`, but the control-plane `/directory` page reads a
SEPARATE registry (`app/data/web_presence.json`) that still labels Lumen Drift +
games-web "pending" — the two registries now disagree about the same games'
reachability, and nothing catches it. A small test (or a healthcheck pass) that
joins the arcade registry to `web_presence.json` by game and flags an
availability mismatch would keep the two public surfaces honest after any future
arcade flip, the same way `test_askverify.py` already pins arcade blockers to the
ledger. Distinct from this PR (a new guard over a second registry, not the
arcade flip itself).

## ⟲ Previous-session review

`.sessions/2026-07-18-nav-reachability-guard.md` (PR #421, complete) closed a
real gap cleanly — off-nav pages were *classified* but never proven to still
*respond* — and did the right thing by pinning botsite's `/testing/owner` to a
documented `{401, 503}` status set rather than a blunt 200, keeping the guard
exact. It also ended on a precisely-scoped session idea (extend the reachability
assertion to `app/`'s control-plane pages) rather than stretching its PR. One
note for its successor: that idea and this session's cross-registry-drift idea
both point at the same underlying pattern — a manifest/registry that lists a
surface without a test proving the surface's live claim — worth folding into a
single "registry-claims-are-verified" guard family rather than one-off tests.
