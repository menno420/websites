"""Release-drift verdict — ONE source of truth for the drift signal that
``scripts/healthcheck.py``'s release-drift pass and ``/owner/queue``'s
drift chip both render.

The signal (PR #365): a registry blocker's ``ask_id`` is joined to its
askverify probe verdict, and RELEASE DRIFT is flagged when the probe
positively detects the ask done while the gate (a registry card, or the
owner ledger the console shows) is still up — or when a registry blocker's
``ask_id`` matches no askverify entry at all (ledger drift).

Both callers already hold the join inputs — whether askverify's REGISTRY
knows the ``ask_id`` and the ask's probe verdict — so this module is a
PURE classifier over those inputs. It reads no files, opens no sockets,
and imports no other service's package: the botsite-registry collection
stays in the healthcheck script, and the console reuses the probe verdicts
``app.askverify.annotate`` already attached to each open ask. That keeps
the drift *logic* single-sourced without coupling the control-plane
service to botsite.
"""

from __future__ import annotations

from typing import Any

from app import askverify

# --------------------------------------------------------------------------- #
# Drift kinds — the classifier's semantic verdict for one ask.
# --------------------------------------------------------------------------- #
ID_LESS = "id-less"  # blocker carries no ask_id — nothing to join
LEDGER_DRIFT = "ledger-drift"  # ask_id matches no askverify entry
DONE_GATED = "done-gated"  # probe done-detected but the gate is still up
STILL_OPEN = "still-open"  # gate matches reality — the healthy row
NOT_CHECKABLE = "not-checkable"  # no read-only probe can observe the ask
UNKNOWN = "unknown"  # probe could not tell (error / unreadable)

# The kinds that FAIL the healthcheck pass and are worth an owner-facing
# warning chip. still-open / not-checkable / unknown / id-less never flag —
# never invent state.
_FLAGGED = frozenset({LEDGER_DRIFT, DONE_GATED})

# Healthcheck column mark per kind (the FLAGGED/PASS/info idiom the pass's
# printed lines and tests pin).
_MARK = {
    ID_LESS: "info",
    LEDGER_DRIFT: "FLAGGED",
    DONE_GATED: "FLAGGED",
    STILL_OPEN: "PASS",
    NOT_CHECKABLE: "info",
    UNKNOWN: "info",
}

# Owner-console chip label per FLAGGED kind (the glanceable phrasing; the
# probe detail rides in the chip title). Only flagged kinds get a chip —
# a non-drifting ask shows nothing.
_CHIP_LABEL = {
    DONE_GATED: "⚠ drift: done-detected but still gated",
    LEDGER_DRIFT: "⚠ drift: blocker without probe",
}


def classify(
    ask_id: str | None,
    entry_exists: bool,
    verdict: str | None,
    detail: str = "",
) -> dict[str, Any]:
    """Classify the release-drift verdict for ONE ask.

    ``ask_id`` — the blocker's stable id, or ``None`` for an id-less
    blocker (nothing to join). ``entry_exists`` — whether askverify's
    REGISTRY knows that id (``False`` is ledger drift). ``verdict`` — the
    ask's askverify probe verdict (one of ``askverify.DONE`` /
    ``STILL_OPEN`` / ``NOT_CHECKABLE`` / ``UNKNOWN``), only consulted once
    the id is known and registered. ``detail`` — the probe's short reason,
    folded into the not-checkable / unknown rows.

    Returns a structured verdict: ``kind`` (a module constant), ``flagged``
    (fails the pass / warrants a chip), ``mark`` (the healthcheck column),
    ``token`` (the id column — the id or ``<no ask_id>``) and ``reason``
    (the canonical parenthetical text). Pure — never raises, never
    invents state (a probe it cannot read stays an honest info row).
    """
    if not ask_id:
        kind = ID_LESS
        reason = "blocker carries no ledger id — nothing to join"
        token = "<no ask_id>"
    elif not entry_exists:
        kind = LEDGER_DRIFT
        reason = "ledger drift: ask_id matches no askverify entry"
        token = ask_id
    elif verdict == askverify.DONE:
        kind = DONE_GATED
        reason = "drift: ask done-detected but registry still gated"
        token = ask_id
    elif verdict == askverify.STILL_OPEN:
        kind = STILL_OPEN
        reason = "still-open — registry gate matches reality"
        token = ask_id
    elif verdict == askverify.NOT_CHECKABLE:
        kind = NOT_CHECKABLE
        reason = f"not machine-checkable — {detail or 'no probe registered'}"
        token = ask_id
    else:  # UNKNOWN / None — never invent state
        kind = UNKNOWN
        reason = f"unknown — {detail or 'probe could not tell'}"
        token = ask_id

    return {
        "kind": kind,
        "flagged": kind in _FLAGGED,
        "mark": _MARK[kind],
        "token": token,
        "reason": reason,
    }


def chip(verify: dict[str, Any] | None) -> dict[str, Any] | None:
    """The owner-console drift chip for one OPEN ask, or ``None`` when the
    ask is not drifting (so the template omits it).

    ``verify`` is the ask's ``item["verify"]`` verdict as
    ``app.askverify.annotate`` attaches it. An open ask on the queue is a
    live ledger row, so its gate is up by definition; the drift worth a
    chip is the DONE-detected case — the probe says the release is done
    while the ledger (and every registry card keyed to this ask) still
    gates. Classification routes through :func:`classify` so the chip and
    the healthcheck line can never diverge. Read-only presentation only:
    label + the site's badge css + the probe reason as the hover title.
    """
    if not verify:
        return None
    v = classify(
        ask_id="_",  # an open ledger ask always carries a live gate
        entry_exists=True,
        verdict=verify.get("verdict"),
        detail=verify.get("detail", ""),
    )
    if not v["flagged"]:
        return None
    return {
        "label": _CHIP_LABEL[v["kind"]],
        "css": "warn",
        "title": verify.get("detail") or v["reason"],
    }
