"""Hostile-env import smoke: import every service module under poison.

The dynamic complement to ``tests/test_env_guard_gate.py`` (PR #285). The
static gate only sees bare ``int()``/``float()`` over env vars — but a
module-level ``json.loads``, date parse, ``.split()[0]``, or ``Path`` read
over an env var is the same crash class (the service dies at import, before
it binds a port; on Railway an empty-string entry is NOT "unset") and is
invisible to an AST cast-scan. A real import under hostile values catches
them all.

What this does: for each of the four services (app, botsite, dashboard,
review) it enumerates every importable runtime module (same discovery and
exclusion rules as the env-guard gate) and imports ALL of them inside ONE
subprocess per service per poison mode — every documented env var set to
``""``, then every one set to ``"!!not-a-value!!"``. The poison is passed
via ``subprocess.run(..., env=...)`` so it never leaks into the running
pytest process. 4 services x 2 modes = 8 subprocesses total. A failure
names the exact module and carries the subprocess traceback.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The four independently deployed services (working agreement: architecture).
SERVICE_DIRS = ("app", "botsite", "dashboard", "review")

# Same exclusions as tests/test_env_guard_gate.py: kit machinery, tests,
# and the review/botsite gen_*.py offline bakers (run from the repo root by
# scheduled workflows; never imported by a running service).
EXCLUDED_DIR_NAMES = {".substrate", "tests", "__pycache__"}
EXCLUDED_FILE_NAMES = {"bootstrap.py"}

# Every env var the four services read, plus PORT (read by the Dockerfile
# start commands). Provenance: the docs env tables (docs/site.md §env,
# docs/botsite.md §env, docs/dashboard.md §env — updated by PR #282) plus a
# source sweep: rg 'os\.environ|os\.getenv' app botsite dashboard review
# (2026-07-13; includes the ENV_* indirections in app/writeback.py,
# app/owner_assist.py, botsite/testing_ai.py, botsite/testing_payouts.py and
# the multiline reads in botsite/data_source.py, dashboard/data_source.py,
# app/config.py). Poisoning the UNION for every service is deliberate — it
# is strictly stronger than per-service lists and cannot rot when a var
# migrates between services.
ENV_VARS = [
    # shared / injected
    "PORT",
    "RAILWAY_GIT_COMMIT_SHA",
    "GIT_SHA",
    "GITHUB_TOKEN",
    "ANTHROPIC_API_KEY",
    "SITE_PASSWORD",
    # app/ (control-plane): app/config.py, app/writeback.py,
    # app/owner_assist.py
    "GITHUB_API_BASE",
    "GITHUB_RAW_BASE",
    "RAILWAY_TOKEN",
    "CACHE_TTL_SECONDS",
    "AUTOREFRESH_SECONDS",
    "FLEET_STALE_HOURS",
    "CLAIM_STALE_HOURS",
    "OWNER_ASSIST_MODEL",
    "OWNER_ASSIST_DAILY_CAP",
    "WRITEBACK_BRANCH",
    "WRITEBACK_BRANCH_PREFIX",
    "WRITEBACK_DB_PATH",
    # botsite/: data_source.py, testing.py, testing_store.py, testing_ai.py,
    # testing_payouts.py
    "SITE_JSON_URL",
    "ADD_TO_DISCORD_URL",
    "SITE_CACHE_TTL_SECONDS",
    "TESTING_BOUNTY_CAP_USD",
    "TESTING_DB_PATH",
    "TESTING_AI_MODEL",
    "TESTING_AI_DAILY_CAP",
    "TESTING_AI_GUIDE_CAP",
    "PAYPAL_CLIENT_ID",
    "PAYPAL_CLIENT_SECRET",
    # botsite/submissions_store.py: durable /submit intake (ORDER 034 / ASK-0004)
    "DATABASE_URL",
    "TESTING_AUTOPAY_ENABLED",
    "TESTING_AUTOPAY_MIN_SCORE",
    "TESTING_PAYOUT_DAILY_CAP_USD",
    "TESTING_PAYOUT_MONTHLY_CAP_USD",
    # dashboard/: data_source.py, app.py (consolidation redirect targets)
    "DASHBOARD_JSON_URL",
    "CONSOLE_JSON_URL",
    "ARCADE_JSON_URL",
    "DATA_CACHE_TTL_SECONDS",
    "SUPERBOT_REPO",
    "SUPERBOT_REF",
    "BOTSITE_GAMES_URL",
    "REVIEW_REVIEWS_URL",
    # review/: ai.py (GITHUB_TOKEN in review/gen_stats.py is baker-only)
    "REVIEW_AI_LOG_SALT",
    "REVIEW_AI_MODEL",
]

POISON_MODES = {
    "empty": "",  # on Railway an empty entry is NOT "unset" — the #282 class
    "garbage": "!!not-a-value!!",
}

# Modules that MUST fail-fast on bad env by documented design would be
# exempted here, each with a comment citing that design. As of 2026-07-13
# there are none — every service module degrades honestly at import.
EXEMPT_MODULES: set[str] = set()

# The subprocess body: imports every module named on argv, collecting
# per-module tracebacks; prints a JSON report on stdout.
IMPORT_RUNNER = """
import importlib, json, sys, traceback
failures = {}
for name in sys.argv[1:]:
    try:
        importlib.import_module(name)
    except Exception:
        failures[name] = traceback.format_exc()
