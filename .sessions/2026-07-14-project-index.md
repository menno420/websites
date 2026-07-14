# 2026-07-14 — populate project.index.json (fleet cleanup audit suggestion 3)

> **Status:** `in-progress` — branch `claude/project-index-0714`; flips to
> `complete` + PR number as the deliberate LAST code step.

- **📊 Model:** Claude Fable 5 · worker · backlog-promotion

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

[[fill: close-out]]

## ⟲ Previous-session review

[[fill: close-out]]
