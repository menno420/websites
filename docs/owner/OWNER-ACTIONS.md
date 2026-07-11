# Owner actions — decisions & actions waiting on you

> **Status:** `owner-guidance`
>
> A single **living** list of decisions/actions that only the owner can make,
> and the ones already made. Future sessions keep this current: when the owner
> decides one, move it to **Decided** with the decision + provenance; when a new
> owner-gated fork appears, add it to **Open**. Skimmable by design.

## 🟡 Open — waiting on the owner

| # | Decision | What it unblocks | Notes / where it lives |
|---|---|---|---|
| 1 | **Dashboard `/admin` live-bot control** — build + wire a production control path, or keep it a labeled stub? | The Discord-OAuth panel that writes the live bot's control API (settings / help / cog routing / submission moderation). | Needs your direct word. Stub today: `dashboard/templates/admin.html`, zero control-API credentials present. Wiring = a **separate** service (OAuth app + control-API token) + deciding *where bot control lives* (websites / superbot / superbot-next). Rework-plan **Q4** (`docs/question-router.md`). |
| 2 | **Botsite `/submit`** — provision a submissions Postgres + moderation mirror, or keep the stub? | The public feature/bug intake pipeline (moderated queue → GitHub-issue mirror). | Stub today: `botsite/templates/submit.html` (now shows a "Stub — not wired" badge). Needs a Postgres + mirror PAT. Rework-plan **Q5**. |
| 3 | **Redeploy-from-browser scoped deploy hook** — yes / no? | A gated `/owner` button that triggers a Railway redeploy of a websites service from the site itself. | Would require a Railway deploy hook (scoped to `superbot-websites` only — never the ambient production IDs, see `docs/RAILWAY-SAFETY.md`). Currently deploy = merge to `main` (auto). |
| 4 | **Custom domains** for the three sites (control-plane / botsite / dashboard). | Friendly URLs instead of `*.up.railway.app`. | Deferred to cutover. Rework-plan **Q6**. |
| 5 | **Preserve v1 visual design vs. the shipped restyle** (rework Q2). | Whether the ds/-based restyle stands or the original superbot visual design is carried over. | Rework-plan **Q2** (`docs/planning/dashboard-botsite-rework-plan-2026-07-09.md`). |
| 6 | **OLD-site cutover / retirement in superbot** — go / no-go? | Retiring the `dashboard/` + `botsite/` still living in `menno420/superbot` once these replace them. | Gated: needs your go. Verify the live websites URLs first (`python3 scripts/healthcheck.py`). |

### ⚑ Active six-field asks

```markdown
⚑ OWNER-ACTION
WHAT: Create the fourth Railway service so the new program-review site (built for Anthropic reviewers) goes live.
WHERE: railway.app → project superbot-websites → New → Service → GitHub repo menno420/websites.
HOW: set Root Directory = review (the service's own Dockerfile at review/Dockerfile is picked up automatically, exactly like botsite/dashboard); branch = main; no environment variables needed (the service is read-only and network-free). After the first deploy, check <service-url>/healthz returns {"status":"ok"} and /version shows the deployed sha.
WHY-IT-MATTERS: the review site — process, growth charts, successes, and an honest problems page, all from the repo's committed record — exists on main but has no URL until the service exists.
UNBLOCKS: a shareable live URL for Anthropic reviewers; the board's deploy-drift row and scripts/healthcheck.py can then also add the fourth service.
VERIFIED-NEEDED: service creation is a Railway account mutation — the Railway-safety policy (`docs/RAILWAY-SAFETY.md` + the deploy decision in the ledger) forbids agent-initiated Railway mutations without your explicit go, so this was deliberately not attempted (the same policy wall as the Postgres ask; no new attempt/error needed).
```

(Previous state: none open — the one conditional ask (external wake-trigger
fallback) self-expired 2026-07-10T16:01:32Z: the self-armed routine's first
fire landed; see row E and
`.sessions/2026-07-10-order008-first-fire-manifest-smoke.md`.)

**Historical record (kept verbatim per the capability ledger):** before ORDER
008, the fleet **coordinator's** toolset exposed **no send_later/scheduling
tool at all** — no scheduler primitive of any kind — and its cross-session
probe failed with the exact error: "target session could not be verified;
retry send_message shortly". That coordinator-side wall still stands; ORDER
008's finding is that a **worker session on this surface** does carry a
scheduler primitive (`docs/CAPABILITIES.md` append log, 2026-07-10).

## 🟢 Decided / resolved

| # | Item | Decision | Provenance |
|---|---|---|---|
| A | **Required `quality` CI check on `main`** | **Owner set the ruleset** — `quality` is now a REQUIRED status check; PRs blocked until green. | Owner-configured ruleset 2026-07-09; verified live (PR #18 `mergeable_state=blocked` while `quality` pended). Board row shows `quality` configured + expected. |
| B | **Basic-auth gate on control-plane + dashboard** | **Dropped** — both sites are fully public; the readiness board masks Actions-secret names to a count. | Owner verbatim "Yes drop the auth"; decision stamped in `docs/decisions.md`. |
| C | **superbot kickoff doc (was PR #1876) → README link** | **Resolved** — the doc is merged on superbot `main`; the README link now returns HTTP 200 (verified 2026-07-09). Was a 404 while the PR was unmerged. | `README.md` → `superbot/docs/planning/websites-project-kickoff-2026-07-09.md`. |
| D | **Leaky born-red session gate** (PR #19 auto-merged empty on an `in-progress` card) | **Resolved — no owner action** — adopted upstream kit **v1.0.0** `bootstrap.py` (fails born-red cards under `--strict`) + folded diff-aware `--session-log` into the `quality` gate. Both directions proven + regression-tested. Upstream substrate-kit repo fix handled by a **separate** session. | Decision stamped in `docs/decisions.md` (born-red-gate entry); `.github/workflows/quality.yml`; `tests/test_born_red_session_gate.py`. |
| E | **Lane wake routine** (was Open row 7 — external owner-armed trigger) | **Self-armed and CONFIRMED working — no owner click needed.** Fleet ORDER 008 (2026-07-10) verified sessions can create routines; this lane armed trigger `trig_017H9Qb9oxtLgUy6sw2gnSHg` (cron `0 */4 * * *`, fresh-session-per-fire, prompt = the standing inbox ritual). First fire confirmed 2026-07-10T16:01:32Z (`list_triggers` `last_fired_at`; this session is that fire) — the conditional fallback ask has been withdrawn. | `control/inbox.md` ORDER 008; claim PR #56; `docs/CAPABILITIES.md` append log 2026-07-10; `.sessions/2026-07-10-order008-first-fire-manifest-smoke.md`; `control/status.md`. |

## How to use this doc

- New owner-gated fork → add a row to **Open** with where it lives.
- Owner decides → move it to **Decided / resolved** with the decision + a
  provenance pointer (a `[D-NNNN]`, a `Q-NNNN`, or a dated verification).
- Keep it short. Detail belongs in the linked decision/plan/router, not here.
