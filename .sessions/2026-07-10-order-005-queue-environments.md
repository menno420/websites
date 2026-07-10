# 2026-07-10 — ORDER 005: /queue + /environments (+ ORDER 007 steps 3–5)

> **Status:** `in-progress`

- **📊 Model:** withheld per session policy
- **Start (UTC):** 2026-07-10T02:27:31Z

**What this session is about to do:** execute ORDER 005 (claimed on main via
fast-lane PR #52 — `claimed-by: 005 gen2-order-005 2026-07-10T02:24Z`): build the
control-plane **`/queue`** (owner to-do surface aggregating every lane's
⚑ needs-owner + `menno420/fleet-manager docs/owner-queue.md`) and
**`/environments`** (render `fleet-manager environments/` with copy-to-clipboard)
pages, both with honest degradation (GITHUB_TOKEN is UNSET in production — the
fleet-manager halves ship degraded by design; the ⚑ is already filed in
`docs/owner/OWNER-ACTIONS.md`). Plus ORDER 007 step 4 (`scripts/env-setup.sh`
wrapper) and step 5 (ledger flips). Tests for degraded + happy paths. Status
`done=` flip follows in a separate control fast-lane PR after live verification.

## What was done

- **`app/owner_queue.py` + `templates/queue.html`** — `/queue`: lane half
  reuses `fleet.overview()` (one fetch+parse path, no drift with `/fleet`);
  manager half fetches `fleet-manager docs/owner-queue.md`. One tolerant
  six-field OWNER-ACTION parser covers both real shapes (the flattened
  one-line string `fleet.parse_status` emits AND raw multiline markdown with
  optional `**label:**` emphasis). Dedup by normalized WHAT/text — merged
  items keep every source badge; newest-first by lane heartbeat, undated
  items last ("date unknown", never invented). Pre-block pointer sentences
  become "lane notes", not asks; an owner-queue.md with NO blocks yields zero
  list items and renders in full below, labeled (found live: flattening the
  whole doc into one giant "ask" was noise).
- **`app/environments.py` + `templates/environments.html` +
  `static/copycode.js`** — `/environments`: contents-API listing of
  `environments/` (one subdir level, `MAX_FILES=40`), README first, markdown
  sanitized via `journal.render_markdown`, scripts/schemas as escaped code
  blocks with a copy-to-clipboard button (vanilla JS, silent no-op without a
  secure-context Clipboard API).
- **Honest degradation on both** (the ORDER 007 dispatch constraint):
  `not-configured` (token unset + fetch failed, names the OWNER-ACTIONS ask)
  / `unavailable` (reason surfaced) / per-lane "asks may be missing" /
  per-file banners; always 200; never fabricated. Live-local exercise with
  `GITHUB_TOKEN` unset: `/queue` 200 rendering REAL fleet asks (the raw host
  serves `owner-queue.md` anonymously — the manager half went live, not
  degraded); `/environments` 200 with the honest not-configured banner (the
  contents API is the walled path here).
- **`scripts/env-setup.sh`** (ORDER 007 step 4) — wrapper `exec`-ing the
  tested `scripts/setup-env.sh`; same always-exit-0 / never-print-secrets
  contract; smoke-run verified (exit 0, full summary printed).
- **Docs**: `docs/site.md` (§3b/§3c + routes table + `GITHUB_TOKEN` env-var
  note), `docs/decisions.md` [D-0027], `docs/current-state.md` (shipped entry
  + Next-steps handover note), queue-state ledger item 1 → DONE.
- **Nav**: `owner queue` + `environments` links in `base.html`; neither page
  auto-refreshes (D-0023 scope kept). Tests 125 → 139 (all suites).

## 💡 Session idea

**`/queue.json` + a manager round-trip check** — a JSON variant of the owner
queue so the *manager/coordinator can machine-verify that an ask it filed
actually surfaces* on the owner's single to-do page (write ask → poll
`/queue.json` → confirm WHAT appears). Today the six-field format is parsed
best-effort; a format drift in a lane's status file silently drops an ask
with no one noticing — the round-trip closes that loop, and the JSON is ~10
lines on top of the existing `overview()` dict (body_html stripped, like
`/fleet.json`). Worth having because /queue is now the surface the owner is
told to trust; a trusted surface needs a way to prove it isn't silently
lossy. Deduped against `docs/ideas/` (README + atom-feed [done] + per-repo
filter + scheduled-healthcheck) — no overlap.

## ⟲ Previous-session review

Previous session: `.sessions/2026-07-10-gen2-walking-skeleton.md` (PR #51).
Its best output wasn't the skeleton — it was the off-repo orientation dossier:
this session needed near-zero rediscovery (claim mechanics, landing sequence,
test counts, service URLs all held true first try), which is exactly what a
handoff artifact should buy. One genuine miss: the dossier stated fleet-manager
is "likely PRIVATE" and the token the only path — an *inference* formatted like
a verified wall. This session found the raw host serves `docs/owner-queue.md`
anonymously, so the manager half of `/queue` runs live even tokenless; had the
build trusted the stated wall (e.g. skipped the fetch entirely when the token
is unset), it would have shipped needlessly degraded. Concrete workflow
improvement: handoff/capability notes should tag claims **VERIFIED** (with the
captured evidence) vs **INFERRED** — the same discovery-rule bar
`docs/CAPABILITIES.md` already sets for walls; the degraded-state logic here
deliberately keys off the *actual fetch result*, not the assumption.

- **End (UTC):** [[fill-at-flip]]
