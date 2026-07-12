"""Tester-recruitment program — the ``/testing`` section (ORDER 018 PR1).

Public flow: an honest landing page over a committed task catalog
(``testing_tasks.json``), a claim form per open task (no mail provider exists
in this repo, so no magic-code email — the claim response shows a private
tokened link the tester must save; claims are reviewed manually), and a
structured per-type submission form on that private link — now with optional
screenshot upload (≤3 files, ≤2 MB each, png/jpeg only, magic-bytes checked;
stored as SQLite blobs so the owner export captures them; served back only on
the owner queue). On submit, the AI exit-review (``testing_ai.py``, PR2)
grades the report, may ask up to 3 follow-up questions inline on the tester's
status page (answers get ONE re-grade round), and stores a structured report
for the owner queue. No API key / cap hit / API failure → honest degraded
mode: the submission is accepted exactly as before and every page says the
owner reviews manually.

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

Guided walkthroughs (PR3): tasks of type ``guided-walkthrough`` carry a
``steps`` script in the catalog; ``/testing/s/{token}/guide`` walks the tester
through it step by step (plain forms — works with JS disabled and with no API
key) and the finished guide IS the submission, flowing into the same storage
and exit-review as every other type. A side-panel AI guide (chat + optional,
explicitly-consented screen sharing) rides on ``testing_ai.py`` with a
per-claim message cap plus the shared daily cap; screen frames are analyzed
IN MEMORY ONLY and never persisted (test-pinned).

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
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from . import data_source as ds
from . import listfilter
from . import testing_ai as ai
from . import testing_payouts as payouts
from . import testing_store as store
from .testing_catalog import TASKS_PATH, load_tasks  # noqa: F401  (re-export — the
# catalog loader moved to botsite/testing_catalog.py so the tester-task URL
# liveness probe reads tasks through the SAME loader without importing routes)

BASE_DIR = Path(__file__).resolve().parent

router = APIRouter(prefix="/testing")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Total-open-bounty cap: the sum of (non-rejected claims × their task payout)
# may never exceed this. Enforced at claim time, shown on the landing page.
DEFAULT_BOUNTY_CAP_USD = 200.0

_FIELD_MAX = 5000  # per-field input cap (bytes of honesty, not a novel)

_UNAUTH_HEADERS = {"WWW-Authenticate": 'Basic realm="testing owner"'}

# Per-type structured questionnaire: (field name, label, kind). Free-form
# findings are appended for every type. guided-walkthrough deliberately has
# no questionnaire: its structured answers come from the task's `steps`
# script via the /s/{token}/guide flow (ORDER 018 PR3), which ends in the
# same submission storage + exit-review as every other type.
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
    "guided-walkthrough": [],  # step scripts drive this type — see the guide flow
}
SEVERITIES = ["none", "minor", "major", "blocker"]

# Screenshot upload caps (PR2 — the deliberate PR1 deferral, now shipped):
# multipart parsing is the service's one new dependency (python-multipart).
SCREENSHOT_MAX_FILES = 3
SCREENSHOT_MAX_BYTES = 2 * 1024 * 1024  # 2 MB each
# content-type AND magic bytes must both say png/jpeg — never trust either alone.
_SCREENSHOT_TYPES = {"image/png", "image/jpeg"}
_MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
_MAGIC_JPEG = b"\xff\xd8\xff"

# Screen-awareness frames (ORDER 018 PR3): hard server-side cap. The client
# JPEG-encodes at capped quality/scale so real frames land well under this.
FRAME_MAX_BYTES = 1_500_000  # ~1.5 MB


def _screenshot_magic_ok(content_type: str, data: bytes) -> bool:
    if content_type == "image/png":
        return data.startswith(_MAGIC_PNG)
    if content_type == "image/jpeg":
        return data.startswith(_MAGIC_JPEG)
    return False


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
# task catalog (committed JSON, via botsite/testing_catalog.py) + live
# shaping over the store
# --------------------------------------------------------------------------
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


def task_steps(task: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """The guided-walkthrough step script (empty for every other type)."""
    if not task:
        return []
    return [s for s in (task.get("steps") or []) if isinstance(s, dict)]


# --------------------------------------------------------------------------
# ORDER 019 PR2 — filter/sort/search specs over the centralized listfilter
# core (botsite/listfilter.py, a byte-identical vendored copy of
# app/listfilter.py). One spec per surface; no params renders each page
# exactly as before.
# --------------------------------------------------------------------------
PAYOUT_BUCKETS = ("<=10", "11-14", "15+")
EST_BUCKETS = ("<=30", "31-45", "46+")


def payout_bucket(task: dict[str, Any]) -> str:
    """Deterministic payout bucket over ``payout_usd`` (derived, not stored)."""
    p = float(task.get("payout_usd") or 0)
    if p <= 10:
        return "<=10"
    if p < 15:
        return "11-14"
    return "15+"


def est_minutes_bucket(task: dict[str, Any]) -> str:
    """Deterministic time bucket over ``est_minutes`` (derived, not stored)."""
    m = int(task.get("est_minutes") or 0)
    if m <= 30:
        return "<=30"
    if m <= 45:
        return "31-45"
    return "46+"


TASKS_FILTER_SPEC = listfilter.ListSpec(
    path="/testing",
    dimensions=(
        listfilter.Dimension(
            key="type", label="type",
            values=("site-review", "game-test", "guided-walkthrough"),
            get=lambda t: [t.get("type", "")],
        ),
        listfilter.Dimension(
            key="status", label="status",
            values=("open", "coming-soon", "closed"),
            get=lambda t: [t.get("effective_status", "")],
        ),
        listfilter.Dimension(
            key="payout", label="payout", derived=True,
            values=PAYOUT_BUCKETS,
            labels={"<=10": "$10 or less", "11-14": "$11–14", "15+": "$15+"},
            get=lambda t: [payout_bucket(t)],
        ),
        listfilter.Dimension(
            key="time", label="time", derived=True,
            values=EST_BUCKETS,
            labels={"<=30": "≤30 min", "31-45": "31–45 min", "46+": "46+ min"},
            get=lambda t: [est_minutes_bucket(t)],
        ),
    ),
    sorts=(
        # ``catalog`` keeps the committed catalog's own order — the default,
        # so a no-param /testing renders exactly as before.
        listfilter.SortOption("catalog", "catalog order"),
        listfilter.SortOption(
            "payout", "payout high→low",
            sort_key=lambda t: float(t.get("payout_usd") or 0), reverse=True,
        ),
        listfilter.SortOption(
            "minutes", "time short→long",
            sort_key=lambda t: int(t.get("est_minutes") or 0),
        ),
        listfilter.SortOption(
            "title", "title A-Z",
            sort_key=lambda t: str(t.get("title") or "").casefold(),
        ),
    ),
    search=lambda t: " ".join(
        str(t.get(k) or "") for k in ("title", "brief", "id")
    ),
)


def _submission_search_text(s: dict[str, Any]) -> str:
    parts = [str(s.get(k) or "") for k in ("name", "email", "task_id", "findings")]
    answers = s.get("answers")
    if isinstance(answers, dict):
        parts.extend(str(v) for v in answers.values())
    return " ".join(parts)


OWNER_FILTER_SPEC = listfilter.ListSpec(
    path="/testing/owner",
    dimensions=(
        listfilter.Dimension(
            key="status", label="claim status",
            values=("submitted", "reviewed", "approved", "rejected", "paid"),
            get=lambda s: [s.get("claim_status", "")],
        ),
        listfilter.Dimension(
            key="task", label="task",
            get=lambda s: [s.get("task_id", "")],
        ),
        listfilter.Dimension(
            key="date", label="date", derived=True,
            get=lambda s: [str(s.get("created_at") or "")[:10] or "undated"],
        ),
    ),
    sorts=(
        # ``newest`` keeps the store's own id-DESC order — the default, so a
        # no-param owner queue renders exactly as before.
        listfilter.SortOption("newest", "newest"),
        listfilter.SortOption(
            "oldest", "oldest", sort_key=lambda s: int(s.get("id") or 0),
        ),
    ),
    search=_submission_search_text,
)


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
    tasks = shaped_tasks()
    state = listfilter.parse(TASKS_FILTER_SPEC, request.query_params)
    ctx.update(
        {
            "tasks": tasks,
            "tasks_filter": listfilter.apply(TASKS_FILTER_SPEC, tasks, state),
            "bounty": _bounty(),
        }
    )
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
    review = None
    screenshots: list[dict[str, Any]] = []
    if submission:
        try:
            answers = json.loads(submission.get("answers_json") or "{}")
        except ValueError:
            answers = {}
        review = store.ai_review_for_submission(submission["id"])
        screenshots = store.screenshots_for_submission(submission["id"])
    return {
        "claim": claim,
        "task": task,
        "submission": submission,
        "answers": answers,
        "review": review,
        "screenshots": screenshots,
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


async def _validate_screenshots(form: Any) -> list[tuple[str, str, bytes]]:
    """Validate uploaded screenshots; returns (filename, content_type, data).

    Raises ValueError with a tester-facing message on any cap/type violation.
    Empty file inputs (browser sends one when nothing is picked) are skipped.
    """
    uploads = []
    for item in form.getlist("screenshots"):
        # Text fields also land in getlist when names collide; only keep files.
        if isinstance(item, str):
            continue
        filename = (item.filename or "").strip()
        data = await item.read()
        if not filename and not data:
            continue  # empty file input
        uploads.append((filename, (item.content_type or "").lower(), data))
    if len(uploads) > SCREENSHOT_MAX_FILES:
        raise ValueError(
            f"Too many screenshots — at most {SCREENSHOT_MAX_FILES} files."
        )
    out = []
    for filename, content_type, data in uploads:
        if content_type not in _SCREENSHOT_TYPES:
            raise ValueError("Screenshots must be PNG or JPEG images.")
        if len(data) > SCREENSHOT_MAX_BYTES:
            raise ValueError("Each screenshot must be 2 MB or smaller.")
        if not data or not _screenshot_magic_ok(content_type, data):
            raise ValueError(
                "That file doesn't look like a real PNG/JPEG image."
            )
        out.append(((filename or "screenshot")[:200], content_type, data))
    return out


def _run_exit_review(
    submission: dict[str, Any], claim: dict[str, Any], task: Optional[dict[str, Any]]
) -> None:
    """Grade the fresh submission; degrade honestly on any failure.

    Deliberately SYNCHRONOUS (decide-and-flag): the call is bounded (~15 s
    timeout, one retry max) and running it inline means the tester sees the
    follow-up questions immediately on the confirmation page instead of on a
    later refresh — and the flow stays deterministic under test. A failure
    here can never lose the submission: it is already stored.
    """
    answers: dict[str, Any] = {}
    try:
        answers = json.loads(submission.get("answers_json") or "{}")
    except ValueError:
        pass
    findings = submission.get("findings") or ""
    if not ai.available():
        store.save_ai_review(
            submission["id"],
            status="degraded",
            degraded_reason=f"{ai.ENV_API_KEY} is not set on the service",
        )
        return
    try:
        report = ai.grade_submission(task or {}, answers, findings)
    except ai.AIReviewUnavailable as exc:
        store.save_ai_review(
            submission["id"], status="degraded", degraded_reason=str(exc), calls_used=1
        )
        return
    followups = [{"question": q, "answer": None} for q in report["followup_questions"]]
    status = "pending-followup" if followups else "reviewed"
    store.save_ai_review(
        submission["id"],
        status=status,
        score=report["score"],
        low_effort=report["low_effort"],
        summary=report["summary"],
        findings=report["findings"],
        followups=followups,
        calls_used=1,
    )
    if not followups:
        store.set_claim_status(claim["id"], "reviewed")


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
    form = await request.form()  # multipart (python-multipart) or urlencoded
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
    try:
        screenshots = await _validate_screenshots(form)
    except ValueError as exc:
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": str(exc)})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=400
        )
    submission = store.create_submission(claim["id"], answers, findings)
    for filename, content_type, data in screenshots:
        store.add_screenshot(submission["id"], filename, content_type, data)
    store.set_claim_status(claim["id"], "submitted")
    _run_exit_review(submission, claim, task)
    refreshed = store.claim_by_token(token)
    ctx.update(_submission_ctx(refreshed))
    ctx.update({"error": None})
    return templates.TemplateResponse(request, "testing_submission.html", ctx)


@router.post("/s/{token}/followups", response_class=HTMLResponse)
async def testing_followups(
    request: Request, token: str, _: None = Depends(guard_state_change)
):
    """Tester answers the AI's follow-up questions → ONE re-grade round."""
    claim = store.claim_by_token(token)
    if claim is None:
        raise HTTPException(status_code=404, detail="unknown submission link")
    submission = store.submission_for_claim(claim["id"])
    review = store.ai_review_for_submission(submission["id"]) if submission else None
    ctx = await _ctx(request)
    if not submission or not review or review["status"] != "pending-followup":
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": "There are no open follow-up questions on this claim."})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=409
        )
    form = await request.form()
    transcript = []
    any_answer = False
    for i, entry in enumerate(review["followups"]):
        answer = _clean(form, f"followup_{i}")
        any_answer = any_answer or bool(answer)
        transcript.append({"question": entry["question"], "answer": answer})
    if not any_answer:
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": "Answer at least one follow-up question."})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=400
        )
    answers: dict[str, Any] = {}
    try:
        answers = json.loads(submission.get("answers_json") or "{}")
    except ValueError:
        pass
    task = task_by_id(claim["task_id"])
    calls_used = int(review.get("calls_used") or 0)
    try:
        ai.check_submission_cap(calls_used)
        report = ai.regrade_with_followups(
            task or {}, answers, submission.get("findings") or "", transcript
        )
    except ai.AIReviewUnavailable as exc:
        # Honest fallback: keep the original grade, store the tester's answers,
        # note that the re-grade round was unavailable. The tester did their
        # part — the claim moves to reviewed either way.
        store.save_ai_review(
            submission["id"],
            status="reviewed",
            score=review.get("score"),
            low_effort=bool(review.get("low_effort")),
            summary=review.get("summary") or "",
            findings=review.get("findings") or [],
            followups=transcript,
            degraded_reason=f"re-grade round unavailable: {exc}",
            calls_used=calls_used,
        )
        store.set_claim_status(claim["id"], "reviewed")
        refreshed = store.claim_by_token(token)
        ctx.update(_submission_ctx(refreshed))
        ctx.update({"error": None})
        return templates.TemplateResponse(request, "testing_submission.html", ctx)
    store.save_ai_review(
        submission["id"],
        status="reviewed",
        score=report["score"],
        low_effort=report["low_effort"],
        summary=report["summary"],
        findings=report["findings"],
        followups=transcript,
        calls_used=calls_used + 1,
    )
    store.set_claim_status(claim["id"], "reviewed")
    refreshed = store.claim_by_token(token)
    ctx.update(_submission_ctx(refreshed))
    ctx.update({"error": None})
    return templates.TemplateResponse(request, "testing_submission.html", ctx)


