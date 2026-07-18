"""Static scan of the env-var NAMES each service's code references.

Build-time generator (the review/gen_*.py idiom): parses the source of all
four services with the ``ast`` module and records the env-var NAME string
literals each service reads at runtime, into the committed names-only snapshot
``app/data/env_coderefs.json``. The running control-plane reads THAT snapshot
(``app/codedrift.py``); it never scans source at request time — the deployed
control-plane image ships only ``app/`` (``COPY app ./app``), so a runtime scan
of the other three services' source would silently see nothing. The snapshot is
pinned fresh by ``tests/test_env_coderefs_snapshot.py`` — add an env read
without regenerating and the build fails.

NAMES ONLY: this records env-var name strings the code passes to an env read.
It never reads a value, never runs the scanned code, never touches the network.

Three reference shapes are resolved (verified against the real source):

1. Direct literal — ``os.getenv("X")`` / ``os.environ.get("X")`` /
   ``os.environ["X"]``.
2. Helper-wrapped literal — ``_env_int("X", default)`` and any ``_env*``
   reader wrapper: the NAME is the wrapper's first string argument.
3. Module-constant indirection — ``ENV_API_KEY = "X"`` then
   ``os.environ.get(ENV_API_KEY)``: the ``Name`` argument is resolved back to
   its assigned string literal (per file).

Everything captured must match the env-var NAME shape (``^[A-Z][A-Z0-9_]+$``),
which also keeps non-env upper-snake noise and lowercase locals out (so e.g.
``extract_env(meta_text)`` or ``_envelope_reason(res)`` contribute nothing).

Run ``python3 -m app.gen_env_coderefs`` (or ``--check`` to verify freshness
without writing) from the repo root.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

# package dir -> the service name used in app/railway.py SERVICES.
SERVICE_PACKAGES: dict[str, str] = {
    "app": "control-plane",
    "botsite": "botsite",
    "dashboard": "dashboard",
    "review": "review",
}

# Repo root = parent of this file's package (app/).
REPO_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = REPO_ROOT / "app" / "data" / "env_coderefs.json"

# An env-var NAME: an upper-snake token (>= 2 chars). Filters lowercase locals
# and single-word junk so only real env-name-shaped strings survive.
_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")


def _is_env_name(s: Any) -> bool:
    return isinstance(s, str) and bool(_NAME_RE.match(s))


def _is_os_environ(node: ast.AST) -> bool:
    """True for the ``os.environ`` attribute expression."""
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "environ"
        and isinstance(node.value, ast.Name)
        and node.value.id == "os"
    )


def _is_env_read_call(func: ast.AST) -> bool:
    """Callables that read the environment by a NAME argument:

    ``os.getenv(...)``, ``os.environ.get(...)``, and any local ``_env*`` reader
    wrapper (e.g. ``_env_int``). The upper-snake shape filter on the resolved
    argument keeps false ``_env*`` matches (``_envelope_reason``) harmless.
    """
    if isinstance(func, ast.Attribute):
        # os.getenv(...)
        if func.attr == "getenv" and isinstance(func.value, ast.Name) and func.value.id == "os":
            return True
        # os.environ.get(...)
        if func.attr == "get" and _is_os_environ(func.value):
            return True
        return False
    if isinstance(func, ast.Name):
        return func.id.startswith("_env")
    return False


def _const_map(tree: ast.AST) -> dict[str, str]:
    """Per-file ``NAME = "literal"`` map, for module-constant indirection."""
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            val = node.value.value
            if isinstance(val, str):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        out[tgt.id] = val
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Constant):
            val = node.value.value
            if isinstance(val, str) and isinstance(node.target, ast.Name):
                out[node.target.id] = val
    return out


def _resolve(expr: ast.AST | None, consts: dict[str, str]) -> str | None:
    """A NAME-argument expression to its string value, resolving a ``Name``
    back through the file's constant map. Returns ``None`` if not a string."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value
    if isinstance(expr, ast.Name):
        return consts.get(expr.id)
    return None


def names_in_source(source: str) -> set[str]:
    """Env-var NAMES referenced in one module's source (pure; no I/O)."""
    tree = ast.parse(source)
    consts = _const_map(tree)
    found: set[str] = set()
    for node in ast.walk(tree):
        # os.environ["X"]
        if isinstance(node, ast.Subscript) and _is_os_environ(node.value):
            name = _resolve(node.slice, consts)
            if _is_env_name(name):
                found.add(name)  # type: ignore[arg-type]
        # os.getenv(...) / os.environ.get(...) / _env*(...)
        elif isinstance(node, ast.Call) and node.args and _is_env_read_call(node.func):
            name = _resolve(node.args[0], consts)
            if _is_env_name(name):
                found.add(name)  # type: ignore[arg-type]
    return found


def scan_service(pkg: str) -> list[str]:
    """Sorted env-var NAMES referenced by a service's package, tests excluded.

    ``tests/`` and ``gen_*.py`` are excluded on purpose: the deployed service
    is the runtime code, not its test suite (a fixture's
    ``monkeypatch.setenv`` is not config the deploy needs) nor its build-time
    data generators (``review/gen_questions.py`` reads ``GITHUB_TOKEN`` in CI,
    but that is never a review DEPLOY var — it belongs to the generator, not
    the running service, and the manifest is per-deployed-service). Unparseable
    files are skipped (a syntax error is not this scan's job to report).
    """
    names: set[str] = set()
    for path in sorted((REPO_ROOT / pkg).rglob("*.py")):
        parts = path.relative_to(REPO_ROOT).parts
        if "tests" in parts or path.name.startswith("gen_"):
            continue
        try:
            names |= names_in_source(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
    return sorted(names)


def build_snapshot() -> dict[str, Any]:
    """The committed snapshot payload: names-only, per service."""
    return {
        "_comment": (
            "GENERATED by app/gen_env_coderefs.py — do not hand-edit. Env-var "
            "NAMES each service's code references (static AST scan, tests "
            "excluded). Names only, never values. Regenerate: "
            "python3 -m app.gen_env_coderefs"
        ),
        "services": {
            svc: scan_service(pkg) for pkg, svc in SERVICE_PACKAGES.items()
        },
    }


def _render(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    snapshot = build_snapshot()
    rendered = _render(snapshot)
    if "--check" in argv:
        current = SNAPSHOT_PATH.read_text(encoding="utf-8") if SNAPSHOT_PATH.exists() else ""
        if current != rendered:
            print(
                "env_coderefs.json is STALE — run `python3 -m app.gen_env_coderefs`",
                file=sys.stderr,
            )
            return 1
        print("env_coderefs.json is fresh")
        return 0
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(rendered, encoding="utf-8")
    print(f"wrote {SNAPSHOT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
