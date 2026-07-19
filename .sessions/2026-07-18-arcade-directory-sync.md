# 2026-07-18 — Arcade + /directory registry sync (Lumen Drift direct-download, games-web live)

> **Status:** `complete` — branch `claude/arcade-directory-sync`. Born red:
> this card holds the `docs`/`quality` gate red until the two registries are
> synced to live reality, the drift guard lands, and the whole suite is green.

- **📊 Model:** Opus 4.8 · high effort · registry-sync + drift-guard

**What this session is about:** after #428 flipped the arcade live, two registries
still disagree about the same games. `botsite/data/arcade.json` points Lumen Drift
at the release *page* (the no-asset fallback the #428 session recorded because the
direct `.gba` asset could not be HTTP-verified from that session's egress), and
`app/data/web_presence.json` still marks BOTH Lumen Drift and games-web
`pending-publish` with `url:null` — stale. This session (a) repoints Lumen Drift's
arcade download to the now-confirmed direct `.gba` asset
(`https://github.com/menno420/gba-homebrew/releases/download/lumen-drift-v1.3/lumen-drift.gba`,
164 KB, SHA256 195a86795e57e2fa0059a96782f1ac7a147cbcebc0cb28a96f353e5d9babae94),
(b) syncs both `web_presence.json` rows to their live state, and (c) adds the
cross-registry drift guard flagged as the 💡 idea of `.sessions/2026-07-18-lumen-drift-live.md`.

## Plan

- Repoint the `lumen-drift` entry in `botsite/data/arcade.json` to the direct
  `.gba` asset URL (keep `availability: download`); update the `LUMEN_DRIFT_URL`
  constant in `botsite/tests/test_arcade.py` in tandem.
- Sync `app/data/web_presence.json`: lumen-drift → live with the direct `.gba`
  URL, games-web → live with its Pages URL, clear the stale `unblocked_by` on
  both, bump `as_of` to 2026-07-18, and decide `probe` per the loader's real
  fetch behavior (a raw-content probe of a release binary / Pages host).
- Repoint `tests/test_web_directory.py`: replace the stale `unblocked_by`/pending
  assertions with the new live-state render.
- Add a cross-registry drift guard (arcade.json vs web_presence.json for the
  shared `lumen-drift` / `games-web` keys) that is green now, red on future drift.
- Full gate green (`tests/ botsite/tests dashboard/tests review/tests` +
  `bootstrap.py check --strict`), then flip this card.

⚑ Self-initiated: no — coordinator-dispatched follow-up to #428 / the
`lumen-drift-live` session's flagged cross-registry-drift idea.

## 💡 Session idea

Add `follow_redirects=True` (or a HEAD-with-redirect probe) to the `/directory`
release-download probe path so a live `.gba` download can be health-probed
instead of being marked `probe:false` — today a 302→CDN redirect would
false-negative as "degraded (HTTP 302)".

## ⟲ Previous-session review

Builds on the release-drift-banner card (ORDER 033), whose 💡 idea (a
published-Release REST cross-check) is what motivated verifying the real
`.gba` asset directly this session rather than trusting the stale registry.