# --------------------------------------------------------------------------
# guided walkthrough (ORDER 018 PR3) — step flow + AI side panel + screen
# awareness v1. The step flow is plain forms (works with JS disabled and
# with no API key); chat and frames are progressive enhancements that count
# against the shared AI spend caps. Frames are processed IN MEMORY ONLY —
# this path deliberately contains no store write (test-pinned).
# --------------------------------------------------------------------------
def _guide_claim_task(token: str) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Resolve claim + guided task + steps or raise 404 (wrong token, or the
    task is not a guided walkthrough with a step script)."""
    claim = store.claim_by_token(token)
    if claim is None:
        raise HTTPException(status_code=404, detail="unknown submission link")
    task = task_by_id(claim["task_id"])
    steps = task_steps(task)
    if task is None or not steps:
        raise HTTPException(
            status_code=404, detail="this claim's task has no guided walkthrough"
        )
    return claim, task, steps


def _guide_ctx(
    request: Request,
    claim: dict[str, Any],
    task: dict[str, Any],
    steps: list[dict[str, Any]],
    step_index: int,
    carried: dict[int, str],
    findings: str,
    error: Optional[str],
) -> dict[str, Any]:
    return {
        "claim": claim,
        "task": task,
        "steps": steps,
        "step_index": step_index,
        "carried": carried,
        "findings_carry": findings,
        "error": error,
        "ai_available": ai.available(),
        "guide_cap": ai.guide_cap(),
        "guide_used": ai.guide_calls_used(claim["id"]),
        "frame_max_bytes": FRAME_MAX_BYTES,
    }


@router.get("/s/{token}/guide", response_class=HTMLResponse)
async def testing_guide_page(request: Request, token: str):
    claim, task, steps = _guide_claim_task(token)
    if claim["status"] != "claimed":
        # Already submitted — the status page owns the story from here.
        return RedirectResponse(f"/testing/s/{token}", status_code=303)
    ctx = await _ctx(request)
    ctx.update(_guide_ctx(request, claim, task, steps, 0, {}, "", None))
    return templates.TemplateResponse(request, "testing_guide.html", ctx)


@router.post("/s/{token}/guide", response_class=HTMLResponse)
async def testing_guide_step(
    request: Request, token: str, _: None = Depends(guard_state_change)
):
    """Step advance / back / final submit. Answers ride hidden fields between
    steps (stateless server — nothing is stored until the final submit, which
    reuses the exact submission + exit-review path every other type takes)."""
    claim, task, steps = _guide_claim_task(token)
    ctx = await _ctx(request)
    if claim["status"] != "claimed":
        ctx.update(_submission_ctx(claim))
        ctx.update({"error": "This claim already has a submission — it's in review."})
        return templates.TemplateResponse(
            request, "testing_submission.html", ctx, status_code=409
        )
    form = await request.form()
    try:
        step_index = int(str(form.get("step") or "0"))
    except ValueError:
        step_index = 0
    step_index = max(0, min(step_index, len(steps) - 1))
    carried = {i: _clean(form, f"answer_{i}") for i in range(len(steps))}
    findings = _clean(form, "findings")
    nav = str(form.get("nav") or "next")

    if nav == "back":
        back_to = max(0, step_index - 1)
        ctx.update(_guide_ctx(request, claim, task, steps, back_to, carried, findings, None))
        return templates.TemplateResponse(request, "testing_guide.html", ctx)

    if not carried.get(step_index):
        ctx.update(
            _guide_ctx(
                request, claim, task, steps, step_index, carried, findings,
                "Answer this step's question before moving on — that answer is the report.",
            )
        )
        return templates.TemplateResponse(
            request, "testing_guide.html", ctx, status_code=400
        )

    if step_index < len(steps) - 1:
        ctx.update(
            _guide_ctx(request, claim, task, steps, step_index + 1, carried, findings, None)
        )
        return templates.TemplateResponse(request, "testing_guide.html", ctx)

    # Final step answered → this IS the submission (same storage, same
    # exit-review, same status flow as every other task type).
    answers = {
        f"step_{i + 1}: {steps[i].get('title') or ''}"[:200]: carried[i]
        for i in range(len(steps))
        if carried.get(i)
    }
    submission = store.create_submission(claim["id"], answers, findings)
    store.set_claim_status(claim["id"], "submitted")
    _run_exit_review(submission, claim, task)
    refreshed = store.claim_by_token(token)
    ctx.update(_submission_ctx(refreshed))
    ctx.update({"error": None})
    return templates.TemplateResponse(request, "testing_submission.html", ctx)


def _guide_panel_json(
    claim: dict[str, Any], *, ok: bool, reply: str, degraded: bool = False,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        {
            "ok": ok,
            "reply": reply,
            "degraded": degraded,
            "used": ai.guide_calls_used(claim["id"]),
            "cap": ai.guide_cap(),
        },
        status_code=status_code,
    )


def _guide_step_index(raw: Any, steps: list[dict[str, Any]]) -> int:
    try:
        idx = int(str(raw))
    except (ValueError, TypeError):
        idx = 0
    return max(0, min(idx, len(steps) - 1))


@router.post("/s/{token}/guide/chat")
async def testing_guide_chat(
    request: Request, token: str, _: None = Depends(guard_state_change)
):
    """Side-panel chat. Guarded like every state change; per-claim guide cap
    + shared daily cap; degrades to honest copy without a key."""
    claim, task, steps = _guide_claim_task(token)
    if claim["status"] != "claimed":
        return _guide_panel_json(
            claim, ok=False,
            reply="This claim is already submitted — the guide session is over.",
            status_code=409,
        )
    try:
        body = await request.json()
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}
    message = str(body.get("message") or "").strip()[:_FIELD_MAX]
    if not message:
        return _guide_panel_json(
            claim, ok=False, reply="Type a question first.", status_code=400
        )
    step_index = _guide_step_index(body.get("step"), steps)
    if not ai.available():
        return _guide_panel_json(
            claim, ok=False, degraded=True,
            reply=(
                "The AI guide is offline (no API key is configured on the "
                "server). The step-by-step walkthrough works fully without it."
            ),
        )
    try:
        ai.consume_guide_call(claim["id"])
        reply = ai.guide_reply(task, steps, step_index, message)
    except ai.AIReviewUnavailable as exc:
        return _guide_panel_json(
            claim, ok=False, degraded=True,
            reply=f"The AI guide is unavailable right now ({exc}). "
            "The steps keep working without it.",
        )
    return _guide_panel_json(claim, ok=True, reply=reply)


@router.post("/s/{token}/guide/frame")
async def testing_guide_frame(
    request: Request, token: str, _: None = Depends(guard_state_change)
):
    """Screen-awareness v1: ONE shared-screen frame in, one guiding question
    out. PRIVACY CONTRACT (test-pinned): the frame lives only in this
    request's memory — it is sent to the vision model and discarded; this
    handler performs NO store write, and nothing here logs the bytes."""
    claim, task, steps = _guide_claim_task(token)
    if claim["status"] != "claimed":
        return _guide_panel_json(
            claim, ok=False,
            reply="This claim is already submitted — the guide session is over.",
            status_code=409,
        )
    # Cheap early reject on the declared size before reading the body.
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > FRAME_MAX_BYTES + 4096:
        return _guide_panel_json(
            claim, ok=False,
            reply="That frame is too large — the page sends smaller ones automatically.",
            status_code=413,
        )
    form = await request.form()
    frame = form.get("frame")
    if frame is None or isinstance(frame, str):
        return _guide_panel_json(
            claim, ok=False, reply="No frame was attached.", status_code=400
        )
    data = await frame.read()
    if len(data) > FRAME_MAX_BYTES:
        return _guide_panel_json(
            claim, ok=False,
            reply="That frame is too large — the page sends smaller ones automatically.",
            status_code=413,
        )
    if not data or not data.startswith(_MAGIC_JPEG):
        return _guide_panel_json(
            claim, ok=False,
            reply="That frame doesn't look like a JPEG image.",
            status_code=400,
        )
    step_index = _guide_step_index(form.get("step"), steps)
    if not ai.available():
        return _guide_panel_json(
            claim, ok=False, degraded=True,
            reply=(
                "The AI guide is offline (no API key is configured on the "
                "server), so screen sharing has nothing to talk to."
            ),
        )
    try:
        ai.consume_guide_call(claim["id"])
        reply = ai.guide_screen_question(task, steps, step_index, data)
    except ai.AIReviewUnavailable as exc:
        return _guide_panel_json(
            claim, ok=False, degraded=True,
            reply=f"The AI guide is unavailable right now ({exc}). "
            "The steps keep working without it.",
        )
    # `data` goes out of scope here — never persisted, by design.
    return _guide_panel_json(claim, ok=True, reply=reply)


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
        s["review"] = store.ai_review_for_submission(s["id"])
        s["screenshots"] = store.screenshots_for_submission(s["id"])
        # Would-auto-pay preview: the REAL eligibility gate, evaluated
        # read-only per submission so the owner sees yes/no + every reason.
        if s["claim_status"] in ("submitted", "reviewed"):
            review = s["review"] or {}
            claim_row = {
                "id": s["claim_id"],
                "task_id": s["task_id"],
                "email": s["email"],
            }
            s["autopay_preview"] = payouts.decide_payout(
                claim_row,
                task_by_id(s["task_id"]) or {"payout_usd": 0},
                ai_score=review.get("score"),
                ai_low_effort=bool(review.get("low_effort")),
            )
        else:
            s["autopay_preview"] = None
    # ORDER 019 PR2: filter/sort/search over the submissions queue (the
    # centralized listfilter core; state lives in the GET query string, so
    # POST-action re-renders simply show the unfiltered default).
    state = listfilter.parse(OWNER_FILTER_SPEC, request.query_params)
    submissions_filter = listfilter.apply(OWNER_FILTER_SPEC, submissions, state)
    ctx = await _ctx(request)
    ctx.update(
        {
            "submissions_filter": submissions_filter,
            "tasks": shaped_tasks(),
            "claims": store.list_claims(),
            "submissions": submissions,
            "ledger": store.ledger_entries(),
            "ledger_totals": store.ledger_totals(),
            "bounty": _bounty(),
            "payout_config": payouts.payout_config_summary(),
            "ai_state": ai.state_summary(),
            "degraded_reviews": store.degraded_review_count(),
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
    submission, claim = _submission_claim_or_400(submission_id)
    if claim["status"] not in ("submitted", "reviewed"):
        return await _owner_page(
            request,
            {"ok": False, "text": f"claim #{claim['id']} is '{claim['status']}' — only a submitted/reviewed claim can be approved"},
            status_code=409,
        )
    task = task_by_id(claim["task_id"]) or {"payout_usd": 0}
    store.set_claim_status(claim["id"], "approved")
    review = store.ai_review_for_submission(submission["id"]) or {}
    decision = payouts.process_approval(
        claim,
        task,
        ai_score=review.get("score"),
        ai_low_effort=bool(review.get("low_effort")),
    )
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


@router.get("/owner/screenshots/{shot_id}")
async def owner_screenshot(
    request: Request, shot_id: int, _: None = Depends(require_owner)
):
    """Serve one uploaded screenshot blob — OWNER-ONLY, never public.

    Content-Disposition + nosniff keep the visitor-supplied bytes inert:
    the browser downloads/renders them as an image, never as a document.
    """
    shot = store.screenshot_by_id(shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail="unknown screenshot")
    return Response(
        content=shot["data"],
        media_type=shot["content_type"],
        headers={
            "Content-Disposition": f'inline; filename="screenshot-{shot_id}"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/owner/export.json")
async def owner_export(request: Request, _: None = Depends(require_owner)):
    """Full-DB JSON export — the backup valve for the ephemeral SQLite disk."""
    return JSONResponse(store.export_all())
