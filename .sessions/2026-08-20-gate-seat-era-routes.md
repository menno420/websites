# 2026-08-20 — gate the seat-era heavy routes behind the owner overlay (crawler DoS fix)

> **Status:** `complete` — branch `claude/gate-seat-era-routes`, PR #508. This
> flip releases the born-red hold; the reviewed head is `74c4015` and the flip
> commit changes only this card's close-out text (the session-close exemption,
> taken and named).

- **📊 Model:** fable-5 · high · mechanical refactor

## previous-session review

The previous card (2026-08-13, kit v1.21.0 hop) closed clean: vendored dist +
pin + heartbeat all v1.21.0, rollback banked, zero workflow changes. Nothing it
recorded contradicts the tree this session found.

## Why (measured, 2026-08-20 — fleet-manager worklist `docs/planning/2026-08-20-railway-keep-bot-only-worklist.md`)

- Meta-range crawlers (57.141.x, spoofed desktop UAs) are enumerating
  control-plane's faceted seat-era `/orders` page: 5,001 requests/40 min
  measured this morning (fm worklist § 1); by this session's own sample the
  service is fully saturated — 17:30–18:00Z httpLogs: 2,001 requests (cap),
  1,997 Meta-range, 1,947 on `/orders`, **every one HTTP 499** (client gave up
  before the render finished), and external `GET /healthz` timed out 3 × 30 s.
  robots.txt (websites #501) is measured ignored: 0 fetches in 3,001 requests.
- Size audit (this session, local render against live data): `/orders` 608 KB ·
  `/orders.json` 775 KB · `/prompts` 513 KB — the three seat-era RECORD-tier
  surfaces ≥ 500 KB. Next-heaviest are live-tier (`/fleet` 211 KB, `/queue`
  150 KB) and stay public; everything else ≤ 65 KB.
- Decided upstream (do not re-litigate): route-scoped gate, NEVER an IP-range
  403 — `facebookexternalhit` shares Meta's ranges and powers link unfurls.

## Scope

Gate exactly `/orders`, `/orders.json`, `/prompts` in place behind the existing
[D-0012] owner overlay (`require_owner` — Basic `SITE_PASSWORD` or the Discord
owner session; both verified configured on the live service). Public response
becomes the tiny 401 challenge; the URLs, nav item hrefs, and the owner's deep
links stay. `/`, page roots, and every other public route unchanged.
`/prompts/history/{seat}` (17 KB each, bounded) stays public.

## Shipped

- `app/owner.py` `require_owner_page` — the [D-0012] gate as a distinct named
  dependency; `app/main.py` applies it to `/orders`, `/orders.json`,
  `/prompts` (gate runs before the route body — an anonymous hit never costs
  a render).
- `app/nav.py`: 🔒 labels + item-level `"gated": True`;
  `nav.gated_in_place_hrefs()` as the single registry the walks read.
- `scripts/smoke_crawl.py` exact-path skips; clarity walk authenticates the
  set + pins anonymous 401 < 2 KB; category-IA/nav-manifest reachability
  allow the documented gate statuses; `test_owner_security.py` gains
  real-dependency gate tests; ten content modules opt into the scoped
  `ungate_seat_era_pages` fixture (conftest).
- Docs: `site.md` route table + auth section (decision referenced by name —
  the id stamps at one home), `current-state.md` gated-corner lines +
  shipped entry, `decisions.md` **[D-0036]**.

## Verify

- Control-plane suite **1074 passed** (from 1022 + 42 gate-shaped failures).
  dashboard 130 · review 276 passed. botsite's 171 local failures reproduce
  **identically on the clean tree** — venv-vs-CI dependency drift,
  pre-existing (CI's pinned env merged today's #507 bake green on the same
  botsite tree; CI is the authority).
- `python3 bootstrap.py check --strict --require-session-log --session-log
  <this card>` → exit 1 on exactly the designed born-red hold
  (`HOLD (by design)`), nothing else; flips green with this commit.
- Codex: reviewed the exact head `74c4015` — **0 findings, 0 inline
  comments** (*"Didn't find any major issues"*), verified via
  `/pulls/508/comments` (not the summary alone).
- Post-merge external probes (recorded in the fm execution records): healthz
  < 1 s repeatedly; anonymous `/orders` tiny 401; owner Basic login serves
  the page at the same URL.

## Session idea

- 💡 `/queue` (150 KB) is the service's OTHER faceted page — if the crawler
  fleet migrates there once `/orders` closes, the same one-line
  `require_owner_page` gate applies; it is live-tier (the owner's public
  queue view), so that widening is an owner call, deliberately not taken
  here. Flagged in the fm records for this execution.
