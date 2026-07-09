# 2026-07-09 — /fleet lane set from the live manifest

> **Status:** `complete` — shipped as PR #36 (`claude/fleet-manifest-live`, squash-merged).

- **📊 Model:** Opus 4.8 · worker · fleet-manifest-live

**What this session did:** self-directed improvement on the `/fleet` control-plane
page — derived the fleet lane set **live** from the manager's canonical manifest
(`menno420/superbot` → `docs/eap/fleet-manifest.md`) instead of the hand-kept
`config.FLEET_LANES` copy, with an honest fallback to that list; and fixed the
websites dogfood `control/status.md` timestamp to a full ISO value so its own
`/fleet` row shows a real freshness age. This resolves the D-0021 "lane-set is
hand-kept / drift risk" ⚑ flagged to the owner.

## What was done

- **`app/fleet.py`** — new live-manifest layer:
  - `MANIFEST_REPO` / `MANIFEST_PATH` point at `superbot/docs/eap/fleet-manifest.md`
    (fetched **read-only** at request time via the shared TTL-cached `github`
    layer; superbot is never written).
  - `parse_manifest(text)` — reads the manifest's markdown table, mapping columns
    by **header name** (Project / Repo(s) / Model / Notes …) so a column reorder
    can't shift a value; extracts every `menno420/<repo>` from the Repo(s) cell;
    skips the header-separator row.
  - `manifest_to_lanes(rows)` — expands rows into the existing lane-dict shape:
    the `manager` row (no concrete repo) is skipped; a **multi-repo** Project
    (SuperBot coordinator, `superbot · superbot-next`) → one lane per repo
    (superbot's own status 404s as an honest absence — its heartbeat is in
    superbot-next); a repo **shared** across rows (superbot-games) →
    `control/status-<slug>.md`, slug from the Project name (`game-mining`→`mining`).
  - `resolve_lanes(refresh)` — PRIMARY = manifest; on any fetch/parse failure or a
    zero-lane parse, FALLBACK = `config.FLEET_LANES` with an honest
    `{source:"fallback", reason:…}`. Success returns `{source:"manifest", count}`.
  - `lane_status` — added an honest `unreadable` state for 401/403 (a manifest
    lane whose repo the token can't read is rendered, never dropped).
  - `overview` — now calls `resolve_lanes`, threads `lane_source` into the payload.
- **`app/templates/fleet.html`** — intro reworded ("lane set derived **live** from
  the manifest"); shows a green `live from manifest` badge when manifest-sourced,
  or a visible **"cached fallback list"** banner (with reason) on fallback.
- **`config.FLEET_LANES`** — kept **as the fallback** (unchanged), no longer the
  primary source.
- **Tests (`tests/test_app.py`) +6** (111 → 117): manifest parse yields the
  expected 10 lanes and they match the fallback set; a manifest-added lane
  auto-appears; resolve uses the manifest when available; resolve falls back +
  labels on fetch failure; overview reports manifest-sourced; unreadable repo is
  honest, not dropped.
- **Docs:** `docs/site.md` § Routes (/fleet now manifest-sourced), `[D-0022]` in
  `docs/decisions.md`, `docs/current-state.md` Recently-shipped + status line.
- **`control/status.md`** — overwritten LAST with a **full ISO timestamp**
  (`2026-07-09T16:30Z`) so the websites `/fleet` row shows a real age; the
  D-0021 lane-set drift ⚑ marked **resolved** by this PR.

## Verification

- Parser validated against the **real** manifest (fetched via raw host): yields
  exactly the 10 lanes with `(repo, status_path)` byte-identical to the prior
  hand-kept `config.FLEET_LANES` — drift-free by construction.
- `python3 -m pytest tests/ botsite/tests dashboard/tests` — 117 passed.
- `python3 bootstrap.py check --strict --require-session-log --session-log <this>` — green.
- Live render smoke: `/fleet` 200 with `live from manifest` badge; `/fleet.json`
  `lane_source=manifest`, total 10.

## Decisions made this session

- Parse the lane SET live (drift removal) but keep `config.FLEET_LANES` as an
  honest fallback rather than deleting it — the page never goes blank if superbot
  is briefly unreachable, and the fallback is visibly labeled so it never lies.
- Map manifest columns by header name (not position) and expand multi-repo /
  shared-repo rows in `manifest_to_lanes` — the manifest genuinely doesn't encode
  status-file paths, so the shared-lane slug + multi-repo split are the app-side
  rendering convention, applied to a manifest-derived set.

## 💡 Session idea

`/fleet` (and the manifest parse) could grow a **"manifest ↔ live drift" cell**:
compare the manifest's `Last-seen` column for each Project against the lane's own
`control/status.md` `updated:` timestamp, and badge a lane where the manager's
recorded last-seen is materially staler than the lane's real heartbeat (the
manager hasn't rolled up that Project recently) — turning the two independent
freshness signals into a check that the manager's rollup itself is current.

## ⟲ Previous-session review

Previous session (ORDER 002, PR #35) built `/fleet` cleanly and, to its credit,
**named the drift risk itself** — it flagged the hand-kept `config.FLEET_LANES`
as a ⚑ to the owner rather than hiding it, which is exactly what made this
follow-up a five-minute decision instead of an archaeology dig. What it could
have done better: it validated the parser "against all 10 real lane status files"
but left the lane SET hand-kept — the same session had the manifest content in
hand and could have parsed it live then. **System improvement it surfaces:** a
self-flagged ⚑ that describes a *contained, reversible, test-coverable* follow-up
(like "parse the manifest live") is really a ready-to-build idea, not an
owner-decision — the workflow could route "⚑ + contained + reversible" flags
straight into `docs/ideas/` as pre-approved build candidates so they don't wait
on an owner glance the collaboration model (Q-0172) already says they don't need.

## Documentation audit

- `docs/decisions.md` — `[D-0022]` added (next free D-number; D-0021 was the last).
- `docs/current-state.md` — Recently-shipped entry + status-line date updated.
- `docs/site.md` — /fleet § rewritten to describe the live-manifest source.
- No owner decision to route (self-directed; the D-0021 ⚑ this resolves is noted
  resolved in `control/status.md`). No new doc needs a reachability link.
