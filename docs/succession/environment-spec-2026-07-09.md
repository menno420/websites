# websites — gen-2 environment spec (2026-07-09)

> **Status:** `reference` — succession deliverable from the gen-1 wind-down. What a
> fresh gen-2 Project environment for menno420/websites needs: base assumptions,
> the defensive setup script, the env var NAMES (never values), and network
> facts, with the script's verbatim test evidence. Source code and the live
> environment win over this file — re-verify walls per the `docs/CAPABILITIES.md`
> discovery rule before declaring them.

This doc is linked from the "Succession (gen-1 → gen-2)" section of
`docs/AGENT_ORIENTATION.md`, alongside the setup script it specifies
(`scripts/setup-env.sh`).

## 1. What the gen-2 environment needs

**Base image assumptions (verified in the gen-1 wind-down container):**

- Linux container, `python3` on PATH. The wind-down container ran **Python
  3.11.15** at `/usr/local/bin/python3`; production services build on **Python
  3.12** (per the repo Dockerfiles / working agreement). The gap has not caused a
  test/CI divergence in gen-1 — the pinned deps install cleanly on both — but the
  gen-2 lane should not assume 3.12 locally.
- `pip` available as `python3 -m pip` (running as root; the setup script sets
  `PIP_ROOT_USER_ACTION=ignore` to quiet the warning).
- `git` present. **Fresh clones may sit on a DETACHED HEAD at main's tip**, not
  a `main` branch (verified gen-1, dossier §3.15d) — setup must tolerate it, and
  sessions must branch (`git switch -c <branch>`) before committing.
- **Nothing beyond the stdlib is preinstalled for this repo.** Verified gen-1:
  a fresh container fails `python3 -m pytest` with
  `/usr/local/bin/python3: No module named pytest`. All deps come from the setup
  script below.
- Repo layout the script expects (and defensively re-discovers): three services
  — `app/` (control-plane, deps in **root** `requirements.txt`), `botsite/` and
  `dashboard/` (each with its **own** `requirements.txt`) — plus `tests/`,
  `bootstrap.py`. Two packages are needed **beyond** the requirements files:
  `python-multipart` and `pytest` (dossier §3.15a).

**The setup script:** `scripts/setup-env.sh` (committed alongside this spec;
wire it into the fresh Project's **environment config as the SessionStart /
environment setup hook** — the Project's startup command — so it runs once per
fresh container before any work). Design contract:

- **Always exits 0.** A broken step is printed (`FAIL:` lines + a `failures:`
  block in the summary), never fatal — a red setup hook must not brick a session.
- **Assumes nothing about repo shape.** Repo dir resolved from `$1` →
  `$WEBSITES_REPO_DIR` → `/home/user/websites` → cwd; every path checked before
  use; requirements files discovered by `find -maxdepth 2 -name 'requirements*.txt'`
  and each installed individually and non-fatally (no bare
  `pip install -r requirements.txt`).
- Installs the two known extras (`pytest`, `python-multipart`) even when no repo
  is found.
- Tolerates detached HEAD (reports it, reminds to branch), missing git, missing
  python, missing pip — each degrades to a printed failure, never an exit.
- Ends with a machine-scannable summary: python version, per-requirements-file
  ok/FAIL, pytest importability, and env var **NAMES** present/absent
  (`GITHUB_TOKEN`, `RAILWAY_API_KEY`, `SITE_PASSWORD`, `DATABASE_URL`) — presence
  only, values never printed.

**After setup, the verification pair** (run unpiped, echo `$?` — the pipe
swallows exit codes, dossier §3.3): `python3 -m pytest tests/ -q` (CI runs all
three suites: `tests/ botsite/tests dashboard/tests`, 125 tests at wind-down)
and `python3 bootstrap.py check --strict`.

## 2. Minimal env var NAMES (names only — NEVER values)

