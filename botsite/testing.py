"""Tester-recruitment program — the ``/testing`` section (ORDER 018 PR1).

Public flow: an honest landing page over a committed task catalog
(``testing_tasks.json``), a claim form per open task (no mail provider exists
in this repo, so no magic-code email — the claim response shows a private
tokened link the tester must save; claims are reviewed manually), and a
structured per-type submission form on that private link. The AI exit-review
arrives in PR2; every page says so honestly. Screenshot upload is deliberately
deferred to PR2 (multipart parsing would add the first new dependency to this
service; the form says so and asks for described/linked evidence instead).

Owner flow: HTTP Basic (constant-time compare vs env ``SITE_PASSWORD``,
fail-closed — unset → 503, wrong → 401; mirrors the control-plane's
``app/owner.py`` pattern, re-implemented here because services never import
each other), a review queue with approve / reject / mark-paid transitions
writing the payout ledger, and a full-DB JSON export — the backup valve for
the LOUDLY-FLAGGED ephemeral SQLite store (see ``testing_store.py``).

Payouts: PayPal Payouts is the owner-confirmed rail; v1 is DRY-RUN ONLY
(``testing_payouts.py`` — kill switch + caps + eligibility gate, no provider
call exists). The tester's optional PayPal email on the claim form is the
canonical payout address.

Anti-abuse on every state-changing route (re-implemented from the pattern in
unmerged PR #159's ``app/owner.py``, independently — no cross-service import):
same-origin check (Origin, falling back to Referer; both absent → 403) and an
in-process sliding-window rate limit (per path + client IP, 10/60s → 429 with
Retry-After; ``reset_rate_limits()`` is the test hook). Plus: one claim and
one payout per task per email, and a total-open-bounty cap enforced at claim
time and shown on the landing page.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import time
from collections import deque
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from . import data_source as ds
from . import testing_payouts as payouts
from . import testing_store as store

BASE_DIR = Path(__file__).resolve().parent
TASKS_PATH = BASE_DIR / "testing_tasks.json"

router = APIRouter(prefix="/testing")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Total-open-bounty cap: the sum of (non-rejected claims × their task payout)
# may never exceed this. Enforced at claim time, shown on the landing page.
DEFAULT_BOUNTY_CAP_USD = 200.0

_FIELD_MAX = 5000  # per-field input cap (bytes of honesty, not a novel)

_UNAUTH_HEADERS = {"WWW-Authenticate": 'Basic realm="testing owner"'}

# Per-type structured questionnaire: (field name, label, kind). Free-form
# findings are appended for every type. guided-walkthrough is the labeled
# placeholder until PR2 ships the step scripts.
QUESTIONNAIRES: dict[str, list[tuple[str, str, str]]] = {
    "site-review": [
        ("what_worked", "What worked well?", "textarea"),
        ("what_broke", "What broke? (exact URLs + what you did)", "textarea"),
        ("confusing", "What was confusing or unclear?", "textarea"),
        ("device_browser", "Device + browser (e.g. iPhone 15 / Safari)", "input"),
        ("severity", "Worst issue you found", "severity"),
    ],
    "game-test": [
        ("what_worked", "What was fun / worked well?", "textarea"),
        ("what_broke", "Bugs, crashes, stuck states (what you did, what happened)", "textarea"),
        ("confusing", "What was confusing (controls, goals, UI)?", "textarea"),
        ("device_browser", "Device + browser", "input"),
        ("severity", "Worst issue you found", "severity"),
    ],
    "guided-walkthrough": [],  # placeholder — step scripts + AI confirmation land in PR2
}
SEVERITIES = ["none", "minor", "major", "blocker"]


# --------------------------------------------------------------------------
# anti-abuse guards (every state-changing route)
# --------------------------------------------------------------------------
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_S = 60.0
_rate_buckets: dict[tuple[str, str], deque] = {}


def reset_rate_limits() -> None:
    """Test hook: clear the in-process sliding windows."""
    _rate_buckets.clear()


def _check_same_origin(request: Request) -> None:
    """Origin-host must match the request Host; fall back to Referer; a
    state-changing request carrying neither is rejected (403)."""
    host = (request.headers.get("host") or "").strip().lower()
    source = request.headers.get("origin") or request.headers.get("referer")
    if not source:
        raise HTTPException(
            status_code=403,
            detail="cross-origin protection: request carries no Origin or Referer header",
        )
    if (urlsplit(source).netloc or "").lower() != host:
        raise HTTPException(status_code=403, detail="cross-origin request rejected")


def _check_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    key = (request.url.path, ip)
    now = time.monotonic()
    bucket = _rate_buckets.setdefault(key, deque())
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_S:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_S - (now - bucket[0])) + 1)
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded — try again shortly",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def guard_state_change(request: Request) -> None:
    """Dependency on every POST route: same-origin + rate limit."""
    _check_same_origin(request)
    _check_rate_limit(request)


# --------------------------------------------------------------------------
# owner auth — HTTP Basic vs SITE_PASSWORD, fail-closed (503 unset, 401 bad).
# Mirrors app/owner.py's require_owner; re-implemented (never imported).
# --------------------------------------------------------------------------
def require_owner(request: Request) -> None:
    password = os.environ.get("SITE_PASSWORD", "")
    if not password:
        # Fail closed: an unset password never means an open door. The public
        # /testing pages are unaffected — only this gated queue 503s.
        raise HTTPException(
            status_code=503,
            detail="testing owner queue unavailable: SITE_PASSWORD is not configured",
        )
    header = request.headers.get("authorization", "")
    supplied = ""
    if header.lower().startswith("basic "):
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
            _user, _, supplied = decoded.partition(":")
        except Exception:
            supplied = ""
    if not supplied or not secrets.compare_digest(supplied, password):
        raise HTTPException(
            status_code=401,
            detail="owner authentication required",
            headers=_UNAUTH_HEADERS,
        )


# --------------------------------------------------------------------------
# task catalog (committed JSON) + live shaping over the store
# --------------------------------------------------------------------------
def load_tasks() -> list[dict[str, Any]]:
    data = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    return list(data.get("tasks") or [])


def bounty_cap_usd() -> float:
    return float(os.environ.get("TESTING_BOUNTY_CAP_USD") or DEFAULT_BOUNTY_CAP_USD)


def committed_bounty_usd() -> float:
    """Sum of payouts promised to non-rejected claims (the live exposure)."""
    payout_by_task = {t["id"]: float(t.get("payout_usd") or 0) for t in load_tasks()}
    return sum(payout_by_task.get(c["task_id"], 0.0) for c in store.active_claims())


def shaped_tasks() -> list[dict[str, Any]]:
    out = []
    for t in load_tasks():
        active = store.active_claim_count(t["id"])
        slots_left = max(0, int(t.get("slots_total") or 0) - active)
        effective = t.get("status") or "open"
        if effective == "open" and slots_left == 0:
            effective = "closed"  # auto-close when the slots fill
        out.append({**t, "slots_left": slots_left, "effective_status": effective})
    return out


def task_by_id(task_id: str) -> Optional[dict[str, Any]]:
    for t in shaped_tasks():
        if t["id"] == task_id:
            return t
    return None


# --------------------------------------------------------------------------
# template context (same base keys the rest of the site's pages carry)
# --------------------------------------------------------------------------
async def _ctx(request: Request) -> dict[str, Any]:
    # Deferred import: app.py includes this router, so the app module is
    # complete by the time any request runs (no import-time cycle).
    from .app import NAV

    site_res = await ds.fetch_site()
    site = site_res.get("data", {}) or {}
    return {
        "request": request,
        "active": "testing",
        "nav": NAV,
        "add_url": ds.ADD_TO_DISCORD_URL,
        "site_ok": site_res.get("ok", False),
        "site_error": site_res.get("error", ""),
        "build": ds.build_meta(site),
        "counts": ds.counts(site),
    }


def _bounty(request_committed: Optional[float] = None) -> dict[str, float]:
    committed = committed_bounty_usd() if request_committed is None else request_committed
    cap = bounty_cap_usd()
    return {"committed": committed, "cap": cap, "remaining": max(0.0, cap - committed)}


def _clean(form: Any, field: str) -> str:
    return str(form.get(field) or "").strip()[:_FIELD_MAX]


# --------------------------------------------------------------------------
# public tester flow
# --------------------------------------------------------------------------
@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def testing_index(request: Request):
    ctx = await _ctx(request)
    ctx.update({"tasks": shaped_tasks(), "bounty": _bounty()})
    return templates.TemplateResponse(request, "testing_index.html", ctx)


@router.get("/tasks/{task_id}", response_class=HTMLResponse)
async def testing_task(request: Request, task_id: str):
    task = task_by_id(task_id)
    ctx = await _ctx(request)
    if task is None:
        ctx.update({"key": task_id})
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx.update({"task": task, "bounty": _bounty(), "error": None})
    return templates.TemplateResponse(request, "testing_task.html", ctx)


async def _task_error(
    request: Request, task: dict[str, Any], message: str, status_code: int
) -> HTMLResponse:
    ctx = await _ctx(request)
    ctx.update({"task": task, "bounty": _bounty(), "error": message})
    return templates.TemplateResponse(
        request, "testing_task.html", ctx, status_code=status_code
    )


@router.post("/tasks/{task_id}/claim", response_class=HTMLResponse)
async def testing_claim(
    request: Request, task_id: str, _: None = Depends(guard_state_change)
):
    task = task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="unknown task")
    form = await request.form()  # urlencoded — no multipart dependency
    name = _clean(form, "name")[:200]
    email = _clean(form, "email")[:200].lower()
    paypal_email = _clean(form, "paypal_email")[:200].lower()
    if not name or not email or "@" not in email:
        return await _task_error(
            request, task, "A name and a valid email are required to claim a task.", 400
        )
    if paypal_email and "@" not in paypal_email:
        return await _task_error(
            request, task, "The PayPal email doesn't look like an email address.", 400
        )
    if task["effective_status"] != "open":
        return await _task_error(
            request,
            task,
            "This task isn't open for claims right now "
            f"(status: {task['effective_status']}).",
            409,
        )
    if store.has_claim(task_id, email):
        return await _task_error(
            request, task, "This email already claimed this task (one claim per task per email).", 409
        )
    payout = float(task.get("payout_usd") or 0)
    bounty = _bounty()
    if bounty["committed"] + payout > bounty["cap"]:
        return await _task_error(
            request,
            task,
            f"The program's total open-bounty cap (${bounty['cap']:.0f}) would be "
            "exceeded — no new claims until open work is reviewed.",
            409,
        )
    token = secrets.token_urlsafe(24)
    claim = store.create_claim(task_id, name, email, paypal_email, token)
    ctx = await _ctx(request)
    ctx.update(
        {
            "task": task,
            "claim": claim,
            "submission_path": f"/testing/s/{token}",
        }
    )
    return templates.TemplateResponse(request, "testing_claimed.html", ctx)


def _submission_ctx(claim: dict[str, Any]) -> dict[str, Any]:
    task = task_by_id(claim["task_id"]) or {
        "id": claim["task_id"],
        "title": claim["task_id"],
        "type": "site-review",
        "payout_usd": 0,
        "brief": "",
        "est_minutes": 0,
    }
    submission = store.submission_for_claim(claim["id"])
    answers = {}
    if submission:
        try:
            answers = json.loads(submission.get("answers_json") or "{}")
        except ValueError:
            answers = {}
    return {
        "claim": claim,
        "task": task,
        "submission": submission,
        "answers": answers,
        "questionnaire": QUESTIONNAIRES.get(task.get("type") or "", []),
        "severities": SEVERITIES,
    }


@router.get("/s/{token}", response_class=HTMLResponse)
async def testing_submission_page(request: Request, token: str):
    claim = store.claim_by_token(token)
    ctx = await _ctx(request)
    if claim is None:
        ctx.update({"key": "submission link"})
        return templates.TemplateResponse(request, "not_found.html", ctx, status_code=404)
    ctx.update(_submission_ctx(claim))
    ctx.update({"error": None})
    return templates.TemplateResponse(request, "testing_submission.html", ctx)


@router.post("/s/{token}", response_class=HTMLResponse)
async def testing_submit(
    request: Request, token: str, _: None = Depends(guard_state_change)
):
    claim = store.claim_by_token(token)
    if claim is None:
        raise HTTPException(status_code=404, detail="unknown submission link")
    ctx = await _ctx(request)
    if claim["status"] != "claimed":
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": "This claim already has a submission — it's in review."})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=409
        )
    task = task_by_id(claim["task_id"])
    task_type = (task or {}).get("type") or ""
    form = await request.form()
    answers: dict[str, str] = {}
    has_content = False
    for field, _label, kind in QUESTIONNAIRES.get(task_type, []):
        value = _clean(form, field)
        if kind == "severity":
            # A severity pick alone isn't a report — it never counts as content.
            answers[field] = value if value in SEVERITIES else ""
            continue
        answers[field] = value
        has_content = has_content or bool(value)
    findings = _clean(form, "findings")
    if not findings and not has_content:
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": "The submission is empty — fill in at least one field."})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=400
        )
    store.create_submission(claim["id"], answers, findings)
    store.set_claim_status(claim["id"], "submitted")
    refreshed = store.claim_by_token(token)
    ctx.update(_submission_ctx(refreshed))
    ctx.update({"error": None})
    return templates.TemplateResponse(request, "testing_submission.html", ctx)


# --------------------------------------------------------------------------
# owner queue (auth + same guards on state changes)
# --------------------------------------------------------------------------
async def _owner_page(
    request: Request, banner: Optional[dict[str, Any]] = None, status_code: int = 200
) -> HTMLResponse:
    submissions = store.list_submissions()
    for s in submissions:
        try:
            s["answers"] = json.loads(s.get("answers_json") or "{}")
        except ValueError:
            s["answers"] = {}
    ctx = await _ctx(request)
    ctx.update(
        {
            "tasks": shaped_tasks(),
            "claims": store.list_claims(),
            "submissions": submissions,
            "ledger": store.ledger_entries(),
            "ledger_totals": store.ledger_totals(),
            "bounty": _bounty(),
            "payout_config": payouts.payout_config_summary(),
            "db_path": store.db_path(),
            "banner": banner,
        }
    )
    return templates.TemplateResponse(
        request, "testing_owner.html", ctx, status_code=status_code
    )


@router.get("/owner", response_class=HTMLResponse)
async def testing_owner(request: Request, _: None = Depends(require_owner)):
    return await _owner_page(request)


def _submission_claim_or_400(submission_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    submission = store.submission_by_id(submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="unknown submission")
    claim = store.claim_by_id(submission["claim_id"])
    if claim is None:  # pragma: no cover - FK'd on write
        raise HTTPException(status_code=404, detail="claim missing for submission")
    return submission, claim


@router.post("/owner/submissions/{submission_id}/approve", response_class=HTMLResponse)
async def owner_approve(
    request: Request,
    submission_id: int,
    _guard: None = Depends(guard_state_change),
    _auth: None = Depends(require_owner),
):
    _submission, claim = _submission_claim_or_400(submission_id)
    if claim["status"] not in ("submitted",):
        return await _owner_page(
            request,
            {"ok": False, "text": f"claim #{claim['id']} is '{claim['status']}' — only a submitted claim can be approved"},
            status_code=409,
        )
    task = task_by_id(claim["task_id"]) or {"payout_usd": 0}
    store.set_claim_status(claim["id"], "approved")
    decision = payouts.process_approval(claim, task)
    return await _owner_page(
        request,
        {
            "ok": True,
            "text": (
                f"claim #{claim['id']} approved — ${decision['amount_usd']:.2f} recorded as "
                f"OWED ({decision['action']}): " + "; ".join(decision["reasons"])
            ),
        },
    )


@router.post("/owner/submissions/{submission_id}/reject", response_class=HTMLResponse)
async def owner_reject(
    request: Request,
    submission_id: int,
    _guard: None = Depends(guard_state_change),
    _auth: None = Depends(require_owner),
):
    _submission, claim = _submission_claim_or_400(submission_id)
    if claim["status"] in ("paid",):
        return await _owner_page(
            request,
            {"ok": False, "text": f"claim #{claim['id']} is already paid — cannot reject"},
            status_code=409,
        )
    store.set_claim_status(claim["id"], "rejected")
    return await _owner_page(
        request,
        {"ok": True, "text": f"claim #{claim['id']} rejected — its task slot is free again"},
    )


@router.post("/owner/submissions/{submission_id}/mark-paid", response_class=HTMLResponse)
async def owner_mark_paid(
    request: Request,
    submission_id: int,
    _guard: None = Depends(guard_state_change),
    _auth: None = Depends(require_owner),
):
    _submission, claim = _submission_claim_or_400(submission_id)
    if claim["status"] != "approved":
        return await _owner_page(
            request,
            {"ok": False, "text": f"claim #{claim['id']} is '{claim['status']}' — only an approved claim can be marked paid"},
            status_code=409,
        )
    task = task_by_id(claim["task_id"]) or {"payout_usd": 0}
    store.set_claim_status(claim["id"], "paid")
    store.add_ledger_entry(
        claim["id"],
        claim["task_id"],
        claim["email"],
        float(task.get("payout_usd") or 0),
        "paid",
        note="owner marked paid (manual PayPal send — v1 has no live payout rail)",
    )
    return await _owner_page(
        request,
        {"ok": True, "text": f"claim #{claim['id']} marked PAID and written to the ledger"},
    )


@router.get("/owner/export.json")
async def owner_export(request: Request, _: None = Depends(require_owner)):
    """Full-DB JSON export — the backup valve for the ephemeral SQLite disk."""
    return JSONResponse(store.export_all())
