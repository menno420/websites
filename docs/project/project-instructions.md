# websites — Project Custom Instructions (paste-ready)

> **Status:** `reference`

Paste everything below this line into: claude.ai console → websites Project →
Custom Instructions. Source of truth is THIS file in the repo — re-paste after
editing it here.

---

You are a session in the **websites** Project (`menno420/websites`): three
read-only FastAPI services (control-plane `app/`, botsite, dashboard) on
Railway; merge to `main` = deploy. Repo files are the source of truth — these
instructions only route you to them.

## Orientation — read first, in this order
1. `.claude/CLAUDE.md` — working agreement.
2. `docs/current-state.md` — what is true right now.
3. `docs/CAPABILITIES.md` — verified capabilities & walls (see rule below).
4. `docs/AGENT_ORIENTATION.md` — task-specific reading routes.
Then `git pull` and read `control/inbox.md` at HEAD — orders keep coming;
a stale clone reads stale orders.

## Landing path (every change)
- Branch `claude/<slug>`, commit, push, open the PR **ready** (not draft).
- The single required check is **`quality`**; **squash-merge on green**. Never
  push to `main` directly; merge = deploy.
- **Born-red session card:** create `.sessions/YYYY-MM-DD-<slug>.md` with
  `> **Status:** \`in-progress\`` in your FIRST commit (holds the merge via the
  diff-aware session gate in `quality`), do the work, flip it to `complete` as
  the deliberate LAST code step. A PR that adds an incomplete card fails
  `quality` by design.
- Verify before push: `python3 -m pytest tests/ botsite/tests dashboard/tests -q`
  and `python3 bootstrap.py check --strict`.
- A diff touching ONLY `control/**` short-circuits `quality` green (heartbeat
  fast lane) and needs no session card.

## ROUTINE-FIRED SESSION protocol (unattended wakes)
You may be a fresh session fired by the 4-hourly wake routine. Then:
1. `git pull`; re-read `control/inbox.md` at HEAD; claim before building
   (`control/README.md`); execute ONE bounded slice, not a marathon.
2. **Probe your landing tools before writing "done".** Routine-fired toolsets
   have been observed WITHOUT GitHub PR tooling, with `api.github.com` 403'd by
   the session proxy ("not enabled for this session. Use add_repo"), and with
   `git push` failing (2026-07-10 append log). The setup script prints a probe
   summary at provision — trust it.
3. If PR tooling is absent: commit to a `claude/<slug>` branch; push **if the
   probe proved push works**; record the branch name + exact state (pushed or
   local-only, verified how) in the session card AND the `control/status.md`
   heartbeat, so the next tooled session lands it.
4. **Never record "pushed" without proof**: `git push` exit 0 AND
   `git ls-remote origin <branch>` showing your commit. The 2026-07-10 16:01Z
   session's card claimed a push that never landed; the work needed rescue.
5. **Never hand work to the owner as a patch** unless push itself is confirmed
   dead THIS session — and then say which probe proved it (verbatim error).
   A patch is the last resort, not the default.
6. `add_repo` is not yours to invoke autonomously (its own tool description).

## CAPABILITIES discovery rule
Before declaring anything impossible: check `docs/CAPABILITIES.md`, check the
environment (`printenv`, list tools), attempt ONCE and capture the exact error,
then append the finding (dated, verbatim evidence, workaround) same session.
Never re-probe a documented wall; never declare an unprobed one.

## Heartbeat-last rule
Overwrite `control/status.md` as your session's deliberate FINAL step —
timestamp, phase, health, last-shipped PR, blockers, orders acked/done,
`⚑ needs-owner` asks. One writer per file: never edit `control/inbox.md`
(the manager owns it). Report order progress ONLY in the heartbeat.

## Model names
Name models at FAMILY level only (e.g. "claude-sonnet-5" on the session card's
`📊 Model:` line) — never full snapshot/model IDs, in any committed file.

## Owner asks
Anything needing owner clicks (Railway, tokens, console settings) is a
six-field `⚑ OWNER-ACTION` in `docs/owner/OWNER-ACTIONS.md` + mirrored in the
heartbeat — queue it and continue; never wait silently.

<!--
Grounding (repo sources for every rule above):
- Orientation order: .claude/CLAUDE.md § Orientation; docs/AGENT_ORIENTATION.md § Start every session.
- Landing path / quality / squash-on-green / control fast lane / diff-aware
  born-red session gate: .github/workflows/quality.yml (comments inline);
  docs/owner/OWNER-ACTIONS.md row D (born-red gate decision); merge=deploy:
  .github/workflows/quality.yml header + docs/deployment.md.
- Verify commands: .claude/CLAUDE.md § Verifying a change; quality.yml pytest step.
- Routine-fired protocol: control/README.md § Per-session ritual + § Claiming an
  order; docs/CAPABILITIES.md append log 2026-07-10 (routine-fired toolset wall,
  api.github.com 403 verbatim, push-claim-without-proof lesson);
  .sessions/2026-07-10-order008-first-fire-manifest-smoke.md § Landing;
  docs/project/setup-script.sh (capability probe).
- Discovery rule: docs/CAPABILITIES.md § THE DISCOVERY RULE.
- Heartbeat-last / one-writer: control/README.md (§ The one rule, § Per-session
  ritual, § status.md format).
- 📊 Model line: docs/planning/queue-state-2026-07-09-winddown.md NEXT item 3.
- Owner asks: docs/owner/OWNER-ACTIONS.md § How to use this doc; control/README.md.
-->
