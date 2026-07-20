"""Auto-discovering vendored-copy AST core guard (plan slice 5, 2026-07-19 cycle).

This repo vendors shared modules **per service** rather than sharing them by
import — the four server-rendered FastAPI services (``app/``, ``botsite/``,
``dashboard/``, ``review/``) never import one another's packages, so a module
needed in more than one lands as a same-basename copy in each. Two such copies
already have hand-written drift guards:

* ``listfilter.py`` (``app/``, ``botsite/``, ``review/``) — a **byte-identical**
  vendored copy, pinned by ``botsite/tests/test_botsite_filters.py`` and
  ``review/tests/test_review_filters.py``.
* ``discord_auth.py`` (``app/``, ``botsite/``, ``dashboard/``) — copies that
  intentionally differ (route prefixes, redirect targets, service labels) but
  must NOT drift in their shared security core, pinned by
  ``tests/test_discord_auth_vendored.py`` (#445) via a docstring-stripped AST
  comparison of a declared function/constant core.

Each new vendored copy currently needs its own hand-written guard, and until
someone remembers to write it the copy ships uncovered. This meta-test
generalises the pattern: it **auto-discovers** every same-basename ``.py``
module living in more than one service dir and, for each group declared in the
manifest below, asserts the declared shared core stays identical across all
copies — reusing the exact idioms the two existing guards use (whole-file bytes
for byte-mode, docstring-stripped ``ast`` unparse of a symbol core for
symbol-mode).

Crucially, the discovery has teeth: ``test_no_undeclared_vendored_group``
asserts that EVERY discovered same-basename group is accounted for in the
manifest — either guarded (``VENDORED_GROUPS``) or explicitly declared a
coincidental name that is NOT a vendored copy (``KNOWN_COINCIDENTAL``). A newly
vendored module therefore reddens this test the moment it appears, instead of
drifting silently until a human writes its bespoke guard.

The existing per-module guards are intentionally left in place — this meta-test
is belt-and-suspenders over them, driven from data rather than replacing them.
"""
import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The four independent server-rendered FastAPI services (see .claude/CLAUDE.md
# "Architecture"). Vendored copies live as same-basename modules across these.
SERVICE_DIRS = ("app", "botsite", "dashboard", "review")

_FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


# --------------------------------------------------------------------------- #
# Manifest — the ONLY hand-maintained surface. A new vendored copy is guarded
# by adding one entry here; a new coincidental same-basename module is silenced
# by listing it (with its reason) in KNOWN_COINCIDENTAL. Everything else the
# meta-test derives by discovery.
# --------------------------------------------------------------------------- #

# Genuine vendored copies whose shared core must stay identical across services.
#   mode "byte"   -> the whole file must be byte-identical in every copy.
#   mode "symbol" -> only the named functions/constants form the shared core;
#                    they are compared docstring-stripped via ast.unparse, so
#                    intentional per-service differences (route paths, labels,
#                    service-only helpers) are excluded by construction.
VENDORED_GROUPS = {
    "listfilter.py": {
        "mode": "byte",
    },
    "discord_auth.py": {
        "mode": "symbol",
        # The Discord-OAuth security core: env/config readers, crypto (base64 +
        # HMAC signing), session make/verify, OAuth state make/verify, cookie
        # setting, and the token-exchange + user-fetch network calls. (Mirrors
        # tests/test_discord_auth_vendored.py — a security-relevant divergence,
        # not an intentional per-service difference.)
        "functions": (
            "_env",
            "oauth_configured",
            "_b64e",
            "_b64d",
            "_sign",
            "make_session",
            "verify_session",
            "make_state",
            "_state_signature_valid",
            "owner_session_id",
            "_is_https",
            "_set_session_cookie",
            "exchange_code",
            "fetch_user",
        ),
        # OAuth endpoints, scope, cookie names, TTLs, env-var-name constants.
        "constants": (
            "AUTHORIZE_URL",
            "TOKEN_URL",
            "USER_URL",
            "OAUTH_SCOPE",
            "SESSION_COOKIE",
            "STATE_COOKIE",
            "SESSION_TTL_SECONDS",
            "STATE_TTL_SECONDS",
            "ENV_CLIENT_ID",
            "ENV_CLIENT_SECRET",
            "ENV_OWNER_ID",
            "ENV_SESSION_SECRET",
            "ENV_REDIRECT_URI",
        ),
    },
}

# Same-basename modules that are NOT vendored copies — coincidental names that
# happen to appear in several service dirs. Each is an INDEPENDENT module with
# no shared core to guard; listing it (with why) keeps the discovery honest
# without asserting a drift contract that was never intended.
KNOWN_COINCIDENTAL = {
    "app.py": (
        "Each service's own FastAPI entrypoint (botsite/dashboard/review) — "
        "distinct applications that merely share the conventional filename; "
        "no shared core."
    ),
    "data_source.py": (
        "botsite/ and dashboard/ each have an independently-authored decoupled "
        "data layer over a different superbot feed (site.json vs "
        "dashboard.json/console.json). They share an httpx-cache plumbing core "
        "by convention but were never declared a synced vendored copy — see "
        "this session's 💡 for a possible symbol-mode promotion of just that "
        "plumbing subset."
    ),
}


# --------------------------------------------------------------------------- #
# Discovery
# --------------------------------------------------------------------------- #


def _discover_groups():
    """Map basename -> sorted list of service dirs containing that module.

    Only ``.py`` files present in MORE THAN ONE service dir count as a group;
    ``__init__.py`` (a package marker, not a vendored module) is excluded.
    """
    seen = {}
    for d in SERVICE_DIRS:
        service = REPO_ROOT / d
        if not service.is_dir():
            continue
        for path in service.glob("*.py"):
            if path.name == "__init__.py":
                continue
            seen.setdefault(path.name, []).append(d)
    return {name: sorted(dirs) for name, dirs in seen.items() if len(dirs) > 1}


DISCOVERED = _discover_groups()


# --------------------------------------------------------------------------- #
# AST helpers — the discord_auth-guard idiom, reused verbatim so symbol-mode
# comparison is identical to the hand-written guard it generalises.
# --------------------------------------------------------------------------- #


def _module(path):
    return ast.parse(path.read_text())


def _strip_leading_docstring(body):
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _function_source(path, func):
    for node in ast.walk(_module(path)):
        if isinstance(node, _FUNC_TYPES) and node.name == func:
            node.body = _strip_leading_docstring(node.body)
            return ast.unparse(node)
    return None


def _constant_source(path, const):
    for node in _module(path).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == const for t in node.targets
        ):
            return ast.unparse(node)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == const
        ):
            return ast.unparse(node)
    return None


