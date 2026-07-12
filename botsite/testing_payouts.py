"""Tester-payout module — provider-pluggable adapters, v1 is DRY-RUN ONLY.

Owner follow-up (relayed live 2026-07-12): payouts should become automatic
once a submission's steps are confirmed; PayPal Payouts is the CONFIRMED v1
payout rail. This module ships the shape of that — adapter interface, caps,
eligibility gate, kill switch — with **no way to move real money**:

- ``DRY_RUN = True`` is a v1 code constant, not configuration. The PayPal
  adapter contains NO provider HTTP call (no http client is even imported —
  a test pins this); its execute path only records a ``dry-run`` ledger row.
- No credentials → the adapter reports itself unconfigured. Credential ENV
  NAMES only (``PAYPAL_CLIENT_ID`` / ``PAYPAL_CLIENT_SECRET``); values are
  never read into any output, log, template, or ledger note.
- Even with credentials present, auto-pay stays OFF unless
  ``TESTING_AUTOPAY_ENABLED=true`` — the global kill switch is that flag
  being absent/false.
- Hard caps: per-payout max, per-day cap, per-month cap, one payout per
  email per task.
- Auto-payout eligibility (auto-pay when the AI exit-review score reaches
  the ``TESTING_AUTOPAY_MIN_SCORE`` threshold AND the submission is not
  low-effort/flagged; otherwise queue for owner one-click) computes REAL
  eligibility since PR2 wired the exit-review score in — but the ``DRY_RUN``
  constant below still holds every payout back, so every approve in v1
  produces an ``owed`` ledger row for the owner queue, never a payment. The
  owner queue shows the would-auto-pay verdict per submission.

Layering: domain module for ``botsite/testing.py``; imports only the store.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from . import testing_store as store

# v1 hard lock: flipping this to False is a deliberate PR3 change that must
# arrive together with the real PayPal Payouts call, its tests, and the
# owner's credentials on the service — never a config toggle.
DRY_RUN = True

# Hard caps. The per-payout max matches the catalog's top payout ($20); the
# day/month caps are env-tunable so the owner can widen them without a PR.
MAX_PAYOUT_USD = 20.0
DEFAULT_DAILY_CAP_USD = 60.0
DEFAULT_MONTHLY_CAP_USD = 300.0

# Credential env NAMES (values never appear anywhere in this repo).
ENV_CLIENT_ID = "PAYPAL_CLIENT_ID"
ENV_CLIENT_SECRET = "PAYPAL_CLIENT_SECRET"
ENV_AUTOPAY = "TESTING_AUTOPAY_ENABLED"

# Auto-pay quality bar: the AI exit-review score (PR2) must reach this for a
# submission to be autopay-eligible. Env-tunable; the gate still queues
# everything in v1 because DRY_RUN holds.
ENV_MIN_SCORE = "TESTING_AUTOPAY_MIN_SCORE"
DEFAULT_MIN_SCORE = 80.0


def min_autopay_score() -> float:
    return float(os.environ.get(ENV_MIN_SCORE) or DEFAULT_MIN_SCORE)


def daily_cap_usd() -> float:
    return float(os.environ.get("TESTING_PAYOUT_DAILY_CAP_USD") or DEFAULT_DAILY_CAP_USD)


def monthly_cap_usd() -> float:
    return float(os.environ.get("TESTING_PAYOUT_MONTHLY_CAP_USD") or DEFAULT_MONTHLY_CAP_USD)


def autopay_enabled() -> bool:
    """The global kill switch: absent/false = OFF (the safe default)."""
    return (os.environ.get(ENV_AUTOPAY) or "").strip().lower() == "true"


class PayoutAdapter:
    """Provider interface. Adapters read credential env NAMES, never log
    values, and in v1 must not perform any provider call."""

    name = "abstract"

    def configured(self) -> bool:  # pragma: no cover - interface default
        return False

    def execute(self, *, claim: dict[str, Any], amount_usd: float) -> dict[str, Any]:
        raise NotImplementedError


class PayPalPayoutsAdapter(PayoutAdapter):
    """PayPal Payouts — the owner-confirmed v1 rail (relayed 2026-07-12).

    v1 is a deliberate shell: ``configured()`` only checks that the two env
    names are set; ``execute()`` NEVER calls PayPal (no HTTP client exists in
    this module) and instead records a ``dry-run`` ledger row. PR3 replaces
    the execute body with the real Payouts API call once credentials are on
    the botsite service.
    """

    name = "paypal-payouts"

    def configured(self) -> bool:
        return bool(os.environ.get(ENV_CLIENT_ID)) and bool(
            os.environ.get(ENV_CLIENT_SECRET)
        )

    def execute(self, *, claim: dict[str, Any], amount_usd: float) -> dict[str, Any]:
        # DRY-RUN, unconditionally in v1: no request is built, no credential
        # value is read, no money can move. The ledger row is the receipt.
        entry = store.add_ledger_entry(
            claim["id"],
            claim["task_id"],
            claim["email"],
            amount_usd,
            "dry-run",
            note=(
                f"DRY-RUN via {self.name}: no provider call executed "
                "(v1 payout module is dry-run only; real call lands in PR3)"
            ),
        )
        return {"ok": False, "dry_run": True, "provider": self.name, "ledger_id": entry["id"]}


def get_adapter() -> PayoutAdapter:
    return PayPalPayoutsAdapter()


def _month_start_iso(now: Optional[time.struct_time] = None) -> str:
    t = now or time.gmtime()
    return time.strftime("%Y-%m-01T00:00:00Z", t)


def _day_start_iso(now: Optional[time.struct_time] = None) -> str:
    t = now or time.gmtime()
    return time.strftime("%Y-%m-%dT00:00:00Z", t)


def decide_payout(
    claim: dict[str, Any],
    task: dict[str, Any],
    *,
    ai_score: Optional[int] = None,
    ai_low_effort: bool = False,
    tester_flagged: bool = False,
) -> dict[str, Any]:
    """The auto-payout eligibility gate, evaluated on approve.

    Returns ``{"action": "queue-owner" | "autopay", "amount_usd", "reasons"}``.
    ``ai_score`` is the AI exit-review's 0-100 quality score (PR2); ``None``
    means no automated verdict exists for the submission (degraded mode /
    review pending) and the gate queues. The score gate computes REAL
    eligibility now, but v1 behavior is unchanged: the DRY_RUN constant below
    always appends a reason, so everything still queues for the owner.
    Reasons are accumulated (not short-circuited) so the owner queue can show
    every gate that held a payout back.
    """
    amount = float(task.get("payout_usd") or 0)
    reasons: list[str] = []

    if amount <= 0 or amount > MAX_PAYOUT_USD:
        reasons.append(
            f"amount ${amount:.2f} outside the per-payout limit (max ${MAX_PAYOUT_USD:.2f})"
        )
    if store.has_payout(claim["task_id"], claim["email"]):
        reasons.append("a payout for this email + task already exists (one per email per task)")
    if not autopay_enabled():
        reasons.append(f"auto-pay kill switch is OFF ({ENV_AUTOPAY} is not 'true')")
    adapter = get_adapter()
    if not adapter.configured():
        reasons.append(
            f"payout adapter '{adapter.name}' has no credentials "
            f"({ENV_CLIENT_ID}/{ENV_CLIENT_SECRET} not set on the service)"
        )
    if DRY_RUN:
        reasons.append("payout module is v1 DRY-RUN — no real payment path exists yet (PR3)")
    if store.paid_total_since(_day_start_iso()) + amount > daily_cap_usd():
        reasons.append(f"daily payout cap (${daily_cap_usd():.2f}) would be exceeded")
    if store.paid_total_since(_month_start_iso()) + amount > monthly_cap_usd():
        reasons.append(f"monthly payout cap (${monthly_cap_usd():.2f}) would be exceeded")
    if tester_flagged:
        reasons.append("tester is flagged — held for owner review")
    if ai_low_effort:
        reasons.append("AI exit-review flagged the submission as low-effort — held for owner review")
    if ai_score is None:
        reasons.append(
            "no automated exit-review verdict for this submission "
            "(degraded/unavailable) — queued for owner one-click approval"
        )
    elif ai_score < min_autopay_score():
        reasons.append(
            f"AI exit-review score {ai_score} is below the auto-pay threshold "
            f"({min_autopay_score():.0f} — {ENV_MIN_SCORE})"
        )

    if reasons:
        return {"action": "queue-owner", "amount_usd": amount, "reasons": reasons}
    # Unreachable in v1 by construction (the DRY_RUN gate above always
    # appends a reason); kept as the real PR3 code path.
    return {"action": "autopay", "amount_usd": amount, "reasons": []}


def process_approval(
    claim: dict[str, Any],
    task: dict[str, Any],
    *,
    ai_score: Optional[int] = None,
    ai_low_effort: bool = False,
) -> dict[str, Any]:
    """Run the gate for an approved submission and write the ledger.

    v1 outcome, always: an ``owed`` ledger row (queued for the owner) with the
    gate's reasons in the note. The autopay branch exists and is exercised in
    tests via the adapter's dry-run execute — it can never pay in v1.
    """
    decision = decide_payout(
        claim, task, ai_score=ai_score, ai_low_effort=ai_low_effort
    )
    if decision["action"] == "autopay":  # pragma: no cover - impossible in v1
        result = get_adapter().execute(claim=claim, amount_usd=decision["amount_usd"])
        decision["executed"] = result
        return decision
    entry = store.add_ledger_entry(
        claim["id"],
        claim["task_id"],
        claim["email"],
        decision["amount_usd"],
        "owed",
        note="; ".join(decision["reasons"]),
    )
    decision["ledger_id"] = entry["id"]
    return decision


def payout_config_summary() -> dict[str, Any]:
    """Owner-queue display of the payout machinery's state. Names only —
    never credential values."""
    adapter = get_adapter()
    return {
        "provider": adapter.name,
        "dry_run": DRY_RUN,
        "autopay_enabled": autopay_enabled(),
        "adapter_configured": adapter.configured(),
        "credential_env_names": [ENV_CLIENT_ID, ENV_CLIENT_SECRET],
        "kill_switch_env": ENV_AUTOPAY,
        "max_payout_usd": MAX_PAYOUT_USD,
        "daily_cap_usd": daily_cap_usd(),
        "monthly_cap_usd": monthly_cap_usd(),
        "autopay_min_score": min_autopay_score(),
        "min_score_env": ENV_MIN_SCORE,
    }
