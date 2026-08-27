# 2026-08-27 — make the control plane the estate review surface

> **Status:** `complete` — PR #521 · branch
> `codex/control-plane-estate-review`.

- **📊 Model:** GPT-5 · high · feature build
- **📍 Venue:** chatgpt-work

**What this session was about:** Owner-directed execution of the control-plane
legibility loop, with the live direction “Improve the control-plane website
first” superseding the older packet order. Build the useful `/repos` catalogue
and repository review pages first, retire the seat-era `/fleet` and `/projects`
representations, then connect owner comments to Fleet Manager's durable records
without making `websites` another truth store.

## What was done

- Made `/repos` the canonical owner-facing software-estate catalogue and
  added validated `/repos/{name}` review pages with concise situation,
  routed activity, focused source pointers, field-level provenance, and the
  exact honest fallback when no current next thread is established.
- Added a bounded public Fleet Manager/member-repository reader and stable
  estate domain/service layer. Overview performs two public Fleet Manager
  reads plus one bounded public GitHub listing; detail alone reads the selected
  repository's routed/focused files with concurrency capped at three.
- Made retrieval time and fact time separate, including live/measured/last
  verified/stale/unknown/unavailable states. A live `archived=true` may
  override an old row; an `archived=false` check never makes dated ACTIVE
  wording live.
- Split anonymous and authenticated GitHub cache identities, prohibited
  authenticated fallback for estate reads, and coalesced identical misses.
  Private/unavailable member contents are not projected.
- Retired the competing HTML estate answers: `/fleet`, `/projects`, and
  `/freshness` redirect to `/repos`. Useful lane/dispatch diagnostics
  remain at `/lanes`, `/lane-freshness`, and `/dispatch`; the
  existing JSON compatibility contracts remain unchanged.
- Closed an independent adversarial review before the gate flip. Its fixes
  cover Fleet Manager `read first` routes, narrative archive false
  positives, current in-flight visibility, parse-validity degradation,
  verification floors, per-fact provenance, non-main default branches,
  exactly-full GitHub listings, unknown unindexed purpose, and console-route
  reachability/counts.
- Verification: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` → **2324 passed**; focused post-review estate suite →
  **154 passed**; `git diff --check` clean; `python3 bootstrap.py check
  --strict` → **all checks passed** after the deliberate final status flip.
- Kept the durable comment loop out of this PR by ownership: Fleet Manager's
  storage/index/consume contract lands separately before a follow-on websites
  writeback change can depend on it.

⚑ Self-initiated: no — direct owner implementation request, routed through
Fleet Manager and the live `websites` working agreement.

## 💡 Session idea

**Expose disagreements as review objects** — when two authoritative-looking
sources conflict, render the contradiction as an attention item with both
provenances instead of silently picking one. Worth having because the owner can
correct drift at the exact point it becomes visible. Deduplication and backlog
disposition: **built here** through normalized contradiction warnings,
attention states, and retained raw wording/provenance; recorded in D-0038, so
no separate backlog item was opened.

## ⟲ Previous-session review

The Railway-hardening session left the deployed sites healthy and the full gate
green; it did not address the still-seat-era estate navigation, which is the
explicit subject of this session.
