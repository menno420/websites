# 2026-07-19 — unify botsite owner login on Discord OAuth (ORDER 037)

> **Status:** `in-progress` — branch `claude/botsite-discord-oauth`; born red.
> Porting the control-plane's proven Discord OAuth owner login
> (`app/discord_auth.py`, PR #426) to botsite's owner surfaces so the fleet
> shares ONE login. Held red by this card until the deliberate LAST code step
> flips it to `complete`.

- **📊 Model:** _(placeholder — filled at flip)_

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

_(placeholder — filled at flip)_

## Verify plan

Four-suite (`tests/ botsite/tests dashboard/tests review/tests`) +
`python3 bootstrap.py check --strict` before flip.

## 💡 Session idea

_(placeholder — filled at flip)_

## ⟲ Previous-session review

_(placeholder — filled at flip)_
