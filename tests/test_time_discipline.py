"""Time-discipline guard: age-measuring entry points must get a frozen now.

Incident this guard exists for: on 2026-07-11T08:45:00Z,
``test_overview_sorts_stranded_landing_above_healthy_and_counts`` started
failing on an UNTOUCHED tree — it called ``fleet.overview()`` without a
frozen ``now``, so the fixtures' fixed ``updated:`` stamps were measured
against the real wall clock; the moment the plain lane crossed
``FLEET_STALE_HOURS`` the attention sort flipped. Green for days, then a
mystery-red quality run with nothing in any diff — the exact failure class
that detonates inside unattended routine-fired sessions.

The guard: statically scan every test module in ``tests/`` and require
that every direct call to an age-measuring entry point passes a ``now``
keyword. All of these functions take an injectable ``now=`` (the module
convention); a test with fixed timestamp fixtures that omits it is a time
bomb by construction, even if it passes today.

Adding a new age-measuring function? Add it to ``GUARDED`` here in the
same PR that introduces it.
"""

import ast
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS_DIR.parent))

# (module alias, function name) pairs whose calls must carry a `now` kwarg.
# Aliases cover the import styles used in this suite: `from app import
# fleet, orders` (attribute calls) and `from app.fleet import freshness`
# (bare-name calls).
GUARDED = {
    ("fleet", "overview"),
    ("fleet", "lane_status"),
    ("fleet", "freshness"),
    ("fleet", "heartbeat_freshness"),
    ("freshness", "overview"),
    ("orders", "overview"),
    ("orders", "classify_order"),
}
GUARDED_BARE = {name for _, name in GUARDED}


def _call_target(call: ast.Call):
    """(module, name) for `mod.fn(...)`, (None, name) for `fn(...)`."""
    fn = call.func
    if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
        return fn.value.id, fn.attr
    if isinstance(fn, ast.Name):
        return None, fn.id
    return None, None


def _has_now_kwarg(call: ast.Call) -> bool:
    return any(kw.arg == "now" for kw in call.keywords)


def _violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        mod, name = _call_target(node)
        guarded = (
            (mod, name) in GUARDED
            or (mod is None and name in GUARDED_BARE)
        )
        if guarded and not _has_now_kwarg(node):
            out.append(f"{path.name}:{node.lineno} {mod or ''}.{name}(...)")
    return out


def test_age_measuring_calls_pass_frozen_now():
    violations = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue  # this guard file only names the functions in strings
        violations.extend(_violations_in(path))
    assert not violations, (
        "time-bomb risk: age-measuring call(s) without a frozen now= "
        "(fixed fixture stamps measured against the wall clock WILL flip "
        "when they cross the stale threshold — see the 2026-07-11T08:45Z "
        "incident in this file's docstring):\n  " + "\n  ".join(violations)
    )


def test_guard_catches_a_missing_now():
    """The guard itself works: an offending snippet is flagged, a fixed one
    is clean (meta-test so a refactor can't silently blunt the scan)."""
    bad = ast.parse("import x\nfleet.overview(refresh=True)\n")
    good = ast.parse("fleet.overview(now=NOW)\nfreshness('x', now=NOW)\n")

    def scan(tree):
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                mod, name = _call_target(node)
                if (
                    (mod, name) in GUARDED
                    or (mod is None and name in GUARDED_BARE)
                ) and not _has_now_kwarg(node):
                    found.append(name)
        return found

    assert scan(bad) == ["overview"]
    assert scan(good) == []
