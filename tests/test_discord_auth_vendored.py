"""Drift guard for the per-service vendored copies of ``discord_auth.py``.

The Discord OAuth module is vendored into each service (app/, botsite/,
dashboard/) rather than shared by import — that is the repo's per-service
vendoring pattern (see the ``listfilter.py`` byte-identity guards in
``review/tests`` and ``botsite/tests``). Unlike listfilter, these copies are
NOT byte-identical: each service intentionally differs in route prefixes,
redirect targets, template names, service-label error text, and a couple of
service-only helpers (dashboard's ``actor_for``/``require_owner``, the
control-plane's nav wiring).

What must NOT drift is the shared security core: the OAuth/crypto/session
logic. This guard normalizes away docstrings and asserts the shared
constants and the shared security-core functions are identical across all
three copies. If someone patches a crypto/session bug in one copy and forgets
the others, this fails. The intentional per-service pieces are excluded by
construction — only the names in SHARED_FUNCTIONS / SHARED_CONSTANTS are
compared.
"""
import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

COPIES = {
    "app": REPO_ROOT / "app" / "discord_auth.py",
    "botsite": REPO_ROOT / "botsite" / "discord_auth.py",
    "dashboard": REPO_ROOT / "dashboard" / "discord_auth.py",
}

# The shared security core: env/config readers, crypto (base64 + HMAC signing),
# session make/verify, OAuth state make/verify, cookie setting, and the OAuth
# token-exchange + user-fetch network calls. These bodies are identical across
# all three copies once docstrings are stripped; any divergence is a
# security-relevant drift, not an intentional per-service difference.
SHARED_FUNCTIONS = (
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
)

# Module-level constants that must match across all copies: OAuth endpoints,
# scope, cookie names, TTLs, and the env-var-name constants.
SHARED_CONSTANTS = (
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
)

_FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _module(name):
    return ast.parse(COPIES[name].read_text())


def _strip_leading_docstring(body):
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


def _function_source(name, func):
    for node in ast.walk(_module(name)):
        if isinstance(node, _FUNC_TYPES) and node.name == func:
            node.body = _strip_leading_docstring(node.body)
            return ast.unparse(node)
    return None


def _constant_source(name, const):
    for node in _module(name).body:
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


@pytest.mark.parametrize("func", SHARED_FUNCTIONS)
def test_shared_security_function_does_not_drift(func):
    sources = {name: _function_source(name, func) for name in COPIES}
    for name, src in sources.items():
        assert src is not None, (
            f"{name}/discord_auth.py is missing the shared security function "
            f"{func!r} — the vendored copies have structurally drifted."
        )
    app_src = sources["app"]
    for name in ("botsite", "dashboard"):
        assert sources[name] == app_src, (
            f"{name}/discord_auth.py has drifted from app/discord_auth.py in the "
            f"shared security function {func!r}. The Discord OAuth crypto/session "
            f"core must stay identical across every vendored copy — patch all "
            f"three copies together (see this guard's module docstring)."
        )


@pytest.mark.parametrize("const", SHARED_CONSTANTS)
def test_shared_constant_does_not_drift(const):
    sources = {name: _constant_source(name, const) for name in COPIES}
    for name, src in sources.items():
        assert src is not None, (
            f"{name}/discord_auth.py is missing the shared constant {const!r}."
        )
    app_src = sources["app"]
    for name in ("botsite", "dashboard"):
        assert sources[name] == app_src, (
            f"{name}/discord_auth.py has drifted from app/discord_auth.py in the "
            f"shared constant {const!r} — keep the OAuth config constants in sync."
        )
