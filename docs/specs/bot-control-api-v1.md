# Bot control API — v1 contract (specification)

> **Status:** `spec` — written 2026-07-11 (owner-directed bot-management push).
>
> This document SPECIFIES the wire contract for managing the live SuperBot
> from a web control panel. **Nothing in this repo implements the armed
> path** — the dashboard service is permanently credential-free and dry-run
> (Q-0004 below). Machine pin consumed by the dashboard's dry-run previews:
> `dashboard/bot_control_contract.json`. Readiness matrix:
> `docs/planning/dashboard-bot-management-readiness.md`.

## 1. Where each half lives (the binding topology)

- **Server / executor: superbot-side.** superbot already has a token-gated
  control-API seam — `disbot/control_api.py` (visible from here in
  `dashboard.json` `env_usage`: its token is read at
  `disbot/control_api.py:111`, layer `control_api`; the rework plan describes
  it as reachable over Railway private networking). v1 is an **extension of
  that seam**, or of its successor if the owner routes Q-0004 to
  superbot-next. It cannot live in this repo: the architecture invariant is
  "no service imports superbot's `disbot/` — cross-repo data arrives only as
  committed JSON, read-only, forward-only".
- **Armed client: a SEPARATE service**, created only after the owner answers
  Q-0004 (`docs/question-router.md`) — "never mounted on a read-only surface"
  (`docs/dashboard.md`). The dashboard service never holds a control URL or
  token; a test enforces the literal identifiers never appear there.
- **Dry-run client: the dashboard, today.** `dashboard/control_plane.py`
  builds and validates exactly the request JSON below, records it in memory,
  sends nothing.

## 2. Auth model

