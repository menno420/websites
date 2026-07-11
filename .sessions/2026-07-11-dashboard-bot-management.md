# 2026-07-11 — Dashboard bot-management: /admin dry-run UX + control-API v1 contract (owner-directed)

> **Status:** `complete` — branch `claude/dashboard-bot-management`; READY PR
> opened and HELD for the repo-wide merge hold (PR #141 awaits a human click).

- **📊 Model:** fable-5 · worker · owner-directed build (readiness audit → dry-run management UX + contract spec)

**What this session was about:** the owner asked "find out how ready the
dashboard is for actually managing the bot? find all ideas there are about
this and bring it as close to finished as you can." Rung: owner-directed
(routed via coordinator; three audit reports grounded the work). Binding
frame: Q-0004 (where live control lives) is an OPEN owner decision and
doctrine prescribes a wired panel be a SEPARATE service — so the dashboard
stays permanently credential-free and everything buildable here was built
against an explicit dry-run controller seam, with the armed path *specified*
(docs/specs) rather than implemented.

## What was done

- `docs/planning/dashboard-bot-management-readiness.md` — the readiness
  matrix: exists/stubbed/missing per capability, split (a) buildable-now /
  (b) owner credentials+decisions / (c) superbot-side; marks the (a) rows
  this PR closes.
- `docs/specs/bot-control-api-v1.md` + machine pin
  `dashboard/bot_control_contract.json` (console-contract pattern) — bearer
  auth, actor = Discord user id via OAuth re-checked bot-side, one action
  envelope (`setting.write`, `cog.set_enabled`, `help.appearance.set`,
  `submission.moderate`) with `dry_run`/idempotency/audit/error shape/
  `schema_version`; restart+uptime explicitly OUT of v1 (no feed semantics
  exist — recorded as a superbot-side open question); the
  `bugs.open_count` vs `by_status.open` flag recorded.
- `dashboard/control_plane.py` — `DryRunController`, the ONLY controller in
  this service (mode `"dry-run"`): validates against the live typed
  `dashboard.json` schema (enum/bool/int/float coercion, known
  cogs/entities, guild-id shape), builds the exact contract-v1 request
  JSON, records confirmed actions to an in-memory audit log (honestly
  labeled "clears on restart/redeploy").
- `/admin` rebuilt from four inert cards into a real overview: DRY-RUN
  banner ("this service holds no credentials and cannot affect the live
  bot"), live action inventory (settings domains → typed write forms at
  `/admin/settings/{domain}`, `/admin/cogs`, `/admin/help`), preview →
  confirm → recorded flows (`/admin/actions/preview|confirm`),
  `/admin/audit`, honest `/admin/login` OAuth-not-configured page.
  Submission moderation stays inert with its "requires owner wiring (Q5)"
  tag. Guild scope is an honest raw guild-id input (no feed carries a
  guild list). Stdlib urlencoded form parsing — zero new dependencies.
- Stale leftovers fixed: `dashboard/Dockerfile` SITE_PASSWORD comment; the
  dead "auth middleware" comment in the 404 handler.
- Tests 30 → 48 (dashboard): contract pin parses + v1, every
  UI-previewable action validates against the pin, preview JSON is
  contract-valid + typed, confirm writes the audit entry with preserved
  envelope, audit page renders, invalid value / unknown cog / bad guild /
  no-changes all reject with 400 and record nothing;
  `test_no_control_api_token_or_url_anywhere` UNTOUCHED and green; the old
  stub test consciously replaced by the honest-labels pin.
- `docs/owner/OWNER-ACTIONS.md` — three ⚑ six-field asks (answer Q-0004;
  Discord OAuth app + redirect URI; scoped control-API token + separate
  armed Railway service) + Open row 1 refreshed to the dry-run state.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — **299 passed**; `python3 bootstrap.py check --strict`
  — green except the designed born-red HOLD, which flips with this commit.

⚑ Self-initiated: no — owner-directed ("bring it as close to finished as you
can"), scoped by the standing Q-0004 gate (no credential, no live write).
File-lock honored: review/**, .github/workflows/**, docs/reviews/**, app/**,
botsite/**, control/** untouched (status is being reported via chat; the
usual `docs/dashboard.md` refresh was outside the lock's writable surface —
left as a named follow-up in the readiness doc §2).

## 💡 Session idea

**Ask superbot for a sanitized guild list in `dashboard.json`** — every
management flow starts with "which server?", but no committed feed carries a
guild list, so the UI honestly falls back to raw guild-id digits. One
sanitized `guilds[]` family (id, name) in the export turns the weakest field
of every form into a real picker, and the armed panel inherits it for free.
Worth having because guild-id digit-pasting will be the #1 papercut the
moment the panel goes live. Deduped against `docs/ideas/backlog.md` + the
queue-state NEXT list: nothing touches guild data. Captured in
`docs/ideas/backlog.md`.

## ⟲ Previous-session review

Slice 28 (#133 pickup latency): clean — honest-None discipline (never guess
a latency) and the same-PR contract-pin-move protocol were exactly the
patterns this session reused (typed rejection over silent coercion; the new
control-contract pin ships WITH the tests that hold it); what it missed:
nothing material — its "check, don't assume stranded" clause also kept this
session off the in-flight #141 lock surface.
