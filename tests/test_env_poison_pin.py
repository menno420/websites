"""Self-deriving poison-list pin: the hostile-env smoke can't rot silently.

``tests/test_hostile_env_smoke.py`` (PR #287) poisons a hand-collected
``ENV_VARS`` literal. A new env-var read added to any service AFTER that
sweep is silently unpoisoned — the exact rot class the smoke exists to
close, reopened one variable at a time (`docs/ideas/backlog.md`, captured
2026-07-13 from the hostile-env-smoke session 💡).

This pin makes the list self-updating-or-loud: an AST sweep over the same
files the smoke discovers (identical service dirs + exclusion rules,
imported from the smoke module — one source of truth) derives every
env-var NAME the source actually reads, and fails BY NAME when
``ENV_VARS`` misses one. Covered read shapes:

- literal reads — ``os.environ.get("X")`` / ``os.environ["X"]`` /
  ``os.getenv("X")`` / ``"X" in os.environ`` (plus ``pop``/``setdefault``
  and the ``from os import environ, getenv`` spellings);
- module-constant indirection — ``ENV_MODEL = "TESTING_AI_MODEL"`` then
  ``os.environ.get(ENV_MODEL)`` (the app/owner_assist.py /
  botsite/testing_ai.py pattern);
- guarded-wrapper indirection — a function whose PARAMETER feeds the
  environ read (``_env_int(name, default)``) marks that function as a
  wrapper, and every literal name at its call sites is collected too;
- anything else is a DYNAMIC read that must sit on the explicit,
  per-entry-justified allowlist below (with a stale-entry check, per the
  #225/#233 allowlist convention) — never silently skipped.

The pin is one-directional on purpose: source reads ⊆ ENV_VARS. The list
may poison MORE than the source reads (``PORT`` is read by the Dockerfile
start commands, not Python).
"""

from __future__ import annotations

import ast
from pathlib import Path

from test_hostile_env_smoke import (  # one source of truth, by design
    ENV_VARS,
    REPO_ROOT,
    SERVICE_DIRS,
    _is_excluded,
)

# --- dynamic-read allowlist ------------------------------------------------
# (relative path, innermost enclosing function) -> why a non-derivable name
# is legitimate there. Every entry must match at least one found dynamic
# read (stale entries fail), and every dynamic read must have an entry.
DYNAMIC_READ_ALLOWLIST: dict[tuple[str, str], str] = {
    ("app/railway.py", "_committed_services"): (
        "presence-only read (bool(...)) of names data-driven from the "
        "committed railway.SERVICES inventory at request time; the value is "
        "never parsed, so poison coverage is not required, and the names "
        "themselves are pinned to the documented inventories by "
        "tests/test_inventory_consistency.py"
    ),
}


def _is_env_expr(node: ast.AST) -> bool:
    """True for ``os.environ`` / bare ``environ`` (from-import spelling)."""
    if isinstance(node, ast.Attribute) and node.attr == "environ":
        return True
    return isinstance(node, ast.Name) and node.id == "environ"


def _name_expr_of_read(node: ast.AST) -> ast.AST | None:
    """The expression carrying the env-var NAME if ``node`` is a
    single-name environment read, else None. Whole-env uses
    (``{**os.environ}``, ``dict(os.environ)``) carry no name and are
    intentionally not name-reads."""
    if isinstance(node, ast.Call):
        f = node.func
        if (
            isinstance(f, ast.Attribute)
            and f.attr in ("get", "pop", "setdefault")
            and _is_env_expr(f.value)
        ):
            return node.args[0] if node.args else None
        if (isinstance(f, ast.Attribute) and f.attr == "getenv") or (
            isinstance(f, ast.Name) and f.id == "getenv"
        ):
            return node.args[0] if node.args else None
    if isinstance(node, ast.Subscript) and _is_env_expr(node.value):
        return node.slice
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and isinstance(node.ops[0], (ast.In, ast.NotIn))
        and any(_is_env_expr(c) for c in node.comparators)
    ):
        return node.left
    return None


def _param_position(fn: ast.AST, name: str) -> tuple[int | None, str] | None:
    """(positional index or None-for-kwonly, param name) if ``name`` is a
    parameter of function node ``fn``."""
    a = fn.args
    positional = [p.arg for p in (*a.posonlyargs, *a.args)]
    if name in positional:
        return (positional.index(name), name)
    if name in [p.arg for p in a.kwonlyargs]:
        return (None, name)
    return None


