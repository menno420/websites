"""Code-referenced-vs-declared env-var NAME drift for ``/owner/environments``.

The third env-name view the page needs. It already holds two:

- the COMMITTED per-service DECLARED manifest — ``app/railway.py`` ``SERVICES``
  (names + a one-line purpose each), and
- the committed-vs-LIVE diff — ``app/envdrift.py`` (documented names vs the
  live Railway variable NAMES).

This module adds **code-referenced-vs-declared**: the env-var NAMES each
service's runtime code actually READS (statically scanned at build time into
the committed snapshot ``app/data/env_coderefs.json`` by
``app/gen_env_coderefs.py``) diffed against that same declared manifest. Two
drift classes per service:

- **referenced-but-undeclared** — code reads a var the manifest omits, so a
  deploy silently gets an empty value with no warning. The load-bearing class.
- **declared-but-unreferenced** — the manifest lists a var no code reads:
  stale/unused config debt.

Signal over noise — the same platform carve-outs ``app/envdrift.py`` already
established, so the two drift views agree:

- ``PORT`` (``envdrift.RUNTIME_INJECTED``) is consumed by the container launch
  command, never a Python ``os.getenv`` — declared-but-unreferenced by design,
  so it is INFORMATIONAL, never counted as stale.
- ``GIT_SHA`` / ``RAILWAY_GIT_COMMIT_SHA`` (and any other ``RAILWAY_*`` except
  the owner-set ``RAILWAY_TOKEN``) are Railway/build injected deploy METADATA
  the code reads but the owner never declares — referenced-but-undeclared by
  design, so INFORMATIONAL, never counted as a silent-empty-deploy risk.

NAMES ONLY: this reads nothing but the committed snapshot's name lists and the
manifest's name strings — no network, no environment read, no value anywhere.
The deployed control-plane image ships only ``app/`` (``COPY app ./app``), so
the running service can never re-scan the other services' source; it reads the
baked snapshot. Fail-soft: a missing/unreadable snapshot yields an honest
``unknown``-with-reason state, never a fabricated match and never a 500.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from . import envdrift

# Per-service / page-level drift states.
DRIFT_OK = "in-sync"
DRIFT_DRIFT = "drift"
DRIFT_UNKNOWN = "unknown"

SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "env_coderefs.json"

# Deploy METADATA the platform injects and the code reads, but the owner never
# declares as config — referenced-but-undeclared here is by design, not a
# silent-empty-deploy risk. Mirrors envdrift's live-side RAILWAY_/PORT carve-out.
INJECTED_METADATA = frozenset({"GIT_SHA", "RAILWAY_GIT_COMMIT_SHA"})


def _is_platform_injected(name: str) -> bool:
    """A referenced name the platform injects, not owner-declared config.

    ``GIT_SHA``/``RAILWAY_GIT_COMMIT_SHA`` plus Railway-managed ``RAILWAY_*``
    (``RAILWAY_TOKEN`` excepted — that one IS owner-set, so its absence from a
    manifest is real drift). Consistent with ``envdrift._is_railway_provided``.
    """
    if name in INJECTED_METADATA:
        return True
    return name.startswith("RAILWAY_") and name != "RAILWAY_TOKEN"


def compute_drift(referenced: Iterable[str], declared: Iterable[str]) -> dict[str, list[str]]:
    """Pure name set-diff: the two drift classes for one service.

    ``referenced`` = names the code reads; ``declared`` = names the manifest
    lists. Returns sorted ``referenced_but_undeclared`` (code reads, manifest
    omits) and ``declared_but_unreferenced`` (manifest lists, code never
    reads). No I/O, no classification — the raw diff the task specifies.
    """
    ref = set(referenced)
    dec = set(declared)
    return {
        "referenced_but_undeclared": sorted(ref - dec),
        "declared_but_unreferenced": sorted(dec - ref),
    }


def load_coderefs() -> dict[str, Any]:
    """The committed code-reference snapshot, fail-soft.

    Returns ``{"ok": bool, "services": {name: [NAME,…]}, "error": str}``. Any
    read/parse failure degrades to ``ok=False`` with a bounded reason — never
    raises, so the page keeps rendering the rest honestly.
    """
    try:
        raw = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "services": {}, "error": "env_coderefs.json not found"}
    except (ValueError, OSError) as exc:
        return {"ok": False, "services": {}, "error": f"{type(exc).__name__}: {exc}"[:140]}
    services = raw.get("services") if isinstance(raw, dict) else None
    if not isinstance(services, dict):
        return {"ok": False, "services": {}, "error": "snapshot has no services map"}
    return {"ok": True, "services": services, "error": ""}


def annotate(data: dict[str, Any]) -> None:
    """Annotate a ``railway.overview()`` payload with the code-vs-declared diff.

    Mutates ``data`` in place: every service gains a ``code_drift`` block and
    the payload gains a page-level ``code_drift`` summary. The same read-only
    annotate idiom as ``envdrift.annotate``. If the committed snapshot is
    unavailable every service is ``unknown`` with the reason — never guessed.
    """
    services = data["services"]
    snap = load_coderefs()

    if not snap["ok"]:
        reason = (
            f"code-reference snapshot unavailable: {snap['error']} "
            "(run `python3 -m app.gen_env_coderefs`)"
        )
        for svc in services:
            svc["code_drift"] = {
                "state": DRIFT_UNKNOWN,
                "reason": reason,
                "referenced_but_undeclared": [],
                "declared_but_unreferenced": [],
                "informational_referenced": [],
                "informational_declared": [],
                "referenced_count": None,
            }
        data["code_drift"] = {
            "state": DRIFT_UNKNOWN,
            "reason": reason,
            "comparable": False,
            "drifted_services": [],
            "referenced_but_undeclared_total": 0,
            "declared_but_unreferenced_total": 0,
            "services_compared": 0,
        }
        return

    by_service = snap["services"]
    drifted: list[str] = []
    undeclared_total = 0
    unreferenced_total = 0
    compared = 0

    for svc in services:
        declared = [var["name"] for var in svc["env_vars"]]
        referenced = by_service.get(svc["name"])

        if not isinstance(referenced, list):
            svc["code_drift"] = {
                "state": DRIFT_UNKNOWN,
                "reason": (
                    f"no code-reference entry for {svc['name']!r} in the "
                    "snapshot — its code-drift stays unknown, not guessed"
                ),
                "referenced_but_undeclared": [],
                "declared_but_unreferenced": [],
                "informational_referenced": [],
                "informational_declared": [],
                "referenced_count": None,
            }
            continue

        raw = compute_drift(referenced, declared)

        # Split each raw list into genuine drift vs informational (platform
        # carve-outs), so the badge flags only real config debt.
        undeclared = [n for n in raw["referenced_but_undeclared"] if not _is_platform_injected(n)]
        info_ref = [n for n in raw["referenced_but_undeclared"] if _is_platform_injected(n)]
        unreferenced = [
            n for n in raw["declared_but_unreferenced"] if n not in envdrift.RUNTIME_INJECTED
        ]
        info_dec = [
            n for n in raw["declared_but_unreferenced"] if n in envdrift.RUNTIME_INJECTED
        ]

        state = DRIFT_DRIFT if (undeclared or unreferenced) else DRIFT_OK
        svc["code_drift"] = {
            "state": state,
            "reason": "",
            "referenced_but_undeclared": undeclared,
            "declared_but_unreferenced": unreferenced,
            "informational_referenced": info_ref,
            "informational_declared": info_dec,
            "referenced_count": len(referenced),
        }
        compared += 1
        if state == DRIFT_DRIFT:
            drifted.append(svc["name"])
        undeclared_total += len(undeclared)
        unreferenced_total += len(unreferenced)

    if compared == 0:
        state = DRIFT_UNKNOWN
    elif drifted:
        state = DRIFT_DRIFT
    else:
        state = DRIFT_OK
    data["code_drift"] = {
        "state": state,
        "reason": "",
        "comparable": compared > 0,
        "drifted_services": drifted,
        "referenced_but_undeclared_total": undeclared_total,
        "declared_but_unreferenced_total": unreferenced_total,
        "services_compared": compared,
    }
