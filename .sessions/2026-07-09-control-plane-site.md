# 2026-07-09 — Build the control-plane site

> **Status:** `complete` — shipped as PR #2 (`claude/control-plane-site`, squash-merged).

- **📊 Model:** claude-opus-4-8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

**What this session was about:** build the control-plane / oversight site — the
repo's core deliverable (kickoff sequence step 2): a **readiness board** and a
**journal browser**, live GitHub data, auth-gated, Railway-ready.

## What was built

- `app/` — FastAPI + Jinja2 server-rendered app (stack: [D-0003]):
  - `/` readiness board: per repo (superbot, superbot-next, substrate-kit,
    websites) — ruleset/branch-protection, required checks configured AND the
    exact check runs currently green/red on the `main` head, CODEOWNERS
    present/enforced, Actions secrets (names only, degrades to
    `unknown (token lacks admin scope)` on 403), auto-merge + enabler-workflow
    presence, open-PR health (count + oldest). superbot-next's `report`
    (golden-parity) job is badged `red-by-design`, never counted broken.
  - `/journal`, `/journal/{repo}`, `/journal/{repo}/file?path=…` — session
    logs, decision ledgers, question-routers, PR + commit history, every item
    deep-linked to GitHub; file view renders markdown.
  - `/api/readiness.json`; `/healthz` (unauthenticated, for Railway).
  - Auth: HTTP Basic vs `SITE_PASSWORD` (constant-time; fails CLOSED when
    unset). Cache: per-URL TTL 180 s, transient errors never cached,
    `?refresh=1` busts ([D-0004]).
- `Dockerfile` (python:3.12-slim, binds `0.0.0.0:$PORT`), pinned
  `requirements.txt`, `docs/site.md` (routes/env vars/model, linked from
  README), `tests/test_app.py` (7 tests: auth gate, fail-closed,
  red-by-design annotation, cache policy), `tools/dev_api_mirror.py`
  (dev stub for egress-restricted local verification, Q-0105-style
  provenance/delete-me header).

## Verification

- 7/7 tests green; `bootstrap.py check --strict` green.
- Live local run verified: auth 401/503 paths; board showed the REAL current
  state — superbot head `2166c532` all checks green + 6 open dependabot PRs
  (oldest #1761, 2026-07-06); superbot-next head `7a14807f` 11 green +
  `report=red-by-design`; substrate-kit `Kit test suite` +
  `Cold-adoption smoke` green; journal rendered superbot-next's real
  decisions ledger (D-0001…) and superbot's question router (…Q-0254) live
  from raw.githubusercontent.com.
- Container egress blocks `api.github.com` (session policy), so API-only
  endpoints were verified through `tools/dev_api_mirror.py` loaded with real
  responses fetched via the GitHub MCP minutes earlier; file bodies were
  fetched genuinely live from the raw host. Rulesets/secrets cells were
  verified for graceful degradation only — **Phase 3 must eyeball those cells
  on Railway with the durable PAT.**
- Docker daemon unavailable in this container — Dockerfile untested as an
  image build (mirrors the local pip+uvicorn run exactly; flagged to Phase 3).

## Decisions made this session

- [D-0003] stack: FastAPI + Jinja2 + httpx, server-rendered, no build step.
- [D-0004] data/auth/cache model (raw-host-without-token quirk documented:
  sending a bad bearer to raw.githubusercontent.com turns 200s into 404s).
- Kit slots answered: `primary_language`, `verify_command`.

## 💡 Session idea

The board already computes everything needed for alerting: a tiny
`/api/readiness.json` poller (GitHub Action on cron in this repo) could diff
the previous snapshot and open an issue when a required check goes red on a
main head or an open PR crosses an age threshold — turning the passive board
into the active watchdog half of the audit checklist, with zero new data
plumbing.

## ⟲ Previous-session review

The adoption session (PR #1) was clean and honest — its minimal-answer
interview posture ("the stack choice belongs to the phase that writes code")
made this session's D-0003/slot-answer flow exactly one step, which validated
the deferral. One improvement it points at: it left `docs/current-state.md`
as unfilled kit template while shipping a session log that says the repo is
governed — the same honesty gap the audit checklist flagged on superbot-next.
This session did not fill it either (scope: the site); the next session
should make `current-state.md` real before the template text ages into
misinformation — cheap now, drift later.
