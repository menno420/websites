# 2026-07-18 — Discord OAuth owner login gate on the control-plane (ASK-0001)

> **Status:** `in-progress` — branch `claude/discord-oauth-owner-gate`; the
> NON-gated half of the ASK-0001 / Q-0004 decision: a Discord OAuth
> authorization-code **login flow** on the control-plane (`app/`) owner
> surface, fail-closed, test-covered without live Discord. A new
> `app/discord_auth.py` carries `oauth_configured()`, stdlib-only signed
> session-cookie helpers (`make_session`/`verify_session`, HMAC-SHA256 over
> `discord_id|issued_at|expiry`), a CSRF `state` floor, an
> `owner_session_id(request)` reader, and an APIRouter with
> `GET /owner/login`, `GET /owner/auth/callback`, `POST /owner/logout`. The
> network calls (`exchange_code`/`fetch_user`) are factored into overridable
> seams so tests monkeypatch them without live Discord. `require_owner` in
> `app/owner.py` now accepts EITHER a valid Discord owner session cookie OR
> the existing HTTP-Basic `SITE_PASSWORD` — fail-closed: nothing configured →
> 503 naming the opening owner action, bad creds → 401. Env-unset →
> `/owner/login` renders an honest "not configured" page naming ASK-0002 +
> ASK-0003. Armed bot-control write path stays stubbed (ASK-0003, owner-gated).
> Born red; flips to `complete` only once the work is confirmed — deliberately
> held in-progress this session.

- **📊 Model:** high effort · worker session (coordinator-dispatched)

**What this session is about:** the owner delegated the ASK-0001 / Q-0004
decision to this seat: live bot control lives on the websites CONTROL-PLANE
(`app/`) owner surface, gated by Discord OAuth that REUSES the existing
fleet-side "SuperBot" Discord application; the dashboard `/admin` dry-run panel
stays the safe preview tier; the scoped bot control-API token + a separate
armed Railway service (ASK-0003) remain the armed-execution architecture,
stubbed until owner-gated creds exist. This session builds ONLY the non-gated
login half — the OAuth login flow, its signed session, the CSRF floor, and the
`require_owner` gate wiring — plus the decision record (ORDER 035) and the
OWNER-ACTIONS narrowing. It does NOT build the armed bot-control write path.

⚑ Self-initiated: no — coordinator-dispatched (ASK-0001 decision seat).

## Close-out

Pending — the card is held `in-progress` this session by design (the born-red
`quality` hold stays red until the work is confirmed downstream).