def _copies(basename):
    """Absolute paths of every discovered copy of ``basename``, dir-sorted."""
    return {d: REPO_ROOT / d / basename for d in DISCOVERED[basename]}


# --------------------------------------------------------------------------- #
# Parametrization case lists (built at import time from discovery + manifest)
# --------------------------------------------------------------------------- #

_BYTE_GROUPS = [
    name
    for name, cfg in VENDORED_GROUPS.items()
    if cfg["mode"] == "byte" and name in DISCOVERED
]

_SYMBOL_FUNC_CASES = [
    (name, func)
    for name, cfg in VENDORED_GROUPS.items()
    if cfg["mode"] == "symbol" and name in DISCOVERED
    for func in cfg.get("functions", ())
]

_SYMBOL_CONST_CASES = [
    (name, const)
    for name, cfg in VENDORED_GROUPS.items()
    if cfg["mode"] == "symbol" and name in DISCOVERED
    for const in cfg.get("constants", ())
]


# --------------------------------------------------------------------------- #
# Discovery has teeth: every discovered group must be accounted for.
# --------------------------------------------------------------------------- #


def test_no_undeclared_vendored_group():
    """A newly vendored same-basename module must be classified, not ignored.

    Every module discovered in more than one service dir has to be either a
    guarded vendored group (``VENDORED_GROUPS``) or an explicitly-declared
    coincidental name (``KNOWN_COINCIDENTAL``). Anything else is a new vendored
    copy shipping without drift coverage — decide which it is and add the
    one-line manifest entry.
    """
    undeclared = {
        name: dirs
        for name, dirs in DISCOVERED.items()
        if name not in VENDORED_GROUPS and name not in KNOWN_COINCIDENTAL
    }
    assert not undeclared, (
        "Same-basename module(s) found across service dirs but not classified "
        f"in tests/test_vendored_core_guard.py: {undeclared}. If it is a "
        "genuine vendored copy, add a VENDORED_GROUPS entry declaring its "
        "shared core (byte- or symbol-mode); if the shared name is "
        "coincidental, add it to KNOWN_COINCIDENTAL with the reason."
    )