- **Service auth: bearer token.** Every request carries
  `Authorization: Bearer <token>` — a scoped, owner-provisioned secret held
  ONLY by the armed service (never this repo's dashboard; never committed).
  The bot rejects requests without it (`401 unauthorized`).
- **Actor identity: Discord OAuth on the client, re-checked by the bot.**
  The armed client signs the operator in with Discord OAuth and forwards
  their Discord user id in the `actor` field. The bot **re-checks that
  user's permission for the target guild/action on every write — the
  browser's claim is never trusted alone** (carried verbatim from the
  rework plan's description of the original panel). Failure is
  `403 forbidden`.
- **Authorization vocabulary.** `dashboard.json` `catalogue[].capabilities`
  (dotted strings, e.g. `ai.settings.configure` vs `ai.settings.view`) plus
  `access.tiers[]` (tier → discord_permission → subsystems) is the
  ready-made scope vocabulary; v1 servers SHOULD map each action to the
  matching `*.configure`-class capability.

## 3. Transport

- `POST <base>/control/v1/actions` — one action per request, enveloped as
  §4. (Single endpoint + action-typed envelope keeps idempotency, audit,
  and dry-run uniform across actions.)
- `GET <base>/control/v1/contract` — serves the canonical contract JSON so
  clients can drift-check their pin (the proven
  `console_data_contract.json` pattern: producer commits canonical, each
  consumer pins the version it was built against).
- `GET <base>/control/v1/health` — unauthenticated liveness.

## 4. Request envelope

```json
{
  "schema_version": 1,
  "action": "setting.write",
  "params": { "guild_id": "123456789012345678", "domain": "ai", "key": "ai_enabled", "value": false },
  "dry_run": false,
  "actor": { "discord_user_id": "987654321098765432", "display": "menno" },
  "idempotency_key": "9f0c2c4e0e5b4d1f8a7b6c5d4e3f2a1b",
  "requested_at": "2026-07-11T18:00:00Z"
}
```

- `schema_version` — always the contract version (1).
- `dry_run: true` → the server validates and returns the would-be `result`
  **without applying anything** (the dashboard's local dry-run mirrors this
  server behavior without the network).
- `idempotency_key` — client-generated, unique per intended action; the
  server stores recent keys and answers a replay with the ORIGINAL result
  (`idempotency_replay` in `error.code` if it chooses to flag it) instead
  of applying twice.
- `requested_at` — client clock, informational; the server's own clock is
  authoritative for audit.
- `actor.discord_user_id` — `null` only ever in dry-run from an
  OAuth-less surface (the dashboard sends
  `"display": "anonymous (OAuth not configured)"`); an armed server MUST
  reject a live write with a null actor.

## 5. Actions (v1)

Derived from the real committed data shapes (audited 2026-07-11, superbot
build `a03e5fe8`):

| action | params | validation source |
|---|---|---|
| `setting.write` | `guild_id, domain, key, value` | `dashboard.json` `settings[]` — 17 domains, 124 typed keys (`constant/key/type/allowed_values/default`), incl. 30 bool toggles and enums like `ai_default_provider ∈ {deterministic, openai, anthropic}`. Value must coerce to `type` / be in `allowed_values`. |
| `cog.set_enabled` | `guild_id, cog, enabled` | `dashboard.json` `cogs[]` (58 entries, 485 commands); `cog` must exist with `is_cog == true`. |
| `help.appearance.set` | `guild_id, entity_type, entity, changes` | `entity_type ∈ {command, subsystem, home_message}`; command/subsystem must exist in the feed; `changes` ⊆ `{hidden, display_name, description}`, at least one. |
| `submission.moderate` | `submission_id, verdict, reason` | `verdict ∈ {approve, reject}`. **Defined for completeness; NOT executable anywhere yet** — the submissions Postgres + issue-mirror PAT are the open Q5 owner action. The dashboard does not even preview it. |

The **feed is the schema, but the bot is the authority**: the dashboard's
dry-run validates against the committed `dashboard.json` (which can lag the
running bot by one deploy); the server validates against its live
`SettingSpec`s and MUST reject what the feed would have allowed if they
disagree.

## 6. Response envelope

```json
{
  "schema_version": 1,
  "ok": true,
  "action": "setting.write",
  "result": { "guild_id": "…", "domain": "ai", "key": "ai_enabled", "previous": true, "value": false },
  "audit_id": "a-000123",
  "applied_at": "2026-07-11T18:00:01Z",
  "error": null
}
```

Failure: `ok: false`, `result: null`, `applied_at: null`, and

```json
"error": { "code": "invalid_value", "message": "…", "details": {} }
```

Error codes (pinned in the contract): `invalid_action`, `invalid_params`,
`unknown_guild`, `unknown_setting`, `invalid_value`, `unknown_cog`,
`not_a_cog`, `unknown_entity`, `no_changes`, `unauthorized`, `forbidden`,
`idempotency_replay`, `unavailable`.

## 7. Audit fields

Every applied (non-dry-run) action MUST be durably audited server-side:
`audit_id`, the full request (incl. `actor` + `idempotency_key`), the
`previous` value where applicable, `applied_at`, and the outcome. `audit_id`
returns to the client so the panel can link "who changed what, when" — the
same audited-seam promise the original superbot panel made. (The dashboard's
dry-run analogue is deliberately weaker: in-memory, clears on restart, and
says so on the page.)

## 8. Out of scope for v1 (recorded, not forgotten)

- **Restart / stop / start, uptime, live status.** No restart or
  live-status semantics exist in ANY committed feed today (verified: the
  feeds are static build-time scans; freshest signal is
  `meta.generated_at`). Inventing them here would be fiction. **Superbot-side
  open question:** should the control API expose a restart verb and/or a
  live-status read (it already has a health server — `HEALTH_HOST`/
  `HEALTH_PORT` in `env_usage` — to build on)?
- **Alias/synonym writes.** The dashboard's /aliases tool already has a
  working suggest-via-GitHub-issue flow; promoting it to an API write can be
  v2.
- **Data-shape flag carried from the audit:** `console.json`
  `bugs.open_count` (12) counts open+partial+unknown while
  `bugs.by_status.open` is 1 — confirm the intended semantics upstream
  before any control/status surface reuses the word "open".

## 9. Env-var names for the FUTURE armed service (docs-only, deliberately)

These names live HERE and in `docs/owner/OWNER-ACTIONS.md` — never in
dashboard code (a dashboard test forbids the load-bearing literals there):
`DISCORD_OAUTH_CLIENT_ID`, `DISCORD_OAUTH_CLIENT_SECRET`,
`DISCORD_OAUTH_REDIRECT_URI`, `DASHBOARD_SESSION_SECRET`,
`CONTROL_API_URL`, `CONTROL_API_TOKEN` (the set the rework plan §1a records
the original superbot panel lighting up on). Provisioning them on a new,
separate Railway service is owner action ⚑ (see OWNER-ACTIONS).

## 10. Versioning

`schema_version` bumps on any breaking change to the envelope, an action's
params, or an error code's meaning; additive fields are non-breaking.
Canonical copy: superbot commits it next to the API (proposal:
`disbot/control_api_contract.json` or alongside the existing
`botsite/data/console_data_contract.json`); this repo's
`dashboard/bot_control_contract.json` pins the version its previews were
built against and is synced by hand in the same PR that adapts the UI —
exactly the console-contract protocol.
