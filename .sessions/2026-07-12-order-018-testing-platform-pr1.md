# 2026-07-12 — ORDER 018 PR1: tester-recruitment `/testing` section on botsite

> **Status:** `complete` — PR `claude/order-018-testing-platform-v1`, parks
> READY + green for the owner (build worker; merge is deliberately not this
> session's call).

- **📊 Model:** Claude Fable 5 · build worker · order

**What this session was about:** Rung: order — ORDER 018 (tester-recruitment
site), captured in `control/inbox.md` on PR #173's branch
`claude/order-018-tester-recruitment` @ `704221d` (owner idea verbatim,
provenance "owner live in the coordinator session 2026-07-12"), routed to this
build worker by the websites coordinator. Owner follow-ups relayed live
2026-07-12: (1) can payouts be automatic once steps are confirmed? → the
dry-run payout module; (2) PayPal Payouts is the CONFIRMED v1 rail → the
definitive setup ask + PayPal named in site copy. Scope: PR1 — a `/testing`
section on botsite (botsite deploys today; a new Railway service would need
an owner click).

## What was done

- **Task catalog** `botsite/testing_tasks.json` — 8 real tasks: 3 open
  site-reviews (botsite / dashboard / control-plane `/projects`, live URLs),
  the review-site review `coming-soon` (URL unverified until the Railway
  service exists — honest note), 3 game-tests `coming-soon` ("activates when
  the game deploys" — Lumen Drift / mineverse / games-web are not deployed),
  1 guided-walkthrough `coming-soon` (needs step scripts + PR2 reviewer).
- **Storage** `botsite/testing_store.py` — stdlib sqlite3 (env
  `TESTING_DB_PATH`, default gitignored `botsite/testing.sqlite3`); tables
  claims / submissions / payout_ledger. ⚠ LOUDLY flagged ephemeral (Railway
  disk — redeploy wipes it) in the module docstring, the owner-queue banner,
  and the PR; mitigation shipped: owner-auth `/testing/owner/export.json`
  full-DB export. Postgres auto-switch deferred (no DATABASE_URL exists to
  test against) — extends the standing Postgres ask, noted in OWNER-ACTIONS.
- **Public flow** `botsite/testing.py` + 4 templates — landing (honest
  program explanation, task cards, visible $200 open-bounty cap), task
  detail + claim form (name/email/optional PayPal email = payout address; no
  mail provider so NO magic-code email — private `secrets.token_urlsafe`
  link shown once, said plainly), per-type structured submission forms
  (site-review/game-test questionnaires, walkthrough placeholder) + findings;
  submitted page says review is manual + AI exit-review lands in PR2.
  Screenshot upload deliberately deferred to PR2 (first new dependency —
  multipart — for the service; the form says so).
- **Owner queue** — HTTP Basic vs `SITE_PASSWORD`, constant-time, fail-closed
  (unset → 503, bad → 401; `app/owner.py` pattern re-implemented in botsite,
  never imported); queue shows claims/submissions/ledger totals/payout-config
  state + ephemerality banner; approve → OWED ledger row, reject → frees the
  slot, mark-paid → PAID row.
- **Payouts** `botsite/testing_payouts.py` — adapter interface +
  `PayPalPayoutsAdapter` (env NAMES only: `PAYPAL_CLIENT_ID` /
  `PAYPAL_CLIENT_SECRET`); v1 DRY-RUN ONLY: `DRY_RUN=True` constant, no HTTP
  client imported (test-pinned), kill switch `TESTING_AUTOPAY_ENABLED`
  defaults OFF, hard caps ($20/payout, $60/day, $300/month env-tunable, one
  payout per email per task), eligibility gate coded so v1 ALWAYS queues for
  owner one-click (AI review is PR2). No real money can move.
- **Anti-abuse** on every state-changing route — same-origin (Origin →
  Referer fallback, both absent → 403) + sliding-window rate limit
  (10/60s per path+IP, 429 + Retry-After, test reset hook); PR #159's
  pattern re-implemented independently in botsite (app/ untouched).
- **Owner asks** appended to `docs/owner/OWNER-ACTIONS.md` (six-field format
  + RISK lines): definitive PayPal Payouts setup (rail confirmed — exact
  console steps, business-account gate warning, names-only env vars),
  `SITE_PASSWORD` on botsite; durable-storage side-note extending (not
  duplicating) the standing Postgres ask; Decided row F records the rail
  confirmation. `control/` untouched.
- **Tests** `botsite/tests/test_testing.py` — 33 new (61 botsite total):
  landing/detail/nav, claim (token, origin 403s, dup-email, slot exhaustion
  + auto-close, bounty cap), submission (store, lock, empty-reject, 404s),
  rate-limit 429, owner 503/401, approve→OWED, mark-paid, reject-frees-slot,
  export, payout dry-run safety (creds+kill-switch-on still cannot pay; no
  HTTP lib in module source).
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 389 passed; `python3 bootstrap.py check --strict` —
  green (sole holds during the session were the designed born-red card
  states; final run on the flipped card: PASS).

⚑ Self-initiated: no — coordinator-routed ORDER 018 (PR1 slice as briefed;
PayPal-rail update folded in live).

## 💡 Session idea

**Tester-task URL liveness guard** — every open task points a paying tester
at a `product_url`; a healthcheck/bake pass that verifies each open task's
URL answers 200 (and flips dead ones to an honest hold, or auto-opens the
seeded coming-soon game tasks the day their games deploy) keeps the catalog
honest by default. Worth having because the program's whole pitch is "real
products, honestly described" — a dead link is the fastest credibility
killer. Deduped against `docs/ideas/backlog.md` + queue-state NEXT: fleet
healthcheck ideas exist, nothing touches the testing catalog. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

The v1.14.0 kit-upgrade session (#171) did well: its chain-of-custody sha
habit and naming every diverged doc on the card made its state instantly
auditable. What it missed: it surfaced the new `[owner-action-risk-class]`
advisory but left it floating as "lane-owed" with no owner-doc example to
copy — this session closed that gap in practice by shipping its new
OWNER-ACTIONS asks with RISK lines from birth.
