"""Documented-vs-live variable NAME drift for ``/owner/environments``.

The page holds both halves of a diff it did not compute until now: the
COMMITTED documented env-var names per service (``app/railway.py``
``SERVICES``) and the LIVE variable NAMES Railway reports
(``railway.live_overview`` — project-scoped ``RAILWAY_TOKEN``, values dropped
at the client boundary, never here). This module computes the comparison and
annotates the ``railway.overview()`` payload in place, the same read-only
annotate idiom as ``envhub.annotate_completeness`` (PR #216):

- **documented-but-missing-live**: a name the repo documents for a service
  that a SUCCESSFUL live read does not report — an outage foot-gun, surfaced.
- **live-but-undocumented**: a live name the repo does not document —
  invisible config debt, surfaced.
- **unknown, with the exact reason**: whenever the live truth is not knowable
  (token unset, read failed, a per-service variables fetch errored) every
  affected row is ``unknown`` and carries the reason — a green/red badge is
  NEVER fabricated.
- a documented service ABSENT from a successful live read is honest drift
  (the service is not created yet — every documented name is missing live),
  not unknown: exactly PR #216's absent-service semantics.

Signal over noise, declared not guessed:

- Railway itself provides ``RAILWAY_*`` names in the live variables map
  (verified live 2026-07-12 — see tests/test_owner_environments.py). Those
  are Railway-managed, not owner-documented config, so undocumented
  ``RAILWAY_*`` names are listed informationally, never counted as drift.
  ``RAILWAY_TOKEN`` is the deliberate exception: it is an owner-set secret,
  so an undocumented live ``RAILWAY_TOKEN`` IS real drift.
- ``PORT`` is injected by Railway into the runtime, not normally present in
  the service's variables tab; a documented ``PORT`` missing live is badged
  ``runtime-injected`` (informational), never drift.

NAMES ONLY: this module reads nothing but the snapshot's ``variable_names``
lists and the committed name strings — no network call, no env read, no
value anywhere (``railway._names_only`` dropped them before this runs).
"""

from __future__ import annotations

from typing import Any

# Per-service / page-level drift states.
DRIFT_OK = "ok"
DRIFT_DRIFT = "drift"
DRIFT_UNKNOWN = "unknown"

# Per-variable live states (the "live (Railway)?" column).
VAR_SET_LIVE = "set-live"
VAR_MISSING_LIVE = "missing-live"
VAR_RUNTIME_INJECTED = "runtime-injected"
VAR_UNKNOWN = "unknown"

# Documented names Railway injects into the RUNTIME rather than the owner
# setting them in the variables tab — absent from the live variables map by
# design, so "missing live" would be permanent noise, not drift.
RUNTIME_INJECTED = frozenset({"PORT"})


def _is_railway_provided(name: str) -> bool:
    """Railway-managed ``RAILWAY_*`` names in the live map — informational,
    never drift. ``RAILWAY_TOKEN`` excepted: that one is owner-set."""
    return name.startswith("RAILWAY_") and name != "RAILWAY_TOKEN"


def _unknown_service(svc: dict[str, Any], reason: str) -> None:
    for var in svc["env_vars"]:
        var["live_state"] = VAR_UNKNOWN
    svc["drift"] = {
        "state": DRIFT_UNKNOWN,
        "reason": reason,
        "missing_live": [],
        "undocumented": [],
        "railway_provided": [],
        "note": "",
    }


