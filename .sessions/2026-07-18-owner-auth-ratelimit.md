# 2026-07-18 — Rate-limit the /owner GET Basic-auth path (brute-force hardening)

> **Status:** `in-progress` — branch `claude/owner-auth-ratelimit`; the control-plane
> owner gate `app.owner.require_owner` — the dependency on EVERY `/owner` GET — only
> did a constant-time password compare with NO throttle, so failed HTTP-Basic guesses
> against `/owner` were completely unlimited (a brute-force exposure, sharp with a weak
> `SITE_PASSWORD`). The existing in-process sliding-window limiter (`_enforce_rate_limit`)
> and the same-origin CSRF check were wired ONLY into `require_owner_action` (the
> state-changing POSTs). This session throttles FAILED auth attempts on the GET path too:
> after N failures from a client host inside the window, `require_owner` returns HTTP 429
> (with `Retry-After`) instead of an unbounded 401 loop. A SUCCESSFUL auth is never
> throttled, the password check is unchanged, and the POST floor (auth → same-origin →
> rate limit) is untouched.

- **📊 Model:** Claude Opus 4.8 · medium · feature build (failed-auth rate limit on the /owner GET gate)

**What this session is about:** `require_owner` (`app/owner.py` ~line 157) gates every
gated `/owner` GET behind HTTP Basic (`secrets.compare_digest` against `SITE_PASSWORD`).
It had no rate-limiting, no lockout, no backoff — an attacker could throw unlimited
password guesses at `/owner` and only ever see 401s, never a throttle. The sibling
`_enforce_rate_limit` (a per-(route,client-host) sliding window, 10/60s, in-memory,
resettable) already existed but only fired on the POST actions via `require_owner_action`.
This session records each FAILED Basic-auth attempt against the client host and, after the
Nth failure inside the window, raises 429 with `Retry-After` BEFORE re-prompting — closing
the no-throttle gap while leaving the correct-password path, the same-origin CSRF, and the
POST rate-limit floor exactly as they were.

⚑ Self-initiated: no — coordinator-dispatched security-hardening slice.

## Close-out

**Evidence:**

- [[fill: files touched, test coverage, git commits, verify results — filled at flip]]

**Judgment:**

- Decisions made: [[fill: decisions taken this session]]
- Next session should know: [[fill: follow-ups + the honest in-memory/per-IP caveat]]

## 💡 Session idea

[[fill: one captured idea]]

## ⟲ Previous-session review

[[fill: one-line review of .sessions/2026-07-18-declare-env-vars.md]]
