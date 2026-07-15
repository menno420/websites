# 2026-07-14 — populate project.index.json (fleet cleanup audit suggestion 3)

> **Status:** `complete` — PR #319, branch `claude/project-index-0714`;
> the AgentContextPack index now maps the four real service areas
> (control-plane / botsite / dashboard / review) to their folios, source
> roots and verification commands; lands via the auto-merge enabler on
> green.

- **📊 Model:** Claude Fable 5 · medium · docs-only (populate project.index.json, backlog-promotion)

**What this session was about:** the merged fleet cleanup audit
(`docs/audits/2026-07-13-fleet-cleanup-audit.md`, suggestion 3) flagged
`project.index.json` as dead scaffolding — the AgentContextPack manifest
index was still the adopt-flow placeholder (`example-area`, every field
empty) despite the repo having four well-documented service areas. The
decided route: populate it honestly with the real areas (control-plane /
botsite / dashboard / review), matching the exact schema the consumer
(`bootstrap.py` `contextpack` subcommand, engine/contextpack.py,
design-spec 2.10) reads.

## What was done

- `project.index.json` — replaced the placeholder `example-area` with the
  four real areas, each populated per the consumer schema (`name`, `folio`,
  `binding_docs`, `source_roots`, `do_not_create`, `gates`, `verification`):
  control-plane → `app/` + `tests/`, folio `docs/site.md`; botsite →
  `botsite/` + `botsite/tests/`, folio `docs/botsite.md`; dashboard →
  `dashboard/` + `dashboard/tests/`, folio `docs/dashboard.md`; review →
  `review/` + `review/tests/` + `review/data/`, folio `review/README.md`.
  Every area's `verification` carries the two real pre-push commands;
  `do_not_create` records genuinely-existing systems (app/github.py TTL
  client, the `ds/` design system, the dashboard's no-auth/no-write-path
  decisions, review's bake-don't-fetch data model); `gates` left honestly
  empty — no active expansion conditions to record.
- Proved the consumer: `python3 bootstrap.py contextpack` generated all
  four packs under `.substrate/contextpacks/` (control-plane, botsite,
  dashboard, review) with zero `(MISSING)` flags — every `source_roots`
  entry passed the generator's existence check.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1365 passed; `python3 bootstrap.py check --strict` —
  green (this card's own designed born-red HOLD until the close-out flip).

⚑ Self-initiated: no — backlog promotion of the merged audit's suggestion 3
(`docs/audits/2026-07-13-fleet-cleanup-audit.md`: "Either populate
`project.index.json` or remove/park it with a note" — populate chosen).

## 💡 Session idea

**Index-drift advisory in `check` — existence-check `project.index.json`
paths on every run** — the contextpack generator existence-checks
`source_roots` only when someone runs `python3 bootstrap.py contextpack`,
which nothing schedules; a renamed folio or moved source root rots the
index silently until the next manual generation. A `check`-time advisory
(never exit-affecting) that walks every area's `folio`, `binding_docs`
and `source_roots` entries and warns on missing paths would surface drift
in every CI run for near-zero cost. Worth having because a
populated-but-stale index is worse than the empty placeholder this
session replaced — it misleads with confidence instead of signalling
neglect. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: no bullet mentions contextpacks or project.index.json at all.
Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — 22 entries
curated with per-title honesty and pinned by a registry test so the page
cannot silently claim a different breakdown; what it missed: the pin
freezes the 1/12/2/7 snapshot against upstream movement it cannot see —
its own sha-drift idea (a fine one) landed only as a backlog bullet, so
the decay watch it identified still depends on a future session picking
it up.