def annotate(data: dict[str, Any]) -> None:
    """Annotate a ``railway.overview()`` payload with the name-drift diff.

    Mutates ``data`` in place: every service gains a ``drift`` block and
    every documented variable a ``live_state``; the payload gains a
    page-level ``drift`` summary. Honesty rules per the module docstring —
    ``unknown`` always carries its reason, and a comparison only ever
    happens against a snapshot whose ``state`` is ``ok``.
    """
    services = data["services"]
    live = data["live"]

    if live.get("state") != "ok":
        reason = live.get("reason") or f"live Railway read state: {live.get('state', '?')}"
        for svc in services:
            _unknown_service(svc, reason)
        data["drift"] = {
            "state": DRIFT_UNKNOWN,
            "comparable": False,
            "reason": reason,
            "live_state": live.get("state", "?"),
            "services_compared": 0,
            "services_unknown": len(services),
            "drifted_services": [],
            "missing_live_total": 0,
            "undocumented_total": 0,
            "undocumented_services": [],
            "fetched_at": "",
            "cached": False,
        }
        return

    by_live_name = {s.get("name"): s for s in live.get("services", [])}
    compared = 0
    unknown = 0
    drifted: list[str] = []
    missing_total = 0
    undocumented_total = 0

    for svc in services:
        documented = [var["name"] for var in svc["env_vars"]]
        lsvc = by_live_name.get(svc["name"])

        if lsvc is None:
            # The authoritative live service list came back WITHOUT this
            # service: it is not created yet — honest drift, not unknown
            # (PR #216's absent-service rule).
            missing = []
            for var in svc["env_vars"]:
                if var["name"] in RUNTIME_INJECTED:
                    var["live_state"] = VAR_RUNTIME_INJECTED
                else:
                    var["live_state"] = VAR_MISSING_LIVE
                    missing.append(var["name"])
            svc["drift"] = {
                "state": DRIFT_DRIFT,
                "reason": "",
                "missing_live": missing,
                "undocumented": [],
                "railway_provided": [],
                "note": (
                    "service not found in the live project — the live read "
                    "succeeded, so this service (and every documented "
                    "variable) is not created yet"
                ),
            }
            compared += 1
            drifted.append(svc["name"])
            missing_total += len(missing)
            continue

        if lsvc.get("error"):
            _unknown_service(
                svc,
                "live variables read failed for this service: "
                f"{lsvc['error']} — its drift stays unknown, not guessed",
            )
            unknown += 1
            continue

        live_names = set(lsvc.get("variable_names", []))
        missing = []
        for var in svc["env_vars"]:
            name = var["name"]
            if name in live_names:
                var["live_state"] = VAR_SET_LIVE
            elif name in RUNTIME_INJECTED:
                var["live_state"] = VAR_RUNTIME_INJECTED
            else:
                var["live_state"] = VAR_MISSING_LIVE
                missing.append(name)
        extra = live_names - set(documented)
        railway_provided = sorted(n for n in extra if _is_railway_provided(n))
        undocumented = sorted(n for n in extra if not _is_railway_provided(n))
        state = DRIFT_DRIFT if (missing or undocumented) else DRIFT_OK
        svc["drift"] = {
            "state": state,
            "reason": "",
            "missing_live": missing,
            "undocumented": undocumented,
            "railway_provided": railway_provided,
            "note": "",
        }
        compared += 1
        if state == DRIFT_DRIFT:
            drifted.append(svc["name"])
        missing_total += len(missing)
        undocumented_total += len(undocumented)

    # Live services the repo documents nothing about — service-level drift.
    documented_names = {svc["name"] for svc in services}
    undocumented_services = sorted(
        name for name in by_live_name if name and name not in documented_names
    )

    if compared == 0:
        state = DRIFT_UNKNOWN
    elif drifted or undocumented_services:
        state = DRIFT_DRIFT
    else:
        state = DRIFT_OK
    data["drift"] = {
        "state": state,
        "comparable": compared > 0,
        "reason": (
            f"{unknown} service{'s' if unknown != 1 else ''}' live variables "
            "could not be read"
            if unknown
            else ""
        ),
        "live_state": "ok",
        "services_compared": compared,
        "services_unknown": unknown,
        "drifted_services": drifted,
        "missing_live_total": missing_total,
        "undocumented_total": undocumented_total,
        "undocumented_services": undocumented_services,
        "fetched_at": live.get("fetched_at", ""),
        "cached": bool(live.get("cached")),
    }