def test_manifest_entries_are_live():
    """Declared basenames must actually exist as multi-dir groups.

    Guards against a stale manifest: if a vendored copy (or a coincidental
    name) stops appearing in more than one service dir, its entry is dead and
    should be removed so the manifest keeps describing the real tree.
    """
    declared = set(VENDORED_GROUPS) | set(KNOWN_COINCIDENTAL)
    stale = sorted(name for name in declared if name not in DISCOVERED)
    assert not stale, (
        "Manifest declares basename(s) that are no longer vendored across "
        f"multiple service dirs: {stale}. Remove the dead entry."
    )


# --------------------------------------------------------------------------- #
# Byte-mode: whole-file identity (the listfilter contract).
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not _BYTE_GROUPS, reason="no byte-mode vendored groups")
@pytest.mark.parametrize("basename", _BYTE_GROUPS)
def test_byte_vendored_group_is_identical(basename):
    copies = _copies(basename)
    dirs = sorted(copies)
    ref_dir = dirs[0]
    ref_bytes = copies[ref_dir].read_bytes()
    for d in dirs[1:]:
        assert copies[d].read_bytes() == ref_bytes, (
            f"{d}/{basename} must stay a byte-identical vendored copy of "
            f"{ref_dir}/{basename} — update every copy together."
        )


# --------------------------------------------------------------------------- #
# Symbol-mode: a declared function/constant core stays AST-identical, while
# intentional per-service differences are excluded by construction (only the
# named symbols are compared).
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(not _SYMBOL_FUNC_CASES, reason="no symbol-mode functions")
@pytest.mark.parametrize("basename,func", _SYMBOL_FUNC_CASES)
def test_symbol_core_function_does_not_drift(basename, func):
    copies = _copies(basename)
    dirs = sorted(copies)
    ref_dir = dirs[0]
    sources = {d: _function_source(copies[d], func) for d in dirs}
    for d in dirs:
        assert sources[d] is not None, (
            f"{d}/{basename} is missing the shared-core function {func!r} — "
            "the vendored copies have structurally drifted."
        )
    for d in dirs[1:]:
        assert sources[d] == sources[ref_dir], (
            f"{d}/{basename} has drifted from {ref_dir}/{basename} in the "
            f"shared-core function {func!r}. This symbol is part of the "
            "declared vendored core and must stay identical across every "
            "copy — patch them together."
        )


@pytest.mark.skipif(not _SYMBOL_CONST_CASES, reason="no symbol-mode constants")
@pytest.mark.parametrize("basename,const", _SYMBOL_CONST_CASES)
def test_symbol_core_constant_does_not_drift(basename, const):
    copies = _copies(basename)
    dirs = sorted(copies)
    ref_dir = dirs[0]
    sources = {d: _constant_source(copies[d], const) for d in dirs}
    for d in dirs:
        assert sources[d] is not None, (
            f"{d}/{basename} is missing the shared-core constant {const!r}."
        )
    for d in dirs[1:]:
        assert sources[d] == sources[ref_dir], (
            f"{d}/{basename} has drifted from {ref_dir}/{basename} in the "
            f"shared-core constant {const!r} — keep the vendored core in sync."
        )
