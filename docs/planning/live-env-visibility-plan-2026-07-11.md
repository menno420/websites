# Plan — live env-variable visibility (gated), with per-env management links

> **Status:** `plan` — owner-directed 2026-07-11. Revives + extends the env
> surface the owner wants: a **password-locked** page that shows every project's
> env variables, **loads their live state from Railway**, and gives a **guide or
> direct link to manage each**. This doc records what already exists, the exact
> gap, and the build design (with the one security decision the owner must make).

## What already exists (so we build, not rebuild)

The owner remembered "a plan for this" — here is the function trail:

1. **`/environments` (public) — the ORDER 005 registry-view decision, PR #53** (`app/environments.py`).
   Renders `menno420/fleet-manager` → `environments/` read-only: setup scripts +
   the env-var **NAME / placeholder schemas** (now including `archetypes.md` and
   `env-grant-policy.md`), copy-to-clipboard, honest degradation. **Secrets never
   present by design — names/placeholders only, sourced from GitHub, not Railway.**
2. **`/owner` (gated)** — the gated-owner-area decision (`app/owner.py`). HTTP Basic, password
   constant-time-compared to `SITE_PASSWORD`, fail-closed 503 if unset. Already
   un-masks Actions **secret NAMES** and runs reversible privileged actions
   (cache refresh, rerun-CI) via `GITHUB_TOKEN`.
3. **The board reads live via a Railway-set token — the board-token decision**: a GitHub PAT is
   set on the `control-plane` service *through* the Railway GraphQL API (variable
   upsert, `RAILWAY_API_KEY`, ambient production IDs never passed).

**So the missing "function" was never written by design, not lost.** The gated-owner-area decision and
`docs/deployment.md` / `docs/runtime_contracts.md` state it explicitly: *"this repo
makes no Railway API calls at all … any Railway account-token action is deliberately
unwired — adding one is an owner decision, not an agent call."* The plan reached
"render the registry (names) + build the gated area" and **stopped** at the live
Railway read, pending the owner deciding to put a Railway token in the service.
**That decision is now made (2026-07-11): the owner wants it, and will provide a token.**

## The gap (what this plan adds)

| Want | Today | This plan |
|---|---|---|
| Live env values/state from Railway | none (registry names only) | read the target project's variables live via a **project-scoped `RAILWAY_TOKEN`** |
| Password-locked | `/environments` is **public** | new page lives under the existing `/owner` gate |
| A guide / manage-link per env | GitHub file link only | per-variable "manage it here" deep link (Railway/Discord/Stripe/…) |

## Design

### Route
Add **`/owner/environments`** (gated by the existing `require_owner`), NOT a new
public route. Reuse `app/owner.py`'s gate verbatim. The public `/environments`
registry page stays as-is (names/schemas, no secrets).

### Data source — project-scoped token, read-only, one project at a time
- New env var **`RAILWAY_TOKEN`** on the `control-plane` service, **project-scoped
  to `superbot-websites` only** (per `fleet-manager/environments/env-grant-policy.md`
  — NOT the account `RAILWAY_API_KEY`, which reaches the production bot's project).
- Query Railway GraphQL (`https://backboard.railway.app/graphql/v2`) for that
  project's services + their variables. Same TTL-cache pattern as the `github`
  layer; honest degradation (`not-configured` if `RAILWAY_TOKEN` unset,
  `unavailable` on fetch failure) — never a 500, never fabricated.
- **To show OTHER projects** (the full-fleet view the owner wants): each project
  the site should surface contributes its OWN project-scoped token (e.g.
  `RAILWAY_TOKEN_VENTURE`, `RAILWAY_TOKEN_MINEVERSE`), aggregated read-only. This
  keeps blast radius per-project and never requires the account key on a web
  service. Start with `superbot-websites`; add projects as their tokens land.

### ⚠️ The one owner decision — values vs. names+status
Railway's `variables` query returns **values**. Two options:
- **(A) names + presence/last-updated status only (RECOMMENDED default).** Show
  *which* variables are set on each service, set/unset, and when — never the
  secret value. Gives "what's configured where" at a glance without turning a
  web page (even gated) into a secret-exfiltration target.
- **(B) reveal values behind the gate.** Maximum convenience (copy a value), but
  the page now renders live secrets; a single gate/misconfig leaks them. If chosen,
  it must be `/owner`-only, no-cache-store, and audited.

Recommendation: **ship (A) first**; add per-value reveal (B) behind an extra
confirm only if the owner explicitly wants it. A test asserts no secret *value*
appears in any public route regardless.

### Per-env management guide / links
Render, next to each variable, a **"manage →"** deep link from the console-link
table in `fleet-manager/environments/env-grant-policy.md` (Railway variables page,
Discord dev portal, Stripe dashboard, GitHub PAT settings, …), matched by variable
name prefix (`STRIPE_*` → Stripe, `DISCORD_*` → Discord dev portal, `RAILWAY_*` →
Railway, else the project's Railway Variables page). Plus a one-line "what this is
for" from the archetypes mapping. This is the "guide for each env" the owner asked for.

### Degradation + safety (non-negotiable, matches the estate)
- Route always 200; honest banners; never fabricate.
- **Never** accept the ambient production Railway trio (`RAILWAY_PROJECT_ID/…`) —
  keep `scripts/check_no_ambient_railway_ids.py` green; the project token is bound,
  not ambient.
- No secret value in any public HTML/JSON (the existing public-no-secrets test extended).

## Suggested slices
1. `/owner/environments` gated route + Railway read layer (project-scoped token, TTL cache, degradation) + option (A) names+status view.
2. Per-variable "manage →" links + "what it's for" from the env-grant-policy/archetypes data.
3. (owner-gated) option (B) value reveal, if requested.

## References
- `app/environments.py`, `app/owner.py`; the ORDER 005 / gated-owner-area / board-token decisions (all in `docs/decisions.md`); `docs/RAILWAY-SAFETY.md`.
- `fleet-manager/environments/env-grant-policy.md` (tiers + manage-links) + `archetypes.md` (name mapping).
