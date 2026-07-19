# 2026-07-19 — port Discord OAuth to dashboard's admin surface (ORDER 038)

> **Status:** `in-progress` — branch `claude/dashboard-discord-oauth`;
> porting the proven Discord OAuth owner login
> (`app/discord_auth.py` #426, `botsite/discord_auth.py` ORDER 037 / #442) to
> dashboard's admin surface (`dashboard/discord_auth.py` + `/admin/login` +
> `/admin/auth/callback`) so the fleet shares ONE login. Discord-ONLY (no
> `SITE_PASSWORD` fallback — dashboard never had one). Born red; flips to
> `complete` as the deliberate LAST code step so merge-on-green lands the PR.

- **📊 Model:** _placeholder — fill at flip._

**What this session is about:** ORDER 038. The owner wants ONE Discord login
across the whole fleet (live, 2026-07-19 ~09:30Z: "Can't we just use te discord
login for everything?"). The control-plane proved it E2E (#426) and botsite
ported it (ORDER 037 / #442); dashboard's admin surface is still only a
Discord-OAuth *display stub* — `dashboard/templates/admin_login.html` renders a
"not configured, never will be" page and `dashboard/control_plane.py` carries an
`ANONYMOUS_ACTOR` placeholder with no working authorization flow behind it. This
session ports the same flow into `dashboard/discord_auth.py` (its own callback +
signed session cookie, never a cross-service import), mounts it at `/admin/login`
+ `/admin/auth/callback` (replacing the stub route + template), and gates the
dry-run `/admin` control actions (preview/confirm) fail-closed behind the owner
session while the `/admin` read views stay public — mirroring botsite's shape.
Discord-ONLY: dashboard has never had a `SITE_PASSWORD` gate, so no HTTP-Basic
fallback is added. When signed in the actor is the real owner id;
`ANONYMOUS_ACTOR` is used only when there is no valid session.

Work-ladder rung: order — ORDER 038 (continuing the owner's live direction).

⚑ Self-initiated: no — ORDER 038 on a coordinator directive continuing a live
owner direction.

## Plan

- Port `app/discord_auth.py` / `botsite/discord_auth.py` →
  `dashboard/discord_auth.py` (own callback, own signed session cookie, same
  authorization-code flow; reuse the same SuperBot Discord app + the same four
  `DISCORD_*`/`OWNER_*` env var names + optional `DISCORD_REDIRECT_URI`).
- Mount the router at `/admin/login` + `/admin/auth/callback`; replace the
  existing "not configured" `/admin/login` stub route + `admin_login.html` copy;
  success redirects to `/admin`.
- Gate the dry-run `/admin` control actions (`POST /admin/actions/preview` +
  `/admin/actions/confirm`) fail-closed behind the owner session (503 when OAuth
  unconfigured); keep the `/admin` read views public.
- Make the actor real when signed in; `ANONYMOUS_ACTOR` only when no valid
  session.
- Tests: cover the login flow, the fail-closed gate, and the actor identity —
  without live Discord.
- Docs: add/update the dashboard Discord-vars ask (redirect URI + the four env
  vars on the dashboard service; ASK-0009 note that `SITE_PASSWORD` is unused).

## Verify plan

Four-suite (`tests/ botsite/tests dashboard/tests review/tests`) +
`python3 bootstrap.py check --strict` before flip.

## 💡 Session idea

_placeholder — fill at flip._

## ⟲ Previous-session review

_placeholder — fill at flip._
