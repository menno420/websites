# 2026-07-12 — widen /journal/{repo}/file render guard to fleet lane repos

> **Status:** `complete` — PR #177 (`claude/journal-guard-fleet`).

- **📊 Model:** claude-fable-5 · worker seat · guard-widening + tests

**What this session was about:** Grounded-skills slice 7 (rung: order —
coordinator-directed slice from substrate-kit
`docs/planning/2026-07-12-grounded-skills-program.md` §7): widen the
control-plane `/journal/{repo}/file` repo guard from the four `config.REPOS`
entries to every fleet lane repo, via a derived allow-set — `REPOS` itself
stays untouched so the readiness board / journal corpus fan-out is unchanged.

## What was done

- `app/config.py`: new derived allow-set `JOURNAL_RENDER_REPOS = set(REPOS) |
  {lane["repo"] for lane in FLEET_LANES}` directly below `FLEET_LANES`, with a
  comment noting the fleet set derives from `FLEET_LANES` (mirror of the kit's
  generated `docs/adopters.md` registry) and that `REPOS` must not grow from
  here. Repos gained: gba-homebrew, product-forge, superbot-idle,
  trading-strategy, superbot-mineverse, idea-engine, superbot-games,
  fleet-manager, codetool-lab-fable5, sim-lab, venture-lab, pokemon-mod-lab,
  codetool-lab-opus4.8, codetool-lab-sonnet5 (14 new; 4 REPOS entries
  unchanged).
- `app/main.py` `journal_file`: guard now checks
  `config.JOURNAL_RENDER_REPOS` (was `config.REPOS`). Path-traversal 400
  guard untouched; sibling `/journal/{repo}` overview route untouched (its
  per-repo journal view depends on `REPOS` metadata).
- `tests/test_app.py` (+4, beside `test_unknown_repo_404`):
  `test_journal_file_unknown_repo_still_404`,
  `test_journal_file_bad_path_still_400`,
  `test_journal_file_fleet_lane_repo_renders` (sim-lab — asserts it is NOT
  in `REPOS`, IS in the render set, and renders mocked markdown),
  `test_journal_file_original_repo_still_renders` (superbot). All mock
  `github.fetch_file` — no network.
- `docs/site.md` routes table: file-route row now notes it accepts any fleet
  lane repo via `JOURNAL_RENDER_REPOS`.
- Private fleet-manager content still won't render until the GITHUB_TOKEN
  owner action lands — queued owner action, deliberately NOT this slice.
- Verified: `python3 -m pytest tests/ -q` — 217 passed (213 + 4 new);
  `python3 -m pytest botsite/tests dashboard/tests review/tests -q` — 141
  passed; `python3 bootstrap.py check --strict` — sole red was the designed
  born-red session-card hold (`HOLD (by design)`), plus the pre-existing
  lane-owed `[owner-action-risk-class]` advisory on control/status.md
  (never exit-affecting, out of this slice's scope).

⚑ Self-initiated: no — coordinator-directed grounded-skills slice 7.

## 💡 Session idea

**Deep-link fleet lane files into the widened /journal/{repo}/file view** —
the file route now renders markdown from every FLEET_LANES repo, but no page
links there for lane repos; add per-lane deep-links from the /fleet lane
cards (lane `docs/current-state.md`, `control/status.md` source) through the
in-app renderer. Worth having because a shipped capability nothing navigates
to is invisible to the owner. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: the lanes.json / pickup ideas touch /fleet data, not
file-view navigation. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.14.0 kit-upgrade session (#171) did well applying its own predecessor's
lesson — it named every diverged doc on the card itself instead of just
counts, so this session could orient without opening the archived upgrade
report. What it missed: its card flagged the `[owner-action-risk-class]`
advisory as "lane-owed" but didn't route it anywhere actionable (no backlog
bullet, no owner-actions entry), so the advisory still fires unowned two
sessions later — a flagged-but-unrouted advisory is drift with a timestamp.
