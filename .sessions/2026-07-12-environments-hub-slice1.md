# 2026-07-12 — ORDER 021 slice 1: owner environments hub

> **Status:** `complete` — PR branch `claude/order-envhub-hub`; one slice,
> lands via the auto-merge-enabler on green.

- **📊 Model:** claude-fable-5 · websites worker · order (ORDER 021)

**What this session was about:** ORDER 021 slice 1 — the owner-gated
fleet-wide environments hub: one page listing every environment surface
(Railway projects/services, GitHub Actions secret stores, claude.ai cloud
envs) grouped per project-group, each row = surface · variable NAMES it
holds (never values) · deep link to where it is managed. Mid-session owner
refinement applied: the hub is THE single canonical environments home —
the three scattered views (fleet-manager schemas at `/environments`, live
Railway names at `/owner/environments`, the new inventory) consolidate
into one front door; the two old pages become clearly-labeled sub-views.

## What was done

- **Committed registry** `app/data/environments.json`: the verified fleet
  inventory (superbot-websites ×4 services, reliable-grace ×5 surfaces,
  superbot-mineverse, GitHub Actions secrets ×5 repos, claude.ai
  pinned-research), agent-updatable by PR. Names + links only; Railway ids
  recorded only where the repo proves them (docs/deployment.md SAFE
  literals) — unrecorded ids are `null`, never fabricated.
- **Loader/domain** `app/envhub.py`: schema validation that hard-rejects
  value-like fields and value-shaped "names"; manage-link ladder (full
  `railway.com/project/…/service/…/variables?environmentId=…` deep link →
  project link → explicit manage_url → console home); live variable-NAME
  merge for the superbot-websites group over the existing project-scoped
  `RAILWAY_TOKEN` read (honest degradation when unset/failing); ORDER 019
  `listfilter.ListSpec` (group + kind dimensions, search, A-Z sort).
- **Route** `GET /owner/environments-hub` in `app/owner.py` behind the
  exact `require_owner` gate, read-only; documented Discord-OAuth seam at
  the dependency (swap point only — OAuth deliberately NOT built).
- **Template** `owner_environments_hub.html`: list-IA summary header (jump
  anchors per group + the schemas section), `_listfilter.html` widget,
  per-group sections; embedded fleet-manager schema INDEX (new light
  `environments.index()` — names + links, no bodies, same honest
  degradation ladder as `overview()`); sub-view links both ways.
- **Consolidation** (owner refinement, live): `/owner/environments`
  retitled "live estate detail — environments-hub sub-view";
  `/environments` labeled the schemas sub-view (kept PUBLIC — it exposes
  nothing owner-only, exactly its existing exposure level); the hub's
  intro names all three consolidated views. `app/nav.py` untouched (the
  IA session owns placement).
- **SERVICES fix** in `app/railway.py`: the review service (live since
  2026-07-12, OWNER-ACTIONS row J) joins the committed facts — it now
  renders on `/owner/environments`; `ANTHROPIC_` manage-link prefix added;
  stale "no review deployment" footer corrected.
- **Tests** `tests/test_envhub.py` (+29 with the extended
  `test_owner_environments.py` run): registry shape, no-value guarantees,
  link degradation, 401/503 gate, no-token rendering, live merge with a
  sentinel value that must never appear, filter sections, SERVICES fix.

## 💡 Session idea

**Record the SAFE review-service Railway id** — worth having because the
review row currently degrades to a project-level link; one owner console
glance → a docs/deployment.md + registry PR upgrades it to the exact
variables deep link.

## ⟲ Previous-session review

Built directly on ORDER 019's listfilter core and the 2026-07-12 list-IA
pass (#200) — both reused verbatim (spec + partial + jump-anchor pattern),
zero new filter machinery. The ORDER 022 reconcile's verified facts
(review live, ANTHROPIC_API_KEY set) fed the registry instead of fresh
probing; nothing was carried from memory without a repo citation.
