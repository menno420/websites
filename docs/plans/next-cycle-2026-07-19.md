# Next-cycle plan — 2026-07-19

> Superseded by docs/PROJECT-CLOSEOUT.md (final close, 2026-07-21) — see its Continuation section.

> **Status:** `binding` (planning pass v2)
>
> Basis: fresh-sync recon at HEAD `7dfdca2` (#447), 2026-07-20. All orders
> 001–038 closed; baton armed; 2070 tests green; `bootstrap.py check --strict`
> passing.

## How this was built

Mined the 💡 lines on every `.sessions/` card dated 2026-07-18+, the
`docs/current-state.md` gaps, the launch-console / arcade / review growth
edges, and the kit advisories — each verified against the tree (anything
already shipped or owner-gated is crossed out). The previous plan
(`next-cycle-2026-07-18.md`) is fully executed. Honest sizing: the
seat-buildable frontier is genuinely thin — most product surface is content-
or owner-gated — so this is six quality/consolidation slices, not padded
feature work.

## Executable slices (ordered by value-per-effort)

### 1 · Route `submissions_store` onto the shared `_db._Conn` shim — M

- **What:** migrate `botsite/submissions_store.py` off its inline per-function
  `psycopg.connect` (`:81`, `:121`) onto the `_Conn / _Row / _pg_row_factory`
  plumbing that `botsite/_db.py` now exports and `testing_store.py` already
  consumes.
- **Why now:** #447 extracted the shim but only `testing_store` uses it —
  `submissions_store` still hand-maintains dual-backend SQL (placeholder
  translation, `RETURNING id`, sequence resync). This is the baton's own
  NEXT-2 item; making the shim real removes the second copy before it drifts.
- **Test shape:** extend `botsite/tests` store tests to assert dual-backend
  behaviour-identical after the migration (mirror the `testing_store`
  dual-backend test). Run with `env -u DATABASE_URL`.
- **Gate:** `quality` (born-red card). Behaviour-preserving; CSRF/routes
  untouched.

### 2 · NAV reachability GET guard for `app/` control-plane — S

- **What:** add a `TestClient` GET bucket over `app/` page routes asserting
  non-5xx (documented allowed status set for gated pages), mirroring the
  `PAGES_NOT_IN_NAV` reachability guard the other three services got
  (#416 / #418 / #421).
- **Why now:** `tests/test_nav_manifest.py` asserts only classification, no
  reachability — `app/` is the last service without the GET guard. Explicit
  successor idea in `.sessions/2026-07-18-nav-reachability-guard.md`.
- **Test shape:** the new test; gated pages get a documented `{401,503}`-style
  allowed set like botsite's `/testing/owner`.
- **Gate:** `quality`. Test-only, zero prod risk.

### 3 · askverify probes for the observable-but-unprobed asks — M

- **What:** add read-only probes for (a) Discord-OAuth-configured
  (`/owner/login` → 302 → discord.com) on botsite + dashboard (ASK-0006/0017)
  and (b) the `/submit` live signal (ASK-0004), following the existing
  six-probe contract in `app/askverify.py`.
- **Why now:** ASK-0002 was satisfied by exactly the 302-redirect-target
  signal, yet `askverify.py:412,422` still says "no read-only probe exists" —
  the same probe is observable for the two sibling logins and the submit-live
  signal. Closes genuinely-observable preflight coverage gaps.
- **Test shape:** async probe returning `still-open` / `done-detected` per the
  contract; unit test against a stubbed 302 target.
- **Gate:** `quality`.

### 4 · Committed signal-registry data file — S/M

- **What:** a committed registry (name → baker → raw-URL → consumers) so each
  drift/parity fan-out is a data edit, not a code hunt.
- **Why now:** 💡 of `.sessions/2026-07-18-release-drift-parity.md`; the
  registry-drift guard (`tests/test_registry_drift.py`) proves the join
  pattern — a registry generalises it.
- **Test shape:** schema + consumer-reachability test over the JSON.
- **Gate:** `quality`.

### 5 · Auto-discovering vendored-copy AST core guard — M

- **What:** generalise the per-module drift guards (listfilter, discord_auth
  #445) into one meta-test that discovers same-basename modules across service
  dirs and asserts a declared shared-symbol core stays AST-identical.
- **Why now:** 💡 of `.sessions/2026-07-19-discord-auth-drift-guard.md`, filed
  to `docs/ideas/backlog.md`; each new vendored copy currently needs a
  hand-written guard.
- **Test shape:** the meta-test itself.
- **Gate:** `quality`.

### 6 · `/directory` `.gba` download probe: follow redirects — S

- **What:** add `follow_redirects=True` to the botsite `/directory` `.gba`
  download probe so a 302 → CDN isn't a false-negative.
- **Why now:** 💡 of `.sessions/2026-07-18-arcade-directory-sync.md`; the
  current probe false-negatives redirect-hosted downloads.
- **Test shape:** probe test asserting a 302 → 200 chain counts as reachable.
- **Gate:** `quality`.

## Hygiene (fold into slices, not separate PRs)

- Refresh `docs/current-state.md` header (lags main by ~26 PRs: says #421,
  HEAD is #447) **and** trim toward the orientation-headroom cliff (boot set
  6909/7000 words, 91 headroom; current-state alone 6176).
- Fix the six model-line advisories on three cards (`-botsite-db-shim`,
  `-botsite-discord-oauth`, `-dashboard-discord-oauth`) to the PL-004
  `model · low|medium|high · class` form.
- `python3 bootstrap.py seat-digest` regen (seat-digest-stale advisory).
- Plant `scripts/preflight.py` (config names it; converges local ritual + CI)
  — optional.

## Routed out — not seat-buildable this cycle

- **Owner-gated (`docs/owner/OWNER-ACTIONS.md`):** ASK-0003 (bot control-API
  token + armed service), 0005 (PayPal Payouts creds), 0006/0017 (Discord-login
  vars — the unlock sitting), 0008 (BAKE_PAT durable fix), 0009 (delete
  dashboard `SITE_PASSWORD`), 0012 (Gumroad publish pass), 0013 (photo
  originals), 0014 (Ultramarine title), 0015 (§5 illustration gate), 0016
  (Dutch proofread). Cross-repo: 0010, 0011.
- **Content-gated:** new arcade game cards (only three games; publishing gated
  on 0010/0012); new review editions (authoring work, one edition since 07-11).
- **Hub venue (`.github/workflows/**`):** wire the orphaned
  `review/gen_releases.py` into `review-bake.yml` (never invoked at
  `:108-112`).

## Honest note

The genuinely-valuable seat-buildable list is short: this cycle is
consolidation and guard-hardening, not new product. The product frontier
(arcade catalogue, review editions, tester payouts, Gumroad titles) is gated on
owner actions and content, all tracked in `OWNER-ACTIONS.md`. The single
highest-value unlock remains the Discord-login var sitting (ASK-0006/0017) — an
owner click, not a seat slice.
