# 2026-08-20 — gate the seat-era heavy routes behind the owner overlay (crawler DoS fix)

> **Status:** `in-progress` — branch `claude/gate-seat-era-routes`. Born red;
> flips `complete` only after review at the exact head and the landing checks.

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

- (filled at close)

## Verify

- (filled at close: pytest suites, `bootstrap.py check --strict` real exit
  code, post-deploy external probes — healthz < 1 s, `/orders` public response
  tiny)

## Session idea

- 💡 `/queue` (150 KB) is the service's OTHER faceted page — if the crawler
  fleet migrates there once `/orders` closes, the same one-line
  `require_owner_page` gate applies; it is live-tier (the owner's public
  queue view), so that widening is an owner call, deliberately not taken
  here. Flagged in the fm records for this execution.
