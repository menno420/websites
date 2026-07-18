# 2026-07-18 — Discord OAuth owner login gate on the control-plane (ASK-0001)

> **Status:** `complete` — branch `claude/discord-oauth-owner-gate`; the
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
> Born red by design; branch brought up to date with `origin/main` (HEAD
> `c27d01c`) and flipped `complete` on green — auto-merge (squash) armed to land
> PR #426 once `quality` reports.

- **📊 Model:** Opus 4.8 (family) · high · feature build

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

**Evidence:**

- feature files touched this branch (`07b4bb9..ebdeca1`):
  - `app/discord_auth.py` — new: `oauth_configured()`, stdlib-only signed
    session cookie (`make_session`/`verify_session`, HMAC-SHA256 over
    `discord_id|issued_at|expiry`), CSRF `state` floor, `owner_session_id`
    reader, and the `GET /owner/login` · `GET /owner/auth/callback` ·
    `POST /owner/logout` router. `exchange_code`/`fetch_user` are overridable
    seams so tests run without live Discord.
  - `app/templates/owner_login.html` — new: the login / not-configured page;
    when env is unset it renders an honest "not configured" state naming the
    opening owner actions (ASK-0002 + ASK-0003) rather than a dead button.
  - `app/owner.py` — `require_owner` now accepts a valid Discord owner session
    cookie OR the existing HTTP-Basic `SITE_PASSWORD`; fail-closed (nothing
    configured → 503 naming the owner action; bad creds → 401).
  - `app/main.py` — mounts the `discord_auth` router on the control-plane app.
  - `app/railway.py`, `app/data/environments.json`, `app/data/env_coderefs.json`,
    `app/askverify.py` — env/coderef surfacing of the new `DISCORD_*` OAuth vars
    so the environments hub and askverify probes know them.
  - `tests/test_discord_auth.py` — new: 19 tests covering the cookie
    sign/verify round-trip, tampered-cookie fail-closed, CSRF state, the
    login/callback/logout routes, and the not-configured fail-closed path.
    `tests/test_clarity_structure.py` + `tests/test_hostile_env_smoke.py`
    updated for the new module/env.
  - `control/inbox.md` — ORDER 035 (the ASK-0001 / Q-0004 decision record).
  - `docs/owner/OWNER-ACTIONS.md` — ASK-0001 → DECIDED (Decided row P);
    ASK-0002 narrowed to the SuperBot-app redirect URI + control-plane env;
    ASK-0003 unblocked but owner-gated.
  - `control/claims/discord-oauth-owner-gate.md` — this branch's in-flight claim.
- integration this session: merged current `origin/main` (`c27d01c`, next-cycle
  planning #423 + doc hygiene) into the branch — clean, no conflicts — which
  deleted the orphaned `control/claims/nav-reachability-guard.md` (PR #421
  merged). Rewrote `control/status.md` (the coordinator heartbeat) to current
  reality and flipped this card to `complete`.
- verify: `python3 -m pytest tests/ botsite/tests dashboard/tests review/tests -q`
  — **1947 passed**, 0 failed; `python3 bootstrap.py check --strict` green, the
  only red having been the DESIGNED born-red hold on this card, released at this
  flip.
- git: branch `claude/discord-oauth-owner-gate`; feature commits `bd8d78b`
  (born-red card + claim) and `ebdeca1` (the OAuth login flow), plus the
  `origin/main` merge commit and this integration + flip commit.

**Judgment:**

- Decisions made: (1) ASK-0001 / Q-0004 — live bot control lives on the websites
  CONTROL-PLANE (`app/`) owner surface, gated by Discord OAuth **reusing** the
  existing SuperBot Discord app; `/admin` dry-run stays the preview tier; the
  scoped control-API token + a separate armed Railway service (ASK-0003) hold
  the armed-write path, stubbed until owner-gated creds exist. (2) Built only the
  non-gated login half this session; the armed path stays stubbed — fail-closed
  so an env-unset deploy is locked, never an open door. (3) Brought the branch up
  to date with `origin/main` so the orphaned nav-reachability-guard claim (its
  PR #421 merged) is removed, clearing the one `quality` failure the card flip
  would otherwise expose.
- Next session should know: the login flow is live in code but **fail-closed
  until the owner completes ASK-0002** — add a redirect URI to the existing
  SuperBot Discord app and paste `DISCORD_CLIENT_ID`/`_SECRET`/owner-id/session
  secret onto the control-plane Railway env. ASK-0003 (scoped control-API token
  + separate armed Railway service) is the remaining gate before the armed
  bot-control write path can be built on top of this gate.

## 💡 Session idea

**Wire the OAuth `guilds` scope into a per-guild owner permission check for the
future armed panel.** The login flow currently authorizes only `identify`,
matching the owner solely by Discord user id. When ASK-0003 lands the armed
control surface, the same OAuth app already grants a `guilds` scope (the
SuperBot dashboard recording shows it listing administered guilds); requesting
it here and caching the owner's administered-guild set would let the armed panel
scope each write to a guild the caller actually administers — a cheap, additive
hardening (identify-only login keeps working) that turns the single-owner gate
into a per-guild permission check before any armed write path exists to abuse.
A smaller companion: a `/owner` login-status indicator (green "signed in as …"
vs "not configured — ASK-0002") so the owner can see the gate's live state
without reading env.

## ⟲ Previous-session review

`.sessions/2026-07-18-release-drift-banner.md` (ORDER 033) closed cleanly and
did the right thing pinning its heartbeat `landing:` line to the classifiable
`pushed-unmerged <branch>` form after discovering free prose made
`fleet.classify_landing` misread it as `unknown` and redden
`test_own_heartbeat` — a good instinct to make the heartbeat grammar
self-enforcing rather than trusting prose. Carrying that forward, this session
wrote `control/status.md`'s `orders:`/`landing:`/`routine:` lines against the
`app.fleet` parsers directly and ran `test_own_heartbeat.py` before committing,
so the heartbeat is machine-clean by construction, not by luck. Workflow note:
the auto-drafted close-out's file-count evidence ("97 code / 258 sessions
touched") was branch-wide diff noise, not this feature's footprint — worth the
adopting session always replacing those counts with the real
`git diff --name-only <base>..<head>` feature list, as done here.
