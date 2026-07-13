# 2026-07-13 — single source of truth for link-bearing arcade availabilities

> **Status:** `in-progress` — branch `claude/arcade-link-truth-0713`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion-slice

**What this session was about:** backlog promotion — the
`docs/ideas/backlog.md` bullet "Single source of truth for link-bearing
arcade availabilities" (`captured` 2026-07-12, arcade download-probe session
💡). The /arcade page's `has_link` hardcodes `("live", "download")` in
`botsite/arcade.py` and the drift probe duplicates the same tuple as
`arcade_probe.PROBED_AVAILABILITIES` — two copies of the doctrine "which
availabilities carry outbound links" that nothing pins together. This session
moves the tuple to ONE constant (`arcade.LINKED_AVAILABILITIES`), consumes it
from both `has_link` and the probe, and adds a pin test asserting the probe's
coverage set is exactly the page's link-bearing set.

## What was done

- [[fill: implementation summary]]
- Verified: [[fill: verify outputs]]

⚑ Self-initiated: no — backlog promotion of the captured 2026-07-12 bullet
(`docs/ideas/backlog.md` "Single source of truth for link-bearing arcade
availabilities"); contained (botsite/arcade.py + botsite/arcade_probe.py +
botsite/tests + the backlog bullet flip) and reversible.

## 💡 Session idea

[[fill: session idea]]

## ⟲ Previous-session review

[[fill: previous-session review]]