def scan_module(source: str, relpath: str) -> dict:
    """Sweep one module.

    Returns ``{"names": [(env_name, site)], "dynamic": [(key, site)],
    "wrappers": {fn_name: (pos, param_name)}}`` where ``site`` is
    ``relpath:lineno`` and ``key`` is the allowlist key tuple.
    """
    tree = ast.parse(source)
    consts: dict[str, str] = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
            if isinstance(stmt.value.value, str):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name):
                        consts[tgt.id] = stmt.value.value
        if (
            isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        ):
            consts[stmt.target.id] = stmt.value.value

    names: list[tuple[str, str]] = []
    dynamic: list[tuple[tuple[str, str], str]] = []
    wrappers: dict[str, tuple[int | None, str]] = {}

    def enclosing_name(fn_stack: list[ast.AST]) -> str:
        for fn in reversed(fn_stack):
            got = getattr(fn, "name", None)
            if got:
                return got
        return "<module>"

    def record(name_expr: ast.AST, fn_stack: list[ast.AST]) -> None:
        site = f"{relpath}:{name_expr.lineno}"
        if isinstance(name_expr, ast.Constant) and isinstance(name_expr.value, str):
            names.append((name_expr.value, site))
            return
        if isinstance(name_expr, ast.Name):
            if name_expr.id in consts:
                names.append((consts[name_expr.id], site))
                return
            # A parameter of an enclosing NAMED function marks a wrapper:
            # its call sites are swept for literal names instead.
            for fn in reversed(fn_stack):
                if not getattr(fn, "name", None):
                    continue  # lambda wrapper = dynamic, stays loud below
                spot = _param_position(fn, name_expr.id)
                if spot is not None:
                    wrappers[fn.name] = spot
                    return
        dynamic.append(((relpath, enclosing_name(fn_stack)), site))

    def visit(node: ast.AST, fn_stack: list[ast.AST]) -> None:
        name_expr = _name_expr_of_read(node)
        if name_expr is not None:
            record(name_expr, fn_stack)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            fn_stack = fn_stack + [node]
        for child in ast.iter_child_nodes(node):
            visit(child, fn_stack)

    visit(tree, [])

    # Wrapper call sites: collect the literal name each call passes.
    if wrappers:

        def visit_calls(node: ast.AST, fn_stack: list[ast.AST]) -> None:
            if isinstance(node, ast.Call):
                f = node.func
                fname = f.id if isinstance(f, ast.Name) else (
                    f.attr if isinstance(f, ast.Attribute) else None
                )
                if fname in wrappers:
                    pos, pname = wrappers[fname]
                    arg: ast.AST | None = None
                    if pos is not None and pos < len(node.args):
                        arg = node.args[pos]
                    else:
                        for kw in node.keywords:
                            if kw.arg == pname:
                                arg = kw.value
                    if arg is not None:
                        record(arg, fn_stack)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                fn_stack = fn_stack + [node]
            for child in ast.iter_child_nodes(node):
                visit_calls(child, fn_stack)

        visit_calls(tree, [])

    return {"names": names, "dynamic": dynamic, "wrappers": wrappers}


def _service_sources() -> list[Path]:
    out: list[Path] = []
    for service in SERVICE_DIRS:
        for path in sorted((REPO_ROOT / service).rglob("*.py")):
            if not _is_excluded(path.relative_to(REPO_ROOT)):
                out.append(path)
    return out


def _sweep() -> tuple[list[tuple[str, str]], list[tuple[tuple[str, str], str]]]:
    names: list[tuple[str, str]] = []
    dynamic: list[tuple[tuple[str, str], str]] = []
    for path in _service_sources():
        rel = str(path.relative_to(REPO_ROOT))
        result = scan_module(path.read_text(encoding="utf-8"), rel)
        names.extend(result["names"])
        dynamic.extend(result["dynamic"])
    return names, dynamic


def test_poison_list_covers_every_source_read():
    names, _ = _sweep()
    assert names, "env sweep derived zero names — scanner or exclusions broken?"
    poison = set(ENV_VARS)
    missing = sorted(
        {(name, site) for name, site in names if name not in poison}
    )
    assert not missing, (
        "env-var read in service source that the hostile-env smoke does NOT "
        "poison — the import smoke silently skips it, reopening the crash "
        "class it exists to close. Add the name to ENV_VARS in "
        "tests/test_hostile_env_smoke.py:\n  "
        + "\n  ".join(f"{name}  (read at {site})" for name, site in missing)
    )


