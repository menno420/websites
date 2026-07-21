# Site-consolidation cutover plan — retire the website duplicates, keep the estate, move the URLs

> Still open at final close — see PROJECT-CLOSEOUT.md Continuation (owner-gated).

> **Status:** `plan` — owner-reviewable. **NOTHING in this document is executed
> yet.** Every destructive step (Step 3) is GATED on the owner's explicit go
> (the coordinator relays it). Reference-repointing (Step 1) and the optional
> pretty-name reclaim (Step 2) are reversible and agent-doable, but are also
> sequenced behind owner sign-off on this plan so the whole cutover moves as one
> reviewed unit. Written 2026-07-18, on the corrected ground truth (#407).

## Summary

There are **two live copies** of the public website estate on Railway. The
consolidation retires the duplicate/old copies and keeps one canonical estate,
then moves any external URLs onto the keep services.

- **KEEP** — the `superbot-websites` Railway project (deploys `menno420/websites@main`).
  This is the real, deploy-current, four-service estate.
- **RETIRE** — three surfaces: the `reliable-grace` review copy
  (`review-production-f027`, a second deploy of `menno420/websites` review
  code), plus the two OLD sites that still deploy `menno420/superbot` code
  (`superbot-dashboard`, `superbot-app`).
- **NEVER RETIRE** — the `reliable-grace` `worker` service (the LIVE Discord bot,
  `menno420/superbot` `disbot/bot1.py`, no web domain) and the two Postgres
  databases. These are infrastructure, not website surfaces. Touching them is
  out of scope for this plan and explicitly forbidden.

**Current status (prerequisites already closed):**

- **Inventory un-inverted (#407).** The repo's canonical-vs-duplicate map in
  code + data + tests now matches live-Railway ground truth (was backwards — a
  cutover run off the old data would have retired the estate we keep).
- **Consolidation redirects shipped (#406, retargeted by #407).** The dashboard
  `/games` and `/reviews` redirects exist and now default to the KEEP services
  (`botsite-production-cfd7` games, `review-production-fc91` reviews).
- **Content parity confirmed.** review = identical between `f027` and `fc91`
  (same repo code); botsite `botsite-production-cfd7` is a NEW superset of the
  old `superbot-app`; dashboard `dashboard-production-a91b` supersedes the old
  `superbot-dashboard`.
- **Prose corrected (this PR).** The last references that named `f027` as the
  canonical review site are corrected to `fc91`.

All domains are auto-generated `*.up.railway.app` — there are **no custom
domains** to re-point at a registrar. "Moving the URLs" here means (a) repointing
references that name an OLD domain, and (b) the optional reclaim of a freed
pretty name onto a keep service.

## Inventory — keep vs retire

| App | KEEP (superbot-websites) | Deploy source | RETIRE | Deploy source |
| --- | --- | --- | --- | --- |
| control-plane | `control-plane-production-abb0.up.railway.app` | `menno420/websites@main` | — (no duplicate) | — |
| review | `review-production-fc91.up.railway.app` | `menno420/websites@main` | `review-production-f027.up.railway.app` (project `reliable-grace`) | `menno420/websites` (duplicate — identical code) |
| botsite | `botsite-production-cfd7.up.railway.app` | `menno420/websites@main` | `superbot-app.up.railway.app` (project `reliable-grace`) | `menno420/superbot` (OLD) |
| dashboard | `dashboard-production-a91b.up.railway.app` | `menno420/websites@main` | `superbot-dashboard.up.railway.app` (project `reliable-grace`) | `menno420/superbot` (OLD) |
| worker (Discord bot) | — | — | **NEVER RETIRE** — `reliable-grace` `worker`, `menno420/superbot` `disbot/bot1.py`, no domain | live bot |
| Postgres ×2 | — | — | **NEVER RETIRE** — infra | — |

The three retire targets all live in the `reliable-grace` Railway project
(alongside the `worker` bot + the Postgres DBs, which stay). The keep estate is
the whole `superbot-websites` project.

## Cutover steps — sequenced lowest-risk-first (review → botsite → dashboard)

Order within each app: **Step 1 (repoint references) → Step 2 (optional
pretty-name reclaim) → Step 3 (gated retirement).** Do the whole sequence for
review first (lowest risk — identical code, no external OLD-domain fanout), then
botsite, then dashboard (highest risk — most likely to have external
references). Each step has a concrete action and a rollback.

### Step 1 — Repoint external references (reversible, agent-doable)

Find every reference that names an OLD domain and point it at the KEEP domain,
so that after retirement nothing links into a dead service. This is a
find/replace across the repo plus a hand-audit of the external surfaces.

**OLD → KEEP repoint map:**

- `review-production-f027.up.railway.app` → `review-production-fc91.up.railway.app`
- `superbot-app.up.railway.app` → `botsite-production-cfd7.up.railway.app`
- `superbot-dashboard.up.railway.app` → `dashboard-production-a91b.up.railway.app`

**Where OLD domains are referenced (surfaces to sweep):**

1. **This repo (`menno420/websites`).** The canonical-review prose is corrected
   in this PR. Remaining in-repo `f027` occurrences are *intentional* — they
   name the retire target as the duplicate (`review-dup-f027` in the registries,
   the "NOT the f027 old copy" deploy comments, the tests that assert f027 is
   never treated as canonical, the fence note about not moving f027 during the
   EAP window). Those stay until the service is actually gone, then get retired
   as part of Step 3 cleanup.
2. **The Discord bot config / `menno420/superbot`.** The OLD `superbot-app` and
   `superbot-dashboard` deploy `menno420/superbot` code and may be linked from
   the bot's messages, embeds, or config, and from `superbot` repo docs. Audit
   `menno420/superbot` for the OLD domains before retiring (cross-repo — the
   coordinator/fleet-manager routes this; the websites seat is read-only toward
   superbot).
3. **The Anthropic EAP email + any external bookmarks.** The 2026-07-12 review
   email linked the `reliable-grace` review URL (`f027`). That is a sent
   artifact — it cannot be edited — so retiring `f027` will break that link.
   This is the single strongest reason Step 3 for review stays owner-gated:
   confirm the EAP window is fully closed and no reviewer is still using the
   `f027` link before the review service is destroyed. (Mitigation option: keep
   `f027` stopped-but-not-deleted, or reclaim its pretty name — see Step 2 — so
   the emailed link continues to resolve to the identical keep content.)
4. **Docs / owner queue / fleet-manager references.** Sweep `docs/`,
   `control/`, and the fleet-manager repo for OLD-domain mentions; correct the
   ones that name a canonical surface, leave the ones that name a retire target.

**Rollback:** revert the reference change (git revert for repo/doc changes; the
cross-repo edits revert the same way in their repos). Pure text — fully reversible.

### Step 2 — Optional pretty-name reclaim (per-service, reversible)

`superbot-dashboard` and `superbot-app` are nicer, more memorable prefixes than
the hashed keep prefixes (`dashboard-production-a91b`, `botsite-production-cfd7`).
After an OLD service is **deleted** (Step 3), its domain prefix is freed and can
be reclaimed by renaming the corresponding keep service's Railway domain prefix:

- freed `superbot-dashboard` → rename KEEP `dashboard-production-a91b`'s domain to `superbot-dashboard.up.railway.app`
- freed `superbot-app` → rename KEEP `botsite-production-cfd7`'s domain to `superbot-app.up.railway.app` (or a fresh clean prefix)
- review: `review-production-fc91` is already a clean prefix; reclaiming
  `review-production-f027` buys nothing (the hash is meaningless) — skip unless
  the emailed `f027` link must keep resolving, in which case reclaiming `f027`
  onto `fc91`'s service preserves that exact URL.

**Caveat — the unclaimed-name window.** Between deleting the OLD service and
renaming the keep service's domain, the pretty name is briefly unclaimed and
could in principle be taken. Do it per-service, immediately after the delete,
and re-verify the keep service answers on the new domain before moving on.

**Rollback:** rename the keep service's domain prefix back to its hashed default
(`dashboard-production-a91b` / `botsite-production-cfd7`). Reversible; the only
cost is the brief switch.

### Step 3 — Retirement (DESTRUCTIVE — GATED on the owner's explicit go)

Do **not** delete anything first. Retirement is a reversible-then-irreversible
two-phase move, per service, gated:

1. **Stop / disconnect (reversible).** Scale the OLD service to zero
   (stop the deployment) or disconnect its GitHub source so it stops serving.
   This is reversible — the service and its config still exist.
2. **Watch for breakage.** With the OLD service stopped, probe the KEEP service
   and any dependents (see Verification below). Confirm nothing that mattered was
   only reachable via the OLD domain. Give it an observation window (the review
   `f027` case especially — confirm no EAP reviewer traffic depends on it).
3. **Delete permanently (irreversible) — ONLY after the owner's EXPLICIT go.**
   Once the owner signs off per-service, delete the OLD service. Then do the
   Step 2 reclaim (if wanted) and the Step 1 repo cleanup (remove the now-dead
   `review-dup-f027` / dup rows + comments).

**Order:** review (`f027`) first, then botsite (`superbot-app`), then dashboard
(`superbot-dashboard`).

**NEVER, in any step:** stop, scale, disconnect, or delete the `reliable-grace`
`worker` service (the live Discord bot) or either Postgres database. They share
the `reliable-grace` project with the retire targets — operate strictly
per-service, by exact service ID, never at the project level.

**Rollback (pre-delete):** restart the stopped service / reconnect its GitHub
source — it returns to serving. **After delete there is no rollback** — which is
exactly why the delete waits for the explicit owner go and is done only after
the stopped-and-watched phase shows no breakage.

## Risk & verification

**How to verify each step live (probe the keep service + any dependents):**

- **Keep service healthy:** `GET https://<keep-domain>/healthz` → `200`
  `{"status":"ok","service":"<name>"}`; `GET /version` → the sha matching
  `menno420/websites@main` HEAD (deploy-current). The control-plane's
  `/api/readiness.json` deploy-drift row already tracks all four keep services
  `in_sync` — watch it stays green across the cutover.
- **Redirects still resolve to keep:** `GET https://dashboard-production-a91b.up.railway.app/reviews`
  and `/games` → 3xx to `review-production-fc91` / `botsite-production-cfd7`.
- **After Step 1 repoint:** grep the repo (and the cross-repo surfaces) for the
  OLD domains — every remaining hit should be an intentional retire-target label,
  never a live link a user follows.
- **After Step 3 stop (before delete):** the OLD domain should stop answering
  (connection refused / 404) while the keep domain keeps returning 200 — this is
  the "watch for breakage" signal. If anything real broke, restart the OLD
  service (rollback) and investigate before proceeding.

**Railway API note.** The stop / rename / delete mutations are supported by the
Railway account API (`RAILWAY_API_KEY`, project-scoped to `superbot-websites` /
`reliable-grace` — **never** the ambient production-bot `RAILWAY_*` IDs, per
`docs/RAILWAY-SAFETY.md`). The relevant GraphQL mutations, by the names already
referenced in this repo's deploy docs/tests, are approximately:
`serviceInstanceRedeploy` / a scale-or-stop instance update (stop),
`serviceDomain*` create/update (rename/reclaim a domain prefix), and
`serviceDelete` (permanent delete). Confirm the exact current mutation names +
argument shapes against the live Railway GraphQL schema at execution time — the
coordinator performs the actual mutations (the websites app services make no
Railway mutations by construction).

## Execution gate

**Nothing in this document is executed yet.** This is a plan for owner review.
Step 1 (repoint) and Step 2 (reclaim) are reversible and agent-doable but wait on
owner sign-off on the plan; Step 3 (retirement) additionally requires the owner's
**explicit per-service go** before any delete, relayed by the coordinator. The
Discord `worker` bot and the Postgres databases are never touched.
