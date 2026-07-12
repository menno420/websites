# 2026-07-12 — /prompts pinned-registry drift chip

> **Status:** `in-progress` — branch `claude/prompts-registry-drift-chip`; flips to `complete`
> + PR number as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · worker · feature-slice

**What this session was about:** the /prompts library pins its seat list
(`app/roster.py` `SEATS`) rather than discovering it, so a seat added or
renamed in the fleet-manager `projects/` registry silently drifts — dead 404
cells with no signal. This session cross-checks the pinned set against the
`projects/` registry listing the app already fetches (same TTL-cached
`github.repo_api` call /projects makes — zero new network surface) and
renders an honest drift chip on /prompts: match / drifted (+new − missing,
named) / registry-unavailable (drift unknown, never a fabricated green).
Coordinator-assigned slice.

## What was done

- [[fill: changes]]
- Verified: [[fill: verification]]

⚑ Self-initiated: no — coordinator-assigned slice.

## 💡 Session idea

[[fill: idea]]

## ⟲ Previous-session review

[[fill: previous-session review]]
