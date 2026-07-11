# Dashboard bot-management readiness matrix

> **Status:** `living-assessment` — written 2026-07-11 (owner-directed: "find
> out how ready the dashboard is for actually managing the bot… bring it as
> close to finished as you can"). Sourced from the same-day audits of the
> dashboard service, the repo's ideas/decisions, and the live cross-repo data
> contracts. Companion spec: `docs/specs/bot-control-api-v1.md`.

**One-line verdict:** everything buildable on this side of the owner gate is
now built — the dashboard carries the complete management UX (typed setting
writes, cog routing, help appearance, audit trail) as an honest **dry-run**;
what separates it from live control is exactly three owner actions (answer
Q-0004, create the Discord OAuth app, provision the token + separate armed
service) and one superbot-side work item (extend `disbot/control_api.py` to
serve contract v1).

Legend — **(a)** buildable in this repo now · **(b)** needs an owner
credential/decision · **(c)** needs superbot-side work. "THIS PR" = closed by
the 2026-07-11 `claude/dashboard-bot-management` branch.

## 1. What exists / is stubbed / is missing

| Capability | State before | State now | Class | Closed by |
|---|---|---|---|---|
| Read-only oversight (functions/commands/settings/access/env/ideas/bugs/updates/console/status) | **Exists** — fully live off `dashboard.json`/`console.json` | unchanged | — | shipped (PR #8/#10/#11) |
| /admin management surface | **Stubbed** — four inert cards, disabled spans, "requires owner wiring" | **Built as dry-run**: live action inventory + preview→confirm→recorded flows against the typed schema | (a) | **THIS PR** |
| Controller seam (validate + build the exact wire request) | **Missing** | `dashboard/control_plane.py` `DryRunController` (mode `"dry-run"`, the only implementation) | (a) | **THIS PR** |
| Control-API wire contract | **Missing** — "no control-API spec draft exists" (audit §5) | `docs/specs/bot-control-api-v1.md` + machine pin `dashboard/bot_control_contract.json`, both test-pinned | (a) | **THIS PR** |
| Per-guild **setting write** UX | **Stubbed** (card #1) | Typed forms for all settings domains (type/allowed_values/default/hint from the live feed; bool/enum selects, int/float coercion, honest rejection) → dry-run | (a) dry-run / (b)+(c) live | **THIS PR** (dry-run half) |
| **Cog enable/disable** per guild UX | **Stubbed** (card #3) | Live cog inventory with command counts; enable/disable → dry-run; non-cog modules honestly excluded | (a) dry-run / (b)+(c) live | **THIS PR** (dry-run half) |
| **Help appearance** edit UX | **Stubbed** (card #2) | Hide/rename/re-describe form validated against live command/subsystem names + home message → dry-run | (a) dry-run / (b)+(c) live | **THIS PR** (dry-run half) |
| **Submission moderation** | **Stubbed** (card #4) | Still deliberately inert ("requires owner wiring (Q5)") — there is no submissions store to moderate, even in dry-run | (b) Q5 Postgres + mirror PAT, then (a) | not closed — Q5 gate |
| Action **audit trail** | **Missing** (idea existed: `/owner` audit-ring 💡, owner-area card) | `/admin/audit` — in-memory per-process log, honest "clears on restart/redeploy" label | (a) dry-run / (c) durable live audit is server-side per spec §7 | **THIS PR** (dry-run half) |
| **Guild picker** | **Missing** — no feed carries a guild list | Honest raw guild-id input, labeled as such | (c) needs a sanitized guild feed from superbot (idea filed in `docs/ideas/backlog.md`) | partially (honest input) |
| **Discord OAuth sign-in** | **Stubbed** — inert span | Honest `/admin/login` page: not configured, why, and where the armed version lives; no env read | (b) OAuth app + redirect URI; armed flow belongs to the separate service | **THIS PR** (honest scaffold) |
| **Live write path** (any) | **Missing by design** | **Still missing by design** — permanently, on THIS service | (b) Q-0004 + credentials, on a separate service | never (doctrine) |
| Restart / uptime / live bot status | **Missing** — no semantics in any feed | Out of v1 scope, recorded as a superbot-side open question (spec §8) | (c) | not closed — recorded |

## 2. (a) — was buildable here, and this PR built it

- Dry-run controller seam + contract pin + pin tests (contract parses,
  v1, every UI-previewable action validates).
- /admin overview with the honest state banner ("DRY-RUN — this service
  holds no credentials and cannot affect the live bot") and the live,
  feed-driven action inventory.
- All three management flows (settings / cogs / help appearance):
  form → preview of the exact contract-v1 request JSON → confirm →
  audit entry + "dry-run: recorded, not sent".
- `/admin/audit`, `/admin/login`, typed-rejection pages.
- Stale-leftover fixes: `dashboard/Dockerfile` SITE_PASSWORD comment,
  dead auth-middleware comment in the 404 handler.
- Tests: 30 → 48; `test_no_control_api_token_or_url_anywhere` untouched.

Adjacent (a) items found in the audit but NOT taken here (out of the owner's
ask, left as follow-ups): repo-wide control-API denylist checker; positive
env-var allowlist guard; `/owner` (control-plane) audit trail;
`docs/dashboard.md` refresh for the new /admin (blocked this session by the
PR #141 file-lock scope — docs/dashboard.md was outside the writable surface).

## 3. (b) — needs the owner (⚑ six-field asks filed in `docs/owner/OWNER-ACTIONS.md`)

1. **Answer Q-0004** (`docs/question-router.md`, open, blocking): where does
   live bot control live — websites / superbot / superbot-next? This is THE
   gate; it "decides whether a control-API credential ever enters a websites
   service."
2. **Create the Discord OAuth app** + decide the redirect URI (the armed
   service's public URL + callback path).
3. **Provision the scoped control-API token + the separate armed Railway
   service** with its env (names in spec §9: OAuth client id/secret,
   redirect URI, session secret, control URL + token). Never on the
   dashboard service; never the ambient production `RAILWAY_*_ID` vars.
4. (Pre-existing, paired) **Q5**: submissions Postgres + issue-mirror PAT —
   unblocks the fourth card (moderation), which stays inert until then.

## 4. (c) — needs superbot-side work

- **Extend `disbot/control_api.py` to serve contract v1**: the module and
  its bearer token already exist (env-usage shows the token read at
  `disbot/control_api.py:111`); v1 needs the action envelope, dry_run,
  idempotency, durable audit, per-actor permission re-check, and the
  `GET /control/v1/contract` drift endpoint (spec §3–§7).
- **Commit the canonical contract copy** in superbot (console-contract
  pattern) so this repo's pin has an upstream to sync from.
- **Open question (recorded, spec §8)**: restart/uptime/live-status verbs —
  no semantics exist in any feed today; v1 deliberately excludes them.
- **Optional feed improvement**: a sanitized guild list (id, name) in
  `dashboard.json` so management UIs can offer a real guild picker
  (idea filed in `docs/ideas/backlog.md`).
- **Data-shape flag**: `console.json` `bugs.open_count` vs `by_status.open`
  semantics mismatch (12 vs 1) — confirm upstream before reusing "open".

## 5. Standing rails this work held (and any successor must hold)

- `dashboard/tests/test_dashboard.py::test_no_control_api_token_or_url_anywhere`
  — the four forbidden literals never appear in non-test dashboard .py/.html.
  Untouched and green.
- Read-only doctrine: the dashboard's POST routes exist but their only
  effect is the in-memory dry-run log + rendered previews — no outbound
  write of any kind.
- "A wired control panel is a separate service, never mounted on a
  read-only surface" (`docs/dashboard.md`; botsite README invariant).
- `docs/RAILWAY-SAFETY.md`: ambient `RAILWAY_*_ID` env vars point at the
  live production bot and must never reach any Railway call.