print(json.dumps(failures))
sys.exit(1 if failures else 0)
"""


def _is_excluded(path: Path) -> bool:
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.name.startswith("gen_"):
        return True  # offline baker scripts, not runtime imports
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def service_modules(service: str) -> list[str]:
    """Dotted module names for every importable runtime .py in a service."""
    out: list[str] = []
    for path in sorted((REPO_ROOT / service).rglob("*.py")):
        rel = path.relative_to(REPO_ROOT)
        if _is_excluded(rel):
            continue
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        name = ".".join(parts)
        if name and name not in EXEMPT_MODULES:
            out.append(name)
    return out


def _poisoned_env(value: str) -> dict[str, str]:
    """The parent env (interpreter needs PATH & friends) with every
    collected env var overridden to the poison value. Passed to the
    subprocess only — the running pytest process is never touched."""
    env = dict(os.environ)
    for name in ENV_VARS:
        env[name] = value
    return env


def _run_imports(modules: list[str], env: dict[str, str]) -> dict[str, str]:
    """Import all modules in one subprocess; return {module: traceback}."""
    proc = subprocess.run(
        [sys.executable, "-c", IMPORT_RUNNER, *modules],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        # The interpreter itself died before the runner could report —
        # surface everything we have.
        return {
            "<runner crashed>": (
                f"exit {proc.returncode}\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        }


def test_module_discovery_sees_all_four_services():
    """Meta-test: a refactor can't silently blank the smoke."""
    for service in SERVICE_DIRS:
        mods = service_modules(service)
        assert mods, f"{service}: discovered zero modules — exclusions broken?"
        assert service in mods  # the package itself imports too


def test_every_service_imports_under_hostile_env():
    failures: list[str] = []
    for service in SERVICE_DIRS:
        modules = service_modules(service)
        for mode, value in POISON_MODES.items():
            bad = _run_imports(modules, _poisoned_env(value))
            for name, tb in bad.items():
                failures.append(
                    f"--- {service} · poison={mode!r} ({value!r}) · "
                    f"module {name} ---\n{tb}"
                )
    assert not failures, (
        "import-time crash under a hostile environment — this kills the "
        "service on Railway before it binds a port (the PR #282 crash "
        "class; the static gate tests/test_env_guard_gate.py cannot see "
        "non-int()/float() parses). Guard the parse like _env_int in "
        "app/config.py or move it inside a function:\n\n"
        + "\n".join(failures)
    )
