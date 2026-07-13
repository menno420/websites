# 2026-07-13 — hostile-env import smoke: import every service module under a poisoned environment

> **Status:** `complete` — PR #287, branch `claude/hostile-env-smoke-0713`;
> `tests/test_hostile_env_smoke.py` imports every runtime module of all
> four services under a poisoned environment (every documented env var
> `""`, then garbage) in isolated subprocesses; zero real crash sites
> found — the PR #282/#285 hardening held; lands via the auto-merge
> enabler on green.

- **📊 Model:** Claude Fable 5 · worker · backlog-slice

**What this session was about:** backlog promotion — the captured bullet in
`docs/ideas/backlog.md` ("Hostile-env import smoke — dynamically import
every service module under a poisoned environment", 2026-07-13,
env-guard-gate session 💡, source `.sessions/2026-07-13-env-guard-gate.md`).
The static AST gate (`tests/test_env_guard_gate.py`, PR #285) only sees bare
`int()`/`float()` over env vars; this session adds the dynamic complement —
a smoke test that actually imports every module of all four services in a
subprocess whose environment sets every documented env var to `""` and to
garbage, proving no import-time crash of ANY kind.

## What was done

- `tests/test_hostile_env_smoke.py` — mirrors the env-guard gate's
  discovery (same SERVICE_DIRS, same exclusions: tests, `__pycache__`,
  `.substrate`, `bootstrap.py`, `gen_*` bakers). 38 env-var names
  collected from the PR #282 docs env tables + a full
  `os.environ`/`os.getenv` source sweep (incl. the `ENV_*` indirections
  and multiline reads); the UNION is poisoned for every service —
  strictly stronger than per-service lists and migration-proof. Two
  poison modes (`""` — on Railway an empty entry is NOT unset — and
  `"!!not-a-value!!"`), one subprocess per service per mode (8 total,
  poison passed via `subprocess.run(env=...)` so nothing leaks into
  pytest); failures name the module and carry the subprocess traceback.
  A meta-test pins discovery non-empty per service. Runtime ~4.6s.
- Result: all 62 runtime modules (app 30 / botsite 21 / dashboard 4 /
  review 7) import clean under both poisons — zero crash sites to fix,
  zero exemptions needed (`EXEMPT_MODULES` is empty by evidence, kept as
  the documented escape hatch).
- `docs/ideas/backlog.md` — source bullet flipped `captured` → `built`;
  this session's 💡 captured as a new bullet.
- Verified: `python3 -m pytest tests/ botsite/tests dashboard/tests
  review/tests -q` — 1228 passed, 1 warning (+2 over the 1226 baseline);
  `python3 bootstrap.py check --strict` — green except this card's own
  designed born-red HOLD (flipped by this commit) and the pre-existing
  never-exit-affecting `owner-action-fields` advisory on
  control/status.md (not owned here).

⚑ Self-initiated: no — backlog promotion of the hostile-env import smoke
bullet (`docs/ideas/backlog.md`, captured 2026-07-13 by the env-guard-gate
session).

## 💡 Session idea

**Self-deriving poison list — pin the smoke's ENV_VARS against a live
source sweep** — the smoke's 38-name poison list is a hand-collected
literal; a companion assertion (AST or regex sweep of
`os.environ`/`os.getenv`/`ENV_* =` over the four services at test time,
same exclusions) failing when source reads a name the list misses would
make the poison self-updating-or-loud. Worth having because a new env-var
read added tomorrow is silently unpoisoned — the exact rot class this
smoke exists to close, reopened one variable at a time. Deduped against
`docs/ideas/backlog.md` + the queue-state NEXT list: the code-vs-inventory
bullets (#227 and its per-service generalization) check env-var NAME
*documentation* completeness against docs tables; nothing pins the smoke
test's own poison list against source. Captured in `docs/ideas/backlog.md`.

## ⟲ Previous-session review

The venture-vetting-catalog session (PR #248) did well — all 22 statuses
derived from each packet's own Status blockquote and Verdict (nothing
invented) and the `test_committed_registry_is_honest` pin locks the exact
1/12/2/7 breakdown; what it missed: everything is pinned to venture-lab
@ `2c039e3` with no drift check against upstream — its own sha-drift 💡
stayed a backlog bullet, so the hand-curated registry decays silently the
moment the vetting lane moves.
