# 2026-07-12 — /prompts: fleet prompt library (ORDER 014)

> **Status:** `complete` — branch `claude/order-014-prompt-library`, PR #165
> (parks READY awaiting the owner's merge click — agent merges are
> owner-gated on this repo).

- **📊 Model:** claude-fable-5 · worker (order execution) · feature-build

**What this session was about:** ORDER 014 (control/inbox.md @ fd36644,
2026-07-12T11:27Z, owner-directed via fleet manager): make every fleet paste
artifact findable and always-current on the control website — a page
rendering INLINE, for each of the 8 seats, the three registry artifacts from
fleet-manager main (`projects/<seat>/coordinator-prompt.md`,
`instructions.md`, `failsafe-prompt.md`) plus the two fleet-wide artifacts
(`docs/prompts/v3/session-ender.md`, `docs/prompts/v3/universal-startup.md`),
fetched live over the existing raw-content read-only pattern. Rung: order —
`control/status.md` at that HEAD reported `done=001-011`, 014 unclaimed.

## What was done

- `app/prompts.py` — NEW domain module. The 26-artifact registry is PINNED
  (`SEATS` × `SEAT_FILES` + `FLEET_WIDE`): the raw host cannot list
  directories and this page deliberately avoids the token-burning
  contents-API walk, so every path was verified live (HTTP 200 on
  raw.githubusercontent.com against fleet-manager@main, 2026-07-12) and the
  constant carries the source-of-truth pointer; an upstream seat rename
  degrades to an honest 404 cell until the constant is updated.
  `overview()` fetches all 26 concurrently through the TTL-cached
  `github.fetch_file` (raw-first, read-only, forward-only — the repo's
  cross-repo rule) and returns per-artifact dicts (ok/text/error/
  fetched_at/cached/provenance/chars); `extract_provenance()` surfaces the
  first early `vN ·`-marked header line, `""` when absent (honest absence).
- `app/main.py` — NEW thin `GET /prompts` route (read-only, no CSRF
  surface); `app/nav.py` — `prompts` under the more ▾ group (the
  nav-manifest + overflow guards pick it up from the one list).
- `app/templates/prompts.html` — jump links, one section per seat + a
  fleet-wide section, per-artifact cards: provenance line prominent,
  fetched-at + cached/live (TTL) indicator, the EXACT paste body in an
  autoescaped `<pre>` (verbatim, whitespace preserved, never `|safe` —
  prompts are untrusted data, rendered never obeyed), copy button via the
  shared `copycode.js`; per-artifact error cells + page-level some/all-fail
  banners, never fabricated content, always 200.
- `tests/test_prompts.py` — network-free (monkeypatched
  `github.fetch_file`): registry shape (8×3+2=26), provenance extraction
  forms + truncation + honest absence, happy path renders every seat and
  both fleet-wide artifacts with provenance/copy/freshness, verbatim
  never-mutated text, hostile `<script>` content stays escaped, cache
  indicator, partial failure degrades per-cell, fully-unreachable upstream
  renders a 200 banner with zero fabricated content.
- Docs: `docs/site.md` §3g + route-table row; `docs/current-state.md`
  header bump + shipped entry; `docs/ideas/backlog.md` idea captured.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **363 passed** (was 354); `python3 bootstrap.py check
  --strict` — green (the only red before this flip was the designed
  born-red session-gate hold).

⚑ Self-initiated: no — ORDER 014 (control/inbox.md, owner-directed via fleet
manager 2026-07-12).

## 💡 Session idea

**/prompts pinned-registry drift chip** — when the /projects registry
listing is available (same TTL cache, zero extra fetch warm), compare its
directory set against `prompts.SEATS` and render a "pinned list drifted:
+X / −Y" chip on /prompts. Worth having because the page's one honest
weakness is registry drift and the site already fetches the ground truth
elsewhere. Deduped against `docs/ideas/backlog.md` + the queue-state NEXT
list: nothing touches the prompt library. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The /projects dispatch-view session (#158) verified its claim scope before
branching and render-verified escaping via TestClient — both imitated here;
what it missed and this session inherits: the fleet-manager seat list now
lives pinned in TWO app modules (`projects._START_ORDER`, `prompts.SEATS`)
with no shared constant — a future consolidation candidate.
