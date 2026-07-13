"""Env-guard gate: no module-level bare int()/float() over env vars.

Crash class this gate exists for: a module-level
``int(os.environ.get("X", "180"))`` executes AT IMPORT TIME, so a bad or
empty env value (on Railway an empty-string entry is NOT "unset") kills the
whole service before it binds a port — only ever caught in prod. PR #282
fixed the four control-plane sites by hand via ``_env_int`` in
``app/config.py``; this gate makes the pattern unshippable so it can never
re-enter any of the four services.

The rule: ``int(...)`` / ``float(...)`` whose argument expression involves
``os.environ`` / ``os.getenv`` is flagged when it executes at import time —
module scope, top-level ``if``/``try``/``with`` blocks, class bodies, and
function default arguments / decorators. Inside a function or method BODY it
is exempt: the call runs lazily at request time and can be guarded (that is
exactly what makes ``_env_int``-guarded sites pass).

Fix for a flagged site: wrap it in a guarded helper — see ``_env_int`` in
``app/config.py`` (empty/unset/garbage all fall back to the default) — or
move the parse inside a function.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The four independently deployed services (working agreement: architecture).
SERVICE_DIRS = ("app", "botsite", "dashboard", "review")

# Kit machinery + non-runtime code, per the repo's search-hygiene convention
# (`--exclude=bootstrap.py --exclude-dir=.substrate`) plus tests dirs and the
# review service's offline bakers (review/gen_*.py run from the repo root by
# a scheduled workflow; they are never imported by a running service).
EXCLUDED_DIR_NAMES = {".substrate", "tests", "__pycache__"}
EXCLUDED_FILE_NAMES = {"bootstrap.py"}


def _is_excluded(path: Path) -> bool:
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.name.startswith("gen_"):
        return True  # offline baker scripts, not runtime imports
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def _service_sources() -> list[Path]:
    out: list[Path] = []
    for service in SERVICE_DIRS:
        for path in sorted((REPO_ROOT / service).rglob("*.py")):
            if not _is_excluded(path.relative_to(REPO_ROOT)):
                out.append(path)
    return out


def _touches_env(node: ast.AST) -> bool:
    """True if the expression subtree involves os.environ / os.getenv
    (covers ``from os import environ, getenv`` spellings too)."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr in ("environ", "getenv"):
            return True
        if isinstance(sub, ast.Name) and sub.id in ("environ", "getenv"):
            return True
    return False


def _bare_env_cast(node: ast.AST) -> bool:
    """True for an ``int(...)``/``float(...)`` call whose arguments involve
    the environment."""
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in ("int", "float")
    ):
        return False
    exprs = [*node.args, *(kw.value for kw in node.keywords)]
    return any(_touches_env(e) for e in exprs)


def _import_time_violations(tree: ast.AST) -> list[ast.Call]:
    """Walk only the parts of the tree that execute at import time.

    Descends through every statement EXCEPT function/lambda bodies. For
    function defs, decorators / argument defaults / annotations still run at
    import, so those subtrees are scanned. Class bodies execute at import and
    are descended fully (their methods hit the function-def rule).
    """
    found: list[ast.Call] = []

    def scan_expr(node: ast.AST) -> None:
        if isinstance(node, ast.Lambda):
            # lambda BODY is lazy; its argument defaults still run at import
            a = node.args
            for default in [*a.defaults, *[d for d in a.kw_defaults if d]]:
                scan_expr(default)
            return
        if _bare_env_cast(node):
            found.append(node)
        for child in ast.iter_child_nodes(node):
            scan_expr(child)

    def scan_stmts(stmts: list[ast.stmt]) -> None:
        for stmt in stmts:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # body is lazy; decorators + defaults + annotations are not
                for dec in stmt.decorator_list:
                    scan_expr(dec)
                a = stmt.args
                for default in [*a.defaults, *[d for d in a.kw_defaults if d]]:
                    scan_expr(default)
                continue
            if isinstance(stmt, ast.ClassDef):
                for dec in stmt.decorator_list:
                    scan_expr(dec)
                for base in stmt.bases:
                    scan_expr(base)
                scan_stmts(stmt.body)
                continue
            # Compound statements whose bodies still run at import.
            for attr in ("body", "orelse", "finalbody"):
                inner = getattr(stmt, attr, None)
                if isinstance(inner, list) and inner and isinstance(inner[0], ast.stmt):
                    scan_stmts(inner)
            for handler in getattr(stmt, "handlers", []) or []:
                scan_stmts(handler.body)
            # Expressions hanging off the statement itself (assign values,
            # if/while tests, with items, return/expr values, ...).
            for child in ast.iter_child_nodes(stmt):
                if not isinstance(child, ast.stmt) and not isinstance(
                    child, ast.excepthandler
                ):
                    scan_expr(child)
    scan_stmts(tree.body)
    return found


