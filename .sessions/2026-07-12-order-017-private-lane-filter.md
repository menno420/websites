# 2026-07-12 — ORDER 017 D compliance: the Pokémon lane stays private on the review site

> **Status:** `in-progress` — branch `claude/order-017-private-lane-filter`;
> flips to `complete` as the deliberate LAST code step.

- **📊 Model:** claude-fable-5 · build worker · order

**What this session was about:** Rung: order — ORDER 017 workstream D
requires "the Pokémon lane stays private", but the public review site's
`/fleet` page rendered a lane card for the private repo (name + github link
+ "live" chip + no-heartbeat lines). Scope: remove the private lane from
every public surface of the review/ service — bake-time exclusion in
`gen_fleet.py`, defensive render-time filter in `fleetdata.py`, regenerated
mirrors, evidence-corpus scrub, and a rendered-HTML regression test.

## What was done

- (filled at close-out)

⚑ Self-initiated: no — ORDER 017 workstream D compliance fix, routed by the
coordinator.

## 💡 Session idea

- (filled at close-out)

## ⟲ Previous-session review

- (filled at close-out)
