# 2026-07-09 — auto-refresh the live-monitoring pages (/fleet + board /)

> **Status:** `complete` — shipped as PR #37 (`claude/monitoring-autorefresh`, squash-merged).

- **📊 Model:** Opus 4.8 · worker · monitoring-autorefresh

**What this session did:** self-directed improvement on the control-plane site.
(A) Audited the `quality` CI job — confirmed it runs the FULL suite on every
normal PR (the ~17s run is genuinely fast, not a short-circuit). (B) Added an
unobtrusive client-side **auto-refresh** to the two live-monitoring surfaces —
the board `/` and `/fleet` — so the owner's control glance stays current without
a manual reload; content/journal pages stay static.

## TASK A — quality.yml audit (NO change needed)

Verified against real run logs (GitHub MCP) that the required `quality` gate runs
the full suite on every normal PR:

- **Normal PR run 29032059374** (job 86167157380, 17s total) executed **every**
  step: control-fast-lane (`control_only=false` → proceed) → setup Python 3.12 →
  install all three services' deps (≈7s) → `substrate check --strict
  --require-session-log` → the ambient-Railway-ID guard → **`pytest tests/
  botsite/tests dashboard/tests`**, whose log reads `117 passed, 1 warning in
  3.61s`. So ~17s = fast install + a small fast suite, **not** a skipped suite.
- The prior ~17s **failed** run 29031306806 was the **born-red session gate**
  failing at the substrate-check step on an in-progress card (before pytest),
  not a short-circuit.
- The ONLY short-circuit in `quality.yml` is the intentional, documented **KL-8
  control fast lane**: a `control/**`-only diff (a status heartbeat) short-circuits
  the job green in-job — deliberately NOT a `paths-ignore` (a required context
  must always report, or it jams the merge). A non-`control/`-only diff (like this
  PR) always runs the full gate.

Conclusion: no fix required; the full gate is genuinely enforced.

## TASK B — auto-refresh /fleet + board / (what was built)

- **`app/static/autorefresh.js`** (new; vanilla JS, no dependency) — soft
  in-place refresh: every `AUTOREFRESH_SECONDS` it re-fetches the CURRENT page
  and swaps only the `#live-content` region into the DOM (server stays the one
  renderer → always matches a hard reload; no reload flash, no scroll jump). The
  fetch omits `?refresh=1`, so it rides the 180s TTL cache and never hammers the
  GitHub API. Pauses while the tab is hidden or a fetch is in flight; a transient
  error keeps prior content and retries next tick.
- **`app/templates/_autorefresh.html`** (new) — the indicator, included only on
  the two monitoring templates, placed OUTSIDE `#live-content` so its toggle
  survives each swap: `auto-refreshing every Ns · last updated <time>` + a
  **pause/resume** button (persisted in `localStorage`, `aria-pressed`).
- **`app/config.py`** — `AUTOREFRESH_SECONDS` (env-tunable, default **45s**).
- **`app/main.py`** — `StaticFiles` mount at `/static`; `autorefresh_seconds`
  threaded into the board + fleet contexts.
- **`app/templates/base.html`** — indicator CSS (pulse dot honors
  `prefers-reduced-motion`; `.is-paused` greys the dot) + a `scripts` block.
- **`app/templates/{board,fleet}.html`** — include the indicator, wrap content in
  `#live-content`, load the script. Content/journal pages are untouched (static).
- **Tests (`tests/test_app.py`) +4** (117 → 121): board + fleet each carry the
  indicator markup + poll script + interval constant + pause control; content
  pages (`/journal`, `/journal/superbot`, `/activity`, `/ideas`) carry none;
  `/static/autorefresh.js` serves 200 as JavaScript.

Interval: 45s (config constant). Pages covered: `/` and `/fleet` only. Pause
control: yes (persisted toggle). Mechanism: HTML-over-the-wire `#live-content`
swap (chosen over a JSON re-render — would duplicate template logic — and over a
`meta refresh`/full reload — flashes + loses scroll).

## Verification

- `python3 -m pytest tests/ botsite/tests dashboard/tests` — **121 passed**.
- `python3 bootstrap.py check --strict` — green (only the born-red card was
  flagged while in-progress; nothing else).
- Local live smoke (uvicorn): board `/` 200 and `/fleet` 200 both serve the
  `class="autorefresh"` indicator + `data-autorefresh="45"` + `id="live-content"`
  + `/static/autorefresh.js` + `id="ar-toggle"` + `auto-refreshing every 45s`;
  `/journal` served NONE of the indicator/wrapper/script markers (only the shared
  CSS class definition, which is inert); `/static/autorefresh.js` 200
  `text/javascript`; `/version` 200.
- CI: the born-red push failed at the substrate-check step (gate working); the
  final push (complete card) runs the full gate green, its pytest log the proof
  the full suite runs on this PR.

## Decisions made this session

- **Soft `#live-content` swap** over JSON-render (duplicates server logic) or
  full reload (flash/scroll loss) — flash-free AND always-correct, server stays
  the single renderer. Recorded as [D-0023].
- **Scope strictly the two monitoring screens** — explicit ask not to
  auto-refresh the whole site; content/journal stay static.
- **Keep the fetch cache-friendly** (no `?refresh=1`) so N viewers polling every
  45s cost nothing beyond re-rendering cached data (cache refreshes at its own
  180s TTL).
- **No CI change** — the quality gate already enforces the full suite; the ~17s
  was fast, not skipped.

## 💡 Session idea

The auto-refresh indicator could surface a **"stale data" signal** when the
server's cached `fetched_at` for the board/fleet data is materially older than a
few TTLs (e.g. the GitHub token is degraded and every cell is `unknown`): badge
the indicator amber ("data N min old — upstream fetch failing") instead of
silently showing an all-`unknown` board that *looks* live because the timestamp
keeps ticking. The refresh loop already re-fetches the rendered page; exposing the
oldest underlying `fetched_at` (already in every cell payload) into the indicator
turns "the page auto-updated" into "the page auto-updated AND the data behind it
is fresh" — the same honesty posture the board already holds per-cell, lifted to
the page-level freshness the auto-refresh implies.

## ⟲ Previous-session review

Previous session (PR #36, fleet-manifest-live) did a genuinely clean job: it
removed the hand-kept-lane-set drift by parsing the manifest live AND kept an
honest labeled fallback, and — to its credit — its own `⟲` review already named
the exact meta-improvement ("a self-flagged ⚑ that's contained + reversible is a
ready-to-build idea, route it to `docs/ideas/` not the owner"). What it could
have done better: it fixed the websites dogfood `control/status.md` timestamp to
full ISO to make its `/fleet` row show a real age — but the board `/` and `/fleet`
it was polishing were still **static snapshots** that go stale the moment you look
away, which is the gap this session closes. **System improvement it surfaces:**
the previous session's own routing idea is real and unimplemented — the workflow
would benefit from a lightweight convention (even a checklist line) that a `⚑
needs-owner` entry describing a *contained, reversible, test-coverable* follow-up
should be MIRRORED into `docs/ideas/` as a pre-approved build candidate, so the
next self-directed session finds it as buildable work instead of re-deriving it
(this session re-derived "these pages should auto-refresh" from scratch rather
than picking it off a backlog — a small `docs/ideas/` for the websites repo would
have made it a pick-off-the-shelf).

## Documentation audit

- `docs/decisions.md` — `[D-0023]` added (next free D-number; D-0022 was last),
  incl. the quality.yml audit finding.
- `docs/site.md` — new §§ "Live-monitoring auto-refresh" + `/static/*` route row
  + `AUTOREFRESH_SECONDS` env var.
- `docs/current-state.md` — Recently-shipped entry + status-line date updated.
- `control/status.md` — overwritten LAST (heartbeat), notes the quality.yml
  finding + this PR; orders 001/002 unchanged (done).
- No owner decision to route (self-directed; no new order). No new doc needs a
  reachability link beyond the D-0023 / site.md cross-refs above.