def scan_source(source: str, label: str) -> list[str]:
    """Return 'label:lineno  <source line>' for each import-time bare
    int()/float() over env vars in the given source text."""
    tree = ast.parse(source)
    lines = source.splitlines()
    out = []
    for call in _import_time_violations(tree):
        src = lines[call.lineno - 1].strip() if call.lineno <= len(lines) else "?"
        out.append(f"{label}:{call.lineno}  {src}")
    return out


def test_no_module_level_bare_env_casts():
    violations: list[str] = []
    scanned = 0
    for path in _service_sources():
        rel = path.relative_to(REPO_ROOT)
        violations.extend(
            scan_source(path.read_text(encoding="utf-8"), str(rel))
        )
        scanned += 1
    assert scanned > 0, "env-guard gate scanned zero files — exclusions broken?"
    assert not violations, (
        "module-level bare int()/float() over env vars — this executes at "
        "IMPORT TIME, so a bad/empty env value crashes the service before it "
        "binds a port (the PR #282 crash class). Wrap it in a guarded helper "
        "like _env_int in app/config.py, or move the parse inside a "
        "function:\n  " + "\n  ".join(violations)
    )


# --- self-test: prove the scanner catches the seeded pattern -------------

SEEDED_VIOLATION = 'import os\nPORT = int(os.environ.get("PORT", "8080"))\n'

GUARDED_OK = (
    "import os\n"
    "def _env_int(name, default):\n"
    "    try:\n"
    '        return int(os.environ.get(name) or default)\n'
    "    except ValueError:\n"
    "        return default\n"
    'PORT = _env_int("PORT", 8080)\n'
)


def test_self_seeded_violation_is_caught(tmp_path):
    fixture = tmp_path / "seeded.py"
    fixture.write_text(SEEDED_VIOLATION, encoding="utf-8")
    hits = scan_source(fixture.read_text(encoding="utf-8"), "seeded.py")
    assert hits == ['seeded.py:2  PORT = int(os.environ.get("PORT", "8080"))']


def test_self_guarded_pattern_passes():
    assert scan_source(GUARDED_OK, "guarded.py") == []


def test_self_import_time_reach():
    """Top-level if/try bodies and function defaults still run at import;
    function bodies do not (meta-test so a refactor can't blunt the scan)."""
    in_if = 'import os\nif True:\n    N = int(os.getenv("N", "1"))\n'
    in_try = (
        "import os\ntry:\n    pass\nexcept Exception:\n"
        '    N = float(os.environ["N"])\n'
    )
    in_default = 'import os\ndef f(n=int(os.getenv("N", "1"))):\n    return n\n'
    in_body = 'import os\ndef f():\n    return int(os.getenv("N", "1"))\n'
    assert len(scan_source(in_if, "x")) == 1
    assert len(scan_source(in_try, "x")) == 1
    assert len(scan_source(in_default, "x")) == 1
    assert scan_source(in_body, "x") == []


def test_self_env_spellings_covered():
    """os.environ[...], os.getenv, and from-import spellings all flag."""
    cases = [
        'import os\nA = int(os.environ["A"])\n',
        'import os\nA = float(os.getenv("A", "1.0"))\n',
        'from os import environ\nA = int(environ.get("A", "1"))\n',
        'from os import getenv\nA = int(getenv("A", "1"))\n',
    ]
    for src in cases:
        assert len(scan_source(src, "x")) == 1, src
    # plain literals stay clean
    assert scan_source("A = int('5')\n", "x") == []
