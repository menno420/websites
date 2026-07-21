# 2026-07-21 — botsite: richer arcade game detail pages (S6)

> **Status:** `in-progress` — branch `claude/arcade-richer-detail`; born red,
> holds the `quality` gate until the optional screenshots/controls/changelog
> sections land green. Flips to `complete` + PR number as the deliberate LAST
> code step (coordinator handles the flip after CI).

- **📊 Model:** opus-4.8 · medium · feature build

**What this session was about:** plan slice S6 of
`docs/plans/next-cycle-2026-07-20.md` (product frontier) — arcade detail pages
are thin (badges, tagline, description, play/download, blocker panel). This
slice adds three OPTIONAL, fail-soft sections to `arcade_detail.html`
(screenshots, controls, changelog), each guarded so a game with no such data
renders exactly as today. The normalizers mirror the existing optional
`blocker` pattern (`botsite/blockers.py`): missing/malformed data degrades to
an empty list and the section is hidden — never invented, never fatal. Which
work-ladder rung: coordinator-assigned plan slice (S6 in the current cycle
plan), the last of the ranked product slices.

## What was done

- **`botsite/arcade.py`** — three new local optional-field normalizers,
  mirroring the `blockers.normalized_blocker` fail-soft shape:
  `_normalized_screenshots` (list of `{src, alt}`), `_normalized_controls`
  (list of `{input, action}`, also accepts bare strings), and
  `_normalized_changelog` (list of `{version|date, note}`). Each drops
  malformed entries and returns `[]` on absence — never raises. Wired into
  `load_games` enrichment so `game.screenshots` / `game.controls` /
  `game.changelog` are ALWAYS present (possibly empty).
- **`botsite/templates/arcade_detail.html`** — three new sections, each
  guarded `{% if game.screenshots %}` / `{% if game.controls %}` /
  `{% if game.changelog %}`, styled with the existing `sb-panel` /
  `section-sm` classes. Screenshots render `<img loading="lazy">`; controls a
  two-column table; changelog a version/date list. A game with none renders
  byte-identically to before.
- **`botsite/data/arcade.json`** — populated ONLY real, build-time-verified
  content read from each game's public source repo (raw.githubusercontent.com,
  build-time WebFetch — the running app still reads committed JSON only):
  - lumen-drift: controls + v1.1/v1.2/v1.3 changelog (docs/PLAYING.md).
  - gloamline: controls + slice 8–11 changelog (docs/PLAYING-GLOAMLINE.md).
  - mineverse: stage 0/a/b/c/d changelog (README staged ladder); NO controls
    documented → left absent.
  - games-web: controls (topbar switcher, tooltips) + v1.0.0/v1.0.1 changelog
    (products/games-web/README.md).
  - screenshots: ABSENT for all four — originals are owner-held / not
    capturable here; the template wiring is proven by fixture-data tests. That
    is the correct fail-soft outcome.
- **`botsite/tests/test_arcade_detail_sections.py`** — new suite: valid data
  renders each section; absent data renders none and does not crash; malformed
  data (screenshots as a string, changelog entries missing keys, controls
  missing `action`) degrades to empty. Committed-registry field-presence pin.
- Verified: `env -u DATABASE_URL python3 -m pytest botsite/tests -q` and the
  full four-suite `env -u DATABASE_URL python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q`; `env -u DATABASE_URL python3 bootstrap.py
  check --strict --added-card .sessions/2026-07-21-arcade-richer-detail.md`
  (no `[session-card-grammar]`, only the born-red hold). Tails in the PR body.

⚑ Self-initiated: no — coordinator-assigned plan slice S6 of
`docs/plans/next-cycle-2026-07-20.md`.

## 💡 Session idea

**Build-time arcade doc-baker — regenerate controls/changelog from each game
repo's committed docs.** This slice hand-copied controls/changelog out of each
game's `PLAYING.md` / `README.md` at build time; a small `gen_arcade_detail.py`
(the review `gen_*.py` reproducible-from-source pattern) could re-derive those
fields from the source docs and diff against `arcade.json`, so the committed
detail data can't silently drift from what the game repos actually document.
Worth having because hand-copied game docs rot the moment a game repo ships a
new version and nobody re-copies — a baker keeps the arcade's TRUTH bar honest
without manual re-transcription. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: not present (the closest bullets are the review edition
auto-drafter and the vendored-core guard — different surfaces). Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

`.sessions/2026-07-19-app-nav-reachability.md` (#450) did it right: it derived
every allowed HTTP status by actually GETting each route rather than inventing
the set, and it completed a property (reachability) across all four services
instead of leaving `app/` half-covered — the lesson carried here is to
populate detail fields only from content actually read at build time, never
fabricated.
