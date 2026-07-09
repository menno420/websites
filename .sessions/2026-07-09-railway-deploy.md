# 2026-07-09 — Deploy the control-plane site to Railway

> **Status:** `complete` — deployed live; docs shipped as PR #3 (`claude/railway-deploy`, squash-merged).

- **📊 Model:** claude-opus-4-8 (pre-v1.2.0 backfill; builder-session subagent, inherited — not independently confirmed)

**What this session was about:** Phase 3 of the kickoff sequence — create a
FRESH Railway project (never the production bot project), deploy the site
built in PR #2 there from GitHub, verify the live URL end-to-end, and record
the deployment in `docs/deployment.md` + make `docs/current-state.md` a real
snapshot.

## What was done

- Minted Railway project **`superbot-websites`**
  (`70198ece-cbc0-484e-86d9-f8a1eca4f045`), env `production`
  (`31485ecd-b3fe-4a8f-b136-337f6f099dc2`), service **`control-plane`**
  (`2c840017-a505-4144-b2ff-b2450430a7d9`) — created via the public GraphQL
  API with `RAILWAY_API_KEY` only; the ambient production-bot IDs were never
  passed to any call, and no destructive mutation was called against
  anything.
- Service repo-connected to `menno420/websites@main` (the account's GitHub
  integration covered the repo — no CLI fallback needed). First Dockerfile
  build succeeded (the build Phase 2 couldn't test locally).
- `SITE_PASSWORD` set as a service variable (value held by the owner, never
  in the repo). `GITHUB_TOKEN` deliberately left unset — owner TODO to mint
  a durable PAT (`docs/deployment.md`).
- Public domain created:
  **https://control-plane-production-abb0.up.railway.app**
- Docs: `docs/deployment.md` (new — IDs, domain, env-var names, redeploy
  path, guardrails, owner TODO, verification evidence),
  `docs/current-state.md` filled from kit template into a real snapshot,
  [D-0005] appended to `docs/decisions.md`.

## Verification (live, 2026-07-09)

- `GET /healthz` → `200` `{"ok":true,"cache_entries":0}`
- `GET /` unauthenticated → `401`; with Basic auth → `200` with **live**
  data (no token yet): superbot rulesets active, `code-quality` 1/1 green,
  live check runs, 6 open PRs (oldest #1761); superbot-next +
  substrate-kit rows live (`Kit test suite`, golden-parity).
- `GET /journal/superbot` (authed) → `200` listing real `.sessions/*.md`
  filenames.
- Degraded-until-PAT cells, as designed: actions secrets
  (`unknown (token lacks admin scope)`), auto-merge allowed
  (`unknown (needs push-scope token)`), CODEOWNERS enforced (`unknown`).
- `python3 bootstrap.py check --strict` green before PR.

## 💡 Session idea

Add a tiny `deploy-state` cell to the websites row of the board itself:
the app knows its own git SHA (bake `GIT_SHA` into the Docker build via a
Railway-provided build arg) and can compare it to the live `main` head it
already fetches — a one-line "deployed == main? ✅/⚠️ behind" indicator
turns silent deploy drift (failed build after a merge) into a visible cell
on the very board whose job is catching config drift.

## ⟲ Previous-session review

Phase 2's deploy notes were exactly what a handoff should be: the start
command, the exact env-var table, the generated password with explicit
"committed nowhere" provenance, and — most valuably — the two things it
*couldn't* verify (docker image build, rulesets/secrets cells) called out
as this session's first watch-items. Both checked out fine on the first
attempt, which is the payoff of that discipline. One improvement to the
workflow: the notes lived only in the ephemeral scratchpad — a cross-phase
handoff that must survive a container loss belongs in the repo (even as a
throwaway `docs/planning/` file deleted at sequence end); this session's
`docs/deployment.md` now durably carries everything the scratchpad note had
except the secret.