def test_sweep_sees_reads_in_every_service():
    """Meta-test: a refactor can't silently blank the sweep for a service."""
    names, _ = _sweep()
    for service in SERVICE_DIRS:
        prefix = f"{service}/"
        assert any(site.startswith(prefix) for _, site in names), (
            f"{service}: sweep derived zero env-var names — every service "
            "reads at least RAILWAY_GIT_COMMIT_SHA/GIT_SHA today, so an "
            "empty result means the scanner lost a read shape"
        )


def test_dynamic_reads_are_allowlisted_and_allowlist_is_live():
    _, dynamic = _sweep()
    found_keys = {key for key, _ in dynamic}
    unlisted = sorted(
        f"{site}  (in {key[1]})" for key, site in dynamic
        if key not in DYNAMIC_READ_ALLOWLIST
    )
    assert not unlisted, (
        "non-derivable (dynamic) env read outside the justified allowlist — "
        "the sweep cannot prove the poison list covers it. Either read a "
        "literal/module-constant name, or add a justified "
        "DYNAMIC_READ_ALLOWLIST entry in tests/test_env_poison_pin.py:\n  "
        + "\n  ".join(unlisted)
    )
    stale = sorted(
        f"{path} · {fn}" for (path, fn) in DYNAMIC_READ_ALLOWLIST
        if (path, fn) not in found_keys
    )
    assert not stale, (
        "stale DYNAMIC_READ_ALLOWLIST entry — the read it justified is gone; "
        "remove it so exemptions cannot outlive their reason:\n  "
        + "\n  ".join(stale)
    )


# --- self-tests: prove each read shape and resolution rung ---------------


def test_self_literal_shapes_resolve():
    src = (
        "import os\n"
        "from os import environ, getenv\n"
        'A = os.environ.get("A_VAR")\n'
        'B = os.environ["B_VAR"]\n'
        'C = os.getenv("C_VAR", "x")\n'
        'D = environ.get("D_VAR")\n'
        'E = getenv("E_VAR")\n'
        'F = "F_VAR" in os.environ\n'
        'G = os.environ.setdefault("G_VAR", "x")\n'
    )
    result = scan_module(src, "x.py")
    got = {name for name, _ in result["names"]}
    assert got == {f"{c}_VAR" for c in "ABCDEFG"}
    assert result["dynamic"] == []


def test_self_module_constant_indirection_resolves():
    src = (
        "import os\n"
        'ENV_MODEL = "REAL_NAME"\n'
        "def f():\n"
        "    return os.environ.get(ENV_MODEL)\n"
    )
    result = scan_module(src, "x.py")
    assert [n for n, _ in result["names"]] == ["REAL_NAME"]
    assert result["dynamic"] == []


def test_self_wrapper_call_sites_are_collected():
    src = (
        "import os\n"
        "def _env_int(name, default):\n"
        "    try:\n"
        "        return int(os.environ.get(name) or default)\n"
        "    except ValueError:\n"
        "        return default\n"
        'TTL = _env_int("TTL_VAR", 180)\n'
        'AGE = _env_int(name="AGE_VAR", default=12)\n'
    )
    result = scan_module(src, "x.py")
    assert {n for n, _ in result["names"]} == {"TTL_VAR", "AGE_VAR"}
    assert result["wrappers"] == {"_env_int": (0, "name")}
    assert result["dynamic"] == []


def test_self_dynamic_read_is_loud_with_enclosing_function():
    src = (
        "import os\n"
        "def probe(rows):\n"
        '    return [bool(os.environ.get(r["name"])) for r in rows]\n'
    )
    result = scan_module(src, "pkg/mod.py")
    assert result["names"] == []
    assert [key for key, _ in result["dynamic"]] == [("pkg/mod.py", "probe")]


def test_self_whole_env_uses_are_not_name_reads():
    src = (
        "import os\n"
        'env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}\n'
        "copy = dict(os.environ)\n"
    )
    result = scan_module(src, "x.py")
    assert result["names"] == [] and result["dynamic"] == []