| Name | What breaks without it |
|---|---|
| `GITHUB_TOKEN` | Control-plane board cells degrade (live GitHub REST + raw-content reads unauthenticated → rate-limited/blank) and `/owner` re-run-CI is dead; agent-side GitHub work falls back to MCP tools only. |
| `RAILWAY_API_KEY` | No Railway API access — cannot inspect/manage the `superbot-websites` services (deploy state, service config); merge-deploys still happen but are unverifiable from the session beyond public `/version`. |
| `SITE_PASSWORD` | The control-plane's gated `/owner` area (un-masked board, cache refresh, CI re-run) is inaccessible — HTTP Basic has no credential to check against. Absent in the wind-down container (owner-side secret). |
| `DATABASE_URL` | botsite `/submit` stays a labeled stub — the moderated submissions queue (rework Q5, OWNER-ACTION #1) cannot come live. Expected to be set on the `botsite` Railway service, not necessarily in agent sessions. |

Also known to the lane (not in the setup script's check set): `GITHUB_PAT` (the
owner's name for the deploy token during seeding), `AUTOREFRESH_SECONDS`, `PORT`,
`RAILWAY_GIT_COMMIT_SHA`/`GIT_SHA` (Railway/Docker-injected, services only), and
the **denylisted ambient trio `RAILWAY_PROJECT_ID` / `RAILWAY_ENVIRONMENT_ID` /
`RAILWAY_SERVICE_ID`** — those point at the LIVE PRODUCTION BOT and must never
reach a Railway call (CI-enforced by `scripts/check_no_ambient_railway_ids.py`;
see `docs/RAILWAY-SAFETY.md`).

## 3. Network facts

- **Direct `api.github.com` HTTP is blocked** from agent sessions → GitHub is
  **MCP-tools-only** (dossier §3.14 / `docs/CAPABILITIES.md`). Known MCP caveats:
  ~1 min stale-cache reads (confirm merges via `git ls-remote`), tight GraphQL
  quota, proxy 403 on ruleset/branch-protection writes and on branch deletion.
- **All outbound HTTPS goes through the pre-configured agent proxy**
  (CA bundle `/root/.ccr/ca-bundle.crt`; never disable TLS verification or unset
  `HTTPS_PROXY`). `pip install` works through it (verified in every test run
  below).
- **Railway API is reachable with `RAILWAY_API_KEY`** — the gen-1 lane managed
  the `superbot-websites` project through it (service inspection, the dashboard
  deploy-trigger recreation, PR #29/#30). Explicit `superbot-websites` IDs only;
  never the ambient `RAILWAY_*_ID` trio (§2).
- The three public site URLs (`control-plane-production-abb0` /
  `botsite-production-cfd7` / `dashboard-production-a91b` `.up.railway.app`) are
  probeable for `/healthz` + `/version` drift checks via `scripts/healthcheck.py`.
- `menno420/fleet-manager` is **NOT reachable** from this repo's sessions (MCP
  access denied; allowed repos at wind-down: superbot, substrate-kit, websites,
  superbot-next). The proven fleet setup-script pattern there was therefore not
  consulted; `setup-env.sh` was written and proven from scratch.

## 4. Test evidence — setup-env.sh (verbatim, 2026-07-09)

All runs performed against the drafted script in the wind-down session's
scratchpad; `EXIT_CODE=` echoed directly after the run, never piped. pip
root-user warnings appeared on run 1 only (before `PIP_ROOT_USER_ACTION=ignore`
was added) and are elided as `[pip root-user warning]` for readability; no other
output is altered.

### Run 1 — from inside `/home/user/websites`

```
$ cd /home/user/websites && bash .../drafts/setup-env.sh; echo "EXIT_CODE=$?"
[setup-env] starting (2026-07-09T20:08:38Z)
[setup-env] python: Python 3.11.15
[setup-env] repo dir: /home/user/websites
[setup-env] git: on branch claude/winddown-queue-state at 7364917
[setup-env] installing: /home/user/websites/botsite/requirements.txt
[pip root-user warning]
[setup-env] installing: /home/user/websites/dashboard/requirements.txt
[pip root-user warning]
[setup-env] installing: /home/user/websites/requirements.txt
[pip root-user warning]
[pip root-user warning]
[setup-env] extra installed: pytest
[pip root-user warning]
[setup-env] extra installed: python-multipart

================ setup-env summary ================
python:        Python 3.11.15 (/usr/local/bin/python3)
requirements installed:
  ok   /home/user/websites/botsite/requirements.txt
  ok   /home/user/websites/dashboard/requirements.txt
  ok   /home/user/websites/requirements.txt
pytest importable: yes (9.1.1)
env vars (names only, presence check):
  present: GITHUB_TOKEN
  present: RAILWAY_API_KEY
  ABSENT:  SITE_PASSWORD
  present: DATABASE_URL
failures: none
===================================================
EXIT_CODE=0
```

### Run 2 — from an empty scratch directory

```
$ mkdir -p .../winddown/empty-scratch && cd .../winddown/empty-scratch && bash .../drafts/setup-env.sh; echo "EXIT_CODE=$?"
[setup-env] starting (2026-07-09T20:09:11Z)
[setup-env] python: Python 3.11.15
[setup-env] repo dir: /home/user/websites
[setup-env] git: on branch claude/winddown-queue-state at 7364917
[setup-env] installing: /home/user/websites/botsite/requirements.txt
[setup-env] installing: /home/user/websites/dashboard/requirements.txt
[setup-env] installing: /home/user/websites/requirements.txt
[setup-env] extra installed: pytest
[setup-env] extra installed: python-multipart

================ setup-env summary ================
python:        Python 3.11.15 (/usr/local/bin/python3)
requirements installed:
  ok   /home/user/websites/botsite/requirements.txt
  ok   /home/user/websites/dashboard/requirements.txt
  ok   /home/user/websites/requirements.txt
pytest importable: yes (9.1.1)
env vars (names only, presence check):
  present: GITHUB_TOKEN
  present: RAILWAY_API_KEY
  ABSENT:  SITE_PASSWORD
  present: DATABASE_URL
failures: none
===================================================
EXIT_CODE=0
```

(The script found the repo via its `/home/user/websites` default — the intended
behavior when run from anywhere in a standard container.)

### Run 3 — `set -u`-hostile: all four checked env vars unset, invoked `bash -u`

```
$ cd .../winddown/empty-scratch && (unset GITHUB_TOKEN RAILWAY_API_KEY SITE_PASSWORD DATABASE_URL WEBSITES_REPO_DIR; set -u; bash -u .../drafts/setup-env.sh); echo "EXIT_CODE=$?"
[setup-env] starting (2026-07-09T20:09:27Z)
[setup-env] python: Python 3.11.15
[setup-env] repo dir: /home/user/websites
[setup-env] git: on branch claude/winddown-queue-state at 7364917
[setup-env] installing: /home/user/websites/botsite/requirements.txt
[setup-env] installing: /home/user/websites/dashboard/requirements.txt
[setup-env] installing: /home/user/websites/requirements.txt
[setup-env] extra installed: pytest
[setup-env] extra installed: python-multipart

================ setup-env summary ================
python:        Python 3.11.15 (/usr/local/bin/python3)
requirements installed:
  ok   /home/user/websites/botsite/requirements.txt
  ok   /home/user/websites/dashboard/requirements.txt
  ok   /home/user/websites/requirements.txt
pytest importable: yes (9.1.1)
env vars (names only, presence check):
  ABSENT:  GITHUB_TOKEN
  ABSENT:  RAILWAY_API_KEY
  ABSENT:  SITE_PASSWORD
  ABSENT:  DATABASE_URL
failures: none
===================================================
EXIT_CODE=0
```

### Run 4 (bonus) — repo-missing branch (patched copy with a nonexistent default path)

```
$ sed 's|/home/user/websites|/nonexistent-websites|' ../drafts/setup-env.sh > patched-setup.sh && (unset WEBSITES_REPO_DIR; bash patched-setup.sh); echo "EXIT_CODE=$?"
[setup-env] starting (2026-07-09T20:09:45Z)
[setup-env] python: Python 3.11.15
[setup-env] FAIL: websites repo not found (tried $1, $WEBSITES_REPO_DIR, /nonexistent-websites, cwd) — repo-relative installs skipped
[setup-env] git: skipped (no repo dir or no git binary)
[setup-env] no requirements*.txt files found — skipping requirements installs
[setup-env] extra installed: pytest
[setup-env] extra installed: python-multipart

================ setup-env summary ================
python:        Python 3.11.15 (/usr/local/bin/python3)
requirements installed: none
pytest importable: yes (9.1.1)
env vars (names only, presence check):
  present: GITHUB_TOKEN
  present: RAILWAY_API_KEY
  ABSENT:  SITE_PASSWORD
  present: DATABASE_URL
failures (1) — setup still exits 0, read these:
  ! websites repo not found (tried $1, $WEBSITES_REPO_DIR, /nonexistent-websites, cwd) — repo-relative installs skipped
===================================================
EXIT_CODE=0
```

**Result: exit code 0 in all runs (1, 2, 3, and bonus 4); failures are printed,
never fatal.**

## 5. Known limits of this spec (what was NOT verified)

- The detached-HEAD reporting branch was not exercised in the test runs (the
  wind-down clone was already on a branch); the code path is guarded (`rev-parse`
  fallbacks + `|| true`) but its output line is unproven.
- Runs were performed in a container where deps were already partially installed;
  the "fresh container lacks pytest" fact is first-hand from earlier in the
  wind-down session (dossier §3.15a), but the script's very-first-run timing on a
  truly cold container was not measured.
- The fleet-manager reference pattern (`environments/templates/setup-universal.sh`)
  was unreachable (§3) — no diff against it was possible.
- Live Railway API reachability and the three site URLs were not re-probed by
  this docs-only worker; facts in §3 are from the committed gen-1 record.
