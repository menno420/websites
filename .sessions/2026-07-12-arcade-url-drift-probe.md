# 2026-07-12 — Arcade live-URL drift probe (healthcheck pass)

> **Status:** `in-progress` — branch `claude/arcade-url-drift-probe`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** `botsite/data/arcade.json` presents games
with `availability: "live"` URLs, but nothing re-verifies those URLs after
the card ships — a dead game link silently outlives its card (ORDER 022
flipped mineverse by hand to notice exactly this). This session builds the
probe: every live-availability URL is cold-fetched by the scheduled
healthcheck and flagged when it stops returning 200. Live network fetches
stay OUT of the required `quality` gate — probe logic is unit-tested against
`httpx.MockTransport`; the real fetch runs only via
`scripts/healthcheck.py` / `healthcheck.yml`. Coordinator-assigned slice;
executes the backlog bullet "Arcade live-URL drift probe" (captured
2026-07-12, ORDER 022 drift session).

## What was done

- (in progress — filled at close-out)

⚑ Self-initiated: no — coordinator-assigned slice executing an existing
backlog bullet.

## 💡 Session idea

(filled at close-out)

## ⟲ Previous-session review

(filled at close-out)
