# 2026-07-09 — ORDER 002 · /fleet page

> **Status:** `complete` — shipped as PR #35 (`claude/order-002-fleet-page`, squash-merged).

- **📊 Model:** Opus 4.8 · worker · fleet-order-002

**What this session did:** executed fleet ORDER 002 (`control/inbox.md`, P1) —
built a public `/fleet` page on the control-plane board that renders **every fleet
lane's `control/status*.md`** as one glanceable heartbeat screen, so the owner can
see which agents are running and how far along they are without opening each session
one by one.

## What was done

- **`app/fleet.py`** — fetches every lane's `control/status*.md` over the shared
  TTL-cached `github.fetch_file`, parses the documented `control/README.md` format
  (`parse_status`: heading → project name; `key: value` fields where a colon
  *inside* a value — ISO timestamp, `#PR — text`, URL — never spuriously starts a
  field; `⚑ needs-owner` + substrate-kit `kit:` line handled; wrapped lines
  appended), classifies `health:` into ok/green · design/red-by-design (purple,
  never counted broken) · broken/red · unknown, badges heartbeat freshness
  **stale** past `FLEET_STALE_HOURS=12` (honest `ok=False` on an unparseable
  timestamp), attaches each repo's **last-commit age** + **open-PR count**
  (`repo_meta`), renders the full status body via `journal.render_markdown`, and
  `overview()` sorts **attention-first** with roll-up summary counts.
- **`app/templates/fleet.html`** — summary header + one card per lane (field table,
  health/stale badges, repo meta, rendered body), each GitHub-deep-linked.
- **`app/config.py`** — `FLEET_LANES` (the 10-lane app-side copy of the manager's
  `superbot/docs/eap/fleet-manifest.md` registry) + `FLEET_STALE_HOURS`.
- **`app/main.py`** — `/fleet` + `/fleet.json` routes (JSON strips the rendered
  body). **`base.html`** — nav link (placed after the board).
- **Tests +8** (103 → 111): documented-format parse incl. value-colons + `⚑`/`kit`;
  health kinds; freshness stale threshold + honest bad-timestamp; lane renders
  parsed health + body + repo meta; 404 = honest absence; non-404 = honest banner;
  overview attention-sort + counts; route degrades no-auth incl. body-stripped JSON.
- Docs: `docs/decisions.md` [D-0021], `docs/site.md` (routes + description),
  `docs/current-state.md`.

## Lane set (decide-and-flag)

Rendered the **10 lanes** ORDER 002 names, cross-checked against the manager's
canonical registry `menno420/superbot` → `docs/eap/fleet-manifest.md`: superbot,
superbot-next, substrate-kit, websites, trading-strategy,
codetool-lab-fable5/opus4.8/sonnet5, and the two superbot-games cohabitation lanes
(`status-mining.md` / `status-exploration.md`). All 10 have real status files
except the bare `superbot` lane (its heartbeat is written to superbot-next — an
honest absence card). **⚑ Flagged to owner:** the canonical source is the manifest;
`config.FLEET_LANES` is a hand-kept copy and must be kept in sync, or `/fleet`
evolved to parse the manifest live (natural follow-up, captured as the session idea).

## ⚑ Self-initiated

None beyond the order — this session executed ORDER 002 as directed. The lane-set
completeness (all 10 vs a minimal 4) is a decide-and-flag call, flagged above.

## 💡 Session idea

`/fleet` could parse `superbot/docs/eap/fleet-manifest.md` **live** to derive the
lane set (repo, model, cadence, last-seen) instead of the hand-kept
`config.FLEET_LANES` — the same "read the canonical file, don't duplicate it" move
the board already makes for required-checks. It closes the sync-drift risk flagged
in D-0021 and would auto-pick-up new lanes as the manager adds Projects. Bounded by
the manifest being a markdown table (needs a small tolerant table parser) — worth an
idea file if the fleet keeps growing.

## ⟲ Previous-session review

The previous session (#33, /activity + /ideas) did the hard part of this one for
free: it built the exact reusable seam — a per-repo, cache-backed, honestly-degrading
fan-out over `github.repo_api` + `render_markdown` — that `/fleet` slotted straight
into, so this order was mostly parsing + presentation. It also did something quietly
excellent: its own `status.md` note **called out** that PR #32's commit title said
"build /fleet page" but its diff only appended the order to `inbox.md` — flagging the
gap for dispatch instead of assuming it was done. That honesty is what let this
session pick up a correctly-scoped order. **One workflow improvement it surfaces:** a
"commit title vs diff" mismatch (a title claiming a feature the diff doesn't contain)
is a recurring drift class in a fleet where orders and code share a repo — a cheap
`quality` check could compare a PR title's claimed artifact against the touched paths
and warn, turning that manual catch into an enforced one (the "enforce, don't exhort"
rule). Left as a flagged idea, not built (out of ORDER 002 scope).
