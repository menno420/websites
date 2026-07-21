# Project closeout doc

- **Status:** in-progress
- **📊 Model:** opus-4.8 · high · docs-only
- **💡 Idea:** A single closeout doc that serves two cold readers at once — the owner (what exists, how to use it, what's still on him) and a fresh Claude session (boot route, verify commands, landing gotchas) — beats scattering that knowledge across records.
- **⟲ Previous-session review:** S5 (#469, submitter status lookup) landed clean with the born-red protocol; the four-marker card + valid PL-004 class + named-path staging kept the flip green first try. Carrying that discipline here.

## What
Add `docs/PROJECT-CLOSEOUT.md` — the final closeout of the autonomous agent build period. Link it from `docs/current-state.md` so the `[reachable]` doc-graph gate passes.

## Verify
- `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
- `env -u DATABASE_URL python3 bootstrap.py check --strict`
