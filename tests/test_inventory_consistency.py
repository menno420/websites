"""Committed-inventory consistency pin: railway.SERVICES vs the envhub registry.

The repo hand-keeps TWO committed inventories of the same four Railway
services' variable names:

1. ``app/railway.py`` ``SERVICES`` — the per-variable purpose ledger rendered
   at /owner/environments;
2. ``app/data/environments.json``'s ``superbot-websites`` group — the owner
   environments-hub registry rendered at /owner/environments-hub.

Both claim to document the same truth, and they have already drifted once
(the registry documented ``ANTHROPIC_API_KEY`` for botsite while SERVICES
did not — found 2026-07-12, ``.sessions/2026-07-12-owner-envs-name-drift.md``,
fixed in this test's PR). The PR #218 live drift check cannot catch this
class: it compares each inventory against Railway, never against the other.

This suite is the compile-time net: zero network (the committed module +
the committed JSON via the real ``envhub.load_registry`` loader — no HTTP,
no token), asserting per service that the two variable-NAME sets agree in
BOTH directions, that the service-name sets agree, and that the public URLs
agree. NAMES ONLY throughout — no test here ever touches a variable value.

Declared exceptions live in the explicit allowlists below — one entry per
legitimately one-sided variable WITH a justification comment; a stale
allowlist entry (exempting a variable that is no longer one-sided) fails
too, so exemptions cannot outlive their reason. No silent exemptions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import envhub, railway  # noqa: E402

# The envhub registry group that mirrors railway.SERVICES. The registry's
# other groups (reliable-grace, superbot-mineverse, github-actions,
# claude-cloud) document OTHER estates whose variable names deliberately
# live elsewhere — they have no SERVICES counterpart and are out of scope
# by construction, not exemption.
GROUP_ID = "superbot-websites"

# Declared exceptions — (service, variable_name) pairs allowed to appear in
# ONE inventory only. Every entry MUST carry a comment saying why the
# one-sidedness is legitimate. Currently empty: after the 2026-07-12 drift
# fix (ANTHROPIC_API_KEY added to SERVICES' botsite entry, evidence
# docs/owner/OWNER-ACTIONS.md row K), every variable either appears in both
# inventories or is a bug.
ALLOWED_ONLY_IN_REGISTRY: set[tuple[str, str]] = set()
ALLOWED_ONLY_IN_SERVICES: set[tuple[str, str]] = set()


def _registry_surfaces() -> dict[str, dict]:
    registry = envhub.load_registry()
    group = next(g for g in registry["groups"] if g["id"] == GROUP_ID)
    return {s["name"]: s for s in group["surfaces"]}


def _services() -> dict[str, dict]:
    return {s["name"]: s for s in railway.SERVICES}


def test_service_name_sets_match():
    """Both inventories describe the same set of services, by name."""
    reg, svc = _registry_surfaces(), _services()
    assert set(reg) == set(svc), (
        f"service sets drifted — only in registry ({envhub.REGISTRY_PATH.name}): "
        f"{sorted(set(reg) - set(svc))}; only in railway.SERVICES: "
        f"{sorted(set(svc) - set(reg))}"
    )


def test_variable_name_sets_match_per_service():
    """Per service, the variable-NAME sets agree in both directions
    (minus the declared allowlists)."""
    reg, svc = _registry_surfaces(), _services()
    problems: list[str] = []
    for name in sorted(set(reg) & set(svc)):
        reg_names = set(reg[name]["variable_names"])
        svc_names = {v["name"] for v in svc[name]["env_vars"]}
        only_reg = {
            v for v in reg_names - svc_names
            if (name, v) not in ALLOWED_ONLY_IN_REGISTRY
        }
        only_svc = {
            v for v in svc_names - reg_names
            if (name, v) not in ALLOWED_ONLY_IN_SERVICES
        }
        if only_reg:
            problems.append(
                f"{name}: {sorted(only_reg)} documented in "
                f"app/data/environments.json but missing from "
                f"app/railway.py SERVICES — add it there (or allowlist it "
                f"here with a justification)"
            )
        if only_svc:
            problems.append(
                f"{name}: {sorted(only_svc)} documented in app/railway.py "
                f"SERVICES but missing from app/data/environments.json — "
                f"add it there (or allowlist it here with a justification)"
            )
    assert not problems, "committed inventories drifted:\n" + "\n".join(problems)


def test_urls_match_per_service():
    """The public URL each inventory records for a service is the same."""
    reg, svc = _registry_surfaces(), _services()
    for name in sorted(set(reg) & set(svc)):
        assert reg[name]["url"] == svc[name]["url"], (
            f"{name}: URL drifted — registry says {reg[name]['url']!r}, "
            f"railway.SERVICES says {svc[name]['url']!r}"
        )


def test_allowlists_carry_no_stale_entries():
    """An allowlist entry whose variable is no longer one-sided (or whose
    service does not exist) is dead weight that would silently mask the
    NEXT drift of that variable — fail it."""
    reg, svc = _registry_surfaces(), _services()
    stale: list[str] = []
    for service, var in sorted(ALLOWED_ONLY_IN_REGISTRY):
        reg_names = set(reg.get(service, {}).get("variable_names", []))
        svc_names = {v["name"] for v in svc.get(service, {}).get("env_vars", [])}
        if not (var in reg_names and var not in svc_names):
            stale.append(f"ALLOWED_ONLY_IN_REGISTRY: ({service!r}, {var!r})")
    for service, var in sorted(ALLOWED_ONLY_IN_SERVICES):
        reg_names = set(reg.get(service, {}).get("variable_names", []))
        svc_names = {v["name"] for v in svc.get(service, {}).get("env_vars", [])}
        if not (var in svc_names and var not in reg_names):
            stale.append(f"ALLOWED_ONLY_IN_SERVICES: ({service!r}, {var!r})")
    assert not stale, (
        "stale allowlist entries (no longer one-sided — remove them):\n"
        + "\n".join(stale)
    )
