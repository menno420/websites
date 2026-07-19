# 2026-07-19 — unify botsite owner login on Discord OAuth (ORDER 037)

> **Status:** `complete` — branch `claude/botsite-discord-oauth`, PR #442;
> ported the control-plane's proven Discord OAuth owner login
> (`app/discord_auth.py`, PR #426) to botsite's owner surfaces
> (`botsite/discord_auth.py` + `/owner/login` + `/owner/auth/callback`) so the
> fleet shares ONE login, with `SITE_PASSWORD` kept as an optional fallback.
> Born red; flipped to `complete` as the deliberate LAST code step so
> merge-on-green lands the PR.

- **📊 Model:** Opus 4.8 (family) · effort medium–high · task-class: cross-service feature port + landing

**What this session is about:** ORDER 037. The owner asked (live, 2026-07-19
~09:30Z, verbatim): "Can't we just use te discord login for everything? Or else
you can add a site password". The control-plane already proved a Discord OAuth
owner login E2E (#426, owner-confirmed 08:42Z). This session extends that same
flow to botsite's owner surfaces — the `/testing/owner` review queue and the
`/submit/queue.json` moderation gate — so the owner has one unified login
across the fleet. botsite gets its OWN port (`botsite/discord_auth.py`) with its
own callback, mirroring `app/`'s flow (services share patterns but never import
each other's packages). botsite's `require_owner` accepts EITHER a valid Discord
owner session OR the existing HTTP-Basic `SITE_PASSWORD` — honoring the owner's
explicit either/or, Discord is the unified default and `SITE_PASSWORD` becomes
an optional fallback rather than being removed. Fail-closed when neither is
configured (503 naming the opening owner action). CSRF floor throughout,
test-covered without live Discord.

Work-ladder rung: order — ORDER 037 (fm ORDER 048, reason-forward).

⚑ Self-initiated: no — ORDER 037 on a live owner directive.

## Plan

- Port `app/discord_auth.py` → `botsite/discord_auth.py` (own callback, own
  signed session cookie, same authorization-code flow; reuse the same
  SuperBot Discord app + the same four `DISCORD_*`/`OWNER_*` env var names).
- Wire botsite's `require_owner` to accept EITHER a valid Discord owner session
  OR the existing HTTP-Basic `SITE_PASSWORD`; fail-closed (503) when neither is
  configured.
- Add `botsite/templates/owner_login.html` (the locked/login surface).
- Register the Discord OAuth router in botsite's app.
- Tests: cover the login flow, the either/or gate, and fail-closed — without
  live Discord.
- Docs: update ASK-0006 + add a botsite Discord-vars ask (redirect URI + the
  four env vars on the botsite service).

## What was done

- `botsite/discord_auth.py` (new, ~409 lines) — botsite's own Discord OAuth
  authorization-code owner login, ported from `app/discord_auth.py`: `GET
  /owner/login` (env-unset → honest "not configured" page; configured →
  "Redirecting to Discord to sign in…") and `GET /owner/auth/callback` (state
  CSRF check, token exchange, owner-id allowlist, signed session cookie).
  Reuses the same SuperBot Discord app + the same four `DISCORD_*`/`OWNER_*`
  env var names; own callback and own signed cookie (services share the
  pattern, never import each other's packages).
- `botsite/testing.py` — `require_owner` now accepts EITHER a valid Discord
  owner session OR the existing HTTP-Basic `SITE_PASSWORD`; fail-closed (503)
  when neither is configured, naming the opening owner action. `SITE_PASSWORD`
  is now the optional fallback, not the sole gate.
- `botsite/app.py` — registered the Discord OAuth router.
- `botsite/templates/owner_login.html` (new) — the locked/login surface.
- `botsite/tests/test_discord_auth.py` (new, ~328 tests-lines) — covers the
  login flow, the either/or gate, and fail-closed, all without live Discord;
  `test_nav_completeness.py` + `test_clarity_structure.py` updated for the new
  route/surface.
- `control/inbox.md` — ORDER 037 grammar-completed (priority/do/why/done-when)
  and flipped `status: done`.
- `docs/owner/OWNER-ACTIONS.md` — ASK-0006 reshaped: the primary unlock is now
  the fleet-wide Discord login (redirect URI + the same four env vars);
  `SITE_PASSWORD` demoted to optional fallback.
- `control/claims/botsite-discord-oauth.md` — work claim for this branch,
  deleted in this flip commit so it merges away with the PR.
- Verified before flip: `python3 -m pytest tests/ botsite/tests
  dashboard/tests review/tests -q` all-green; `python3 bootstrap.py check
  --strict` exit 0 (the born-red card hold + ORDER 037 grammar both released).

## Verify plan

Four-suite (`tests/ botsite/tests dashboard/tests review/tests`) +
`python3 bootstrap.py check --strict` before flip.

## 💡 Session idea

**Make dashboard's admin gate real by porting this same flow.** `dashboard/`'s
admin surface is today a Discord-OAuth *display stub* only —
`dashboard/templates/admin_login.html` renders a "not configured" page and
`dashboard/control_plane.py` carries an `ANONYMOUS_ACTOR` placeholder with no
working authorization flow behind it. The exact port done here (own
`discord_auth.py`, own callback, `require_owner` accepting a Discord session)
would turn that stub into a working gate. Natural next ORDER the moment the
owner wants dashboard's admin surface actually gated rather than open/stubbed.

## ⟲ Previous-session review

`.sessions/2026-07-18-wire-bake-pat.md` wired `BAKE_PAT` into
`review-bake.yml`'s landing step (PR #434) — a `.github/workflows` carve-out
the owner had to merge by hand — so the scheduled bake PR is authored by the
PAT identity and auto-merges on a real `pull_request` quality run. A tightly
scoped one-line env change with a load-bearing `|| secrets.GITHUB_TOKEN`
fallback; clean handoff, nothing left in flight for this session to reconcile.
