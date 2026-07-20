"""Thin GitHub REST client with a server-side TTL cache.

Every fetch returns a plain dict "result":
    {ok, status, data, error, fetched_at, cached, url}
so templates can render partial failures honestly instead of 500ing —
a board whose whole point is honest state must degrade per-cell.

Caching: in-memory, per-URL, TTL = config.CACHE_TTL_SECONDS (default 3 min).
`refresh=True` (the ?refresh=1 query param upstream) bypasses and repopulates.
"""

from __future__ import annotations

import asyncio
import base64
import re
import time
from typing import Any, Optional

import httpx

from . import config

_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = asyncio.Lock()

_client: Optional[httpx.AsyncClient] = None
_raw_client: Optional[httpx.AsyncClient] = None


def make_client() -> httpx.AsyncClient:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "websites-control-plane",
    }
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    # trust_env=True: honors HTTPS_PROXY / SSL_CERT_FILE when present (dev
    # containers); a plain Railway container simply has none set.
    return httpx.AsyncClient(headers=headers, timeout=20.0, trust_env=True)


def make_raw_client() -> httpx.AsyncClient:
    # NO Authorization header: raw.githubusercontent.com serves public repos
    # anonymously, and sending an API bearer token there makes it 404 when the
    # token is invalid/foreign (verified live 2026-07-09).
    return httpx.AsyncClient(
        headers={"User-Agent": "websites-control-plane"},
        timeout=20.0,
        trust_env=True,
    )


def set_clients(client: httpx.AsyncClient, raw_client: httpx.AsyncClient) -> None:
    global _client, _raw_client
    _client = client
    _raw_client = raw_client


def get_client(raw: bool = False) -> httpx.AsyncClient:
    client = _raw_client if raw else _client
    assert client is not None, "client not initialised (app lifespan)"
    return client


# User-visible failure reasons are banner/cell text everywhere downstream:
# cap them hard AT THE SOURCE so an upstream error DOCUMENT can never flood
# a page again (observed live: a transient GitHub failure returned a full
# HTML error page, which rendered wholesale into /freshness cells — PR #237
# bounded that page; this bounds every envelope so /fleet banners, the
# owner UI, and any future consumer inherit the guard for free). Same cap
# as the #237 precedent (app/freshness.py REASON_MAX_CHARS).
REASON_MAX_CHARS = 140


def short_reason(
    text: Any, limit: int = REASON_MAX_CHARS, status: Any = None
) -> str:
    """A render-safe failure reason — short, single-line, human.

    Collapses whitespace runs (newlines included) to single spaces; a body
    that looks like markup (an HTML error page is a document, not a reason)
    is replaced with a generic "HTTP <status> — non-JSON error body" phrase
    (the envelope status when known); anything still longer than ``limit``
    is hard-truncated with an ellipsis, keeping the head (status code /
    first meaningful words) intact. Meaningful short reasons ("HTTP 404",
    "Not Found") pass through verbatim — honest degradation still says
    WHY, just never in document form.
    """
    flat = re.sub(r"\s+", " ", str(text or "")).strip()
    if not flat:
        return ""
    low = flat.lower()
    if flat.startswith("<") or "<!doctype" in low or "<html" in low:
        prefix = f"HTTP {status} — " if status else ""
        return f"{prefix}non-JSON error body"
    if len(flat) > limit:
        return flat[: limit - 1].rstrip() + "…"
    return flat


def classify_listing(
    result: dict,
    *,
    on_404: str,
    reason_404: Optional[str] = None,
    subject: str = "the listing",
) -> tuple[str, str]:
    """Classify a contents-listing envelope into an honest ``(state, reason)``.

    The ONE degradation ladder for directory-listing consumers (/projects
    overview + detail, the /prompts drift chip, /ideas), replacing the
    hand-rolled per-page copies that had begun to diverge (backlog bullet
    2026-07-12). The honesty contract this encodes: a failed listing is
    NEVER rendered as an empty page — unknown-with-a-reason always beats a
    silently fabricated empty.

    Rungs, in order:

    - ``("ok", "")`` — envelope ok and ``data`` is a list. An EMPTY list is
      still ``ok``: whether an empty directory is a friendly launch state,
      real drift, or a plain absence is the CALLER's meaning to assign.
    - ``(on_404, reason_404 or fetch reason)`` — a 404 means something
      different on every page (projects: the registry hasn't landed →
      "empty"; ideas: this repo keeps no backlog → "missing"; prompts:
      drift can't be judged → "unknown"), so the 404 disposition is an
      explicit parameter — deliberate differences are declared here, not
      re-derived per page.
    - ``("unavailable", "unexpected listing payload (HTTP <status>)")`` —
      ok but ``data`` is not a list (a non-JSON 2xx body): honest about
      the wrong shape instead of a bare "HTTP 200".
    - ``("not-configured", …)`` — any other failure while GITHUB_TOKEN is
      unset names the missing token AND the fetch reason: ``"GITHUB_TOKEN
      is not set on this service and {subject} failed (fetch: {reason})"``.
    - ``("unavailable", <fetch reason>)`` — any other failure.

    Every returned reason — including a caller-supplied ``reason_404`` and
    the composed not-configured text — re-passes :func:`short_reason`, so
    banner text stays hard-bounded at ``REASON_MAX_CHARS`` no matter how it
    was assembled (the #237→#240 precedent extended to composed reasons).
    """
    status = result.get("status")
    base_reason = result.get("error") or f"HTTP {status}"
    if result.get("ok") and isinstance(result.get("data"), list):
        return "ok", ""
    if status == 404:
        return on_404, short_reason(reason_404 or base_reason, status=status)
    if result.get("ok"):
        return "unavailable", short_reason(
            f"unexpected listing payload (HTTP {status})", status=status
        )
    if not config.GITHUB_TOKEN:
        return "not-configured", short_reason(
            f"GITHUB_TOKEN is not set on this service and {subject} "
            f"failed (fetch: {base_reason})",
            status=status,
        )
    return "unavailable", short_reason(base_reason, status=status)


def _result(url: str, status: int, data: Any = None, error: str = "") -> dict:
    return {
        "ok": 200 <= status < 300,
        "status": status,
        "data": data,
        # Every envelope any consumer sees is minted here — sanitizing the
        # error field at this choke point is what bounds ALL downstream
        # reason text (fleet, freshness, owner UI, directory probes, …).
        "error": short_reason(error, status=status or None),
        "fetched_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
        "cached": False,
        "url": url,
    }


async def _get(
    url: str,
    refresh: bool = False,
    raw: bool = False,
    follow_redirects: bool = False,
) -> dict:
    """GET a URL through the TTL cache, returning the honest result envelope.

    ``follow_redirects`` is opt-in per call and defaults ``False`` — the raw
    client is SHARED with ``app/askverify.py``'s Discord-login probes, which
    read a bare ``302`` status as the "configured" signal and would break if
    the redirect were chased. Only the ``/directory`` liveness probe
    (``web_presence.overview``) opts in, so a redirect-hosted download (a
    release asset that 302s to a CDN) is health-probed to its FINAL status
    instead of false-negativing on the 302.
    """
    now = time.monotonic()
    if not refresh:
        hit = _cache.get(url)
        if hit and hit[0] > now:
            out = dict(hit[1])
            out["cached"] = True
            return out
    try:
        resp = await get_client(raw=raw).get(url, follow_redirects=follow_redirects)
        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        err = ""
        if resp.status_code >= 300:
            err = (
                data.get("message", "")
                if isinstance(data, dict)
                else str(data)[:200]
            )
        res = _result(url, resp.status_code, data, err)
    except httpx.HTTPError as exc:
        res = _result(url, 0, None, f"{type(exc).__name__}: {exc}")
    # Cache successes and *stable* negatives (404 absent file, 403 scope).
    # Transient failures (429 rate limit, 5xx, network) must not poison the
    # cache for the whole TTL — retry them on the next request.
    if res["ok"] or res["status"] in (404, 403, 401):
        async with _cache_lock:
            _cache[url] = (now + config.CACHE_TTL_SECONDS, res)
    return res


async def api(path: str, refresh: bool = False) -> dict:
    """GET an api.github.com path (must start with '/')."""
    return await _get(config.GITHUB_API_BASE + path, refresh=refresh)


async def api_post(path: str, json_body: Any = None) -> dict:
    """POST an api.github.com path (must start with '/'). Never cached.

    Used by the gated /owner actions (e.g. re-run a failed workflow). Returns
    the same plain result dict as the GET path so callers degrade honestly on
    403/404 instead of raising.
    """
    url = config.GITHUB_API_BASE + path
    try:
        resp = await get_client().post(url, json=json_body)
        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        err = ""
        if resp.status_code >= 300:
            err = (
                data.get("message", "")
                if isinstance(data, dict)
                else str(data)[:200]
            )
        return _result(url, resp.status_code, data, err)
    except httpx.HTTPError as exc:
        return _result(url, 0, None, f"{type(exc).__name__}: {exc}")


async def api_request(
    method: str, path: str, json_body: Any = None, token: str = ""
) -> dict:
    """Uncached api.github.com request with an optional PER-REQUEST token.

    Backs the ORDER 020 owner-writeback engine (app/writeback.py), which
    reads ``GITHUB_TOKEN`` from the environment at REQUEST time — so a
    write-scoped token pasted into Railway lights up on the next submit
    without a redeploy. A supplied ``token`` overrides the client-level
    Authorization header for this one request (httpx merges per-request
    headers over client headers); empty ``token`` leaves the client header
    (config-time token or none) in force. Same honest result envelope as
    every other call here — callers degrade, never raise.
    """
    url = config.GITHUB_API_BASE + path
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        resp = await get_client().request(
            method, url, json=json_body, headers=headers
        )
        try:
            data = resp.json()
        except ValueError:
            data = resp.text
        err = ""
        if resp.status_code >= 300:
            err = (
                data.get("message", "")
                if isinstance(data, dict)
                else str(data)[:200]
            )
        return _result(url, resp.status_code, data, err)
    except httpx.HTTPError as exc:
        return _result(url, 0, None, f"{type(exc).__name__}: {exc}")


async def latest_failed_run(
    repo: str, branch: str = "main", refresh: bool = True
) -> dict:
    """Resolve the newest FAILED Actions run on ``branch`` — the READ half.

    Backs the owner rerun-ci PREFLIGHT (preview + confirm-time re-check):
    strictly read-only, ``refresh=True`` by default so a decision is never
    made from a cached list. Returns
    ``{ok, repo, branch, run, message}`` — ``run`` is the raw workflow-run
    dict from GitHub (id, name, display_title, head_sha, created_at,
    html_url, …), ``None`` when there is no failed run (still ``ok`` — an
    honest absence, not a fetch failure) or when the listing itself failed
    (``ok=False`` with the reason in ``message``).
    """
    base = f"/repos/{config.OWNER}/{repo}/actions/runs"
    listed = await _get(
        f"{config.GITHUB_API_BASE}{base}"
        f"?branch={branch}&status=failure&per_page=1",
        refresh=refresh,
    )
    if not listed["ok"] or not isinstance(listed["data"], dict):
        reason = listed["error"] or f"HTTP {listed['status']}"
        return {
            "ok": False,
            "repo": repo,
            "branch": branch,
            "run": None,
            "message": f"could not list runs: {reason}",
        }
    runs = listed["data"].get("workflow_runs") or []
    if not runs:
        return {
            "ok": True,
            "repo": repo,
            "branch": branch,
            "run": None,
            "message": f"no failed run on {branch} to re-run (nothing to do)",
        }
    return {"ok": True, "repo": repo, "branch": branch, "run": runs[0], "message": ""}


async def run_info(repo: str, run_id: int, refresh: bool = True) -> dict:
    """GET one Actions run (read-only) — the stale-pin diagnosis and the
    post-fire verification chip both re-check the PINNED run through this.
    Plain result envelope; ``refresh=True`` by default (verification must
    never trust the TTL cache)."""
    return await api(
        f"/repos/{config.OWNER}/{repo}/actions/runs/{run_id}", refresh=refresh
    )


async def run_jobs(repo: str, run_id: int, refresh: bool = True) -> dict:
    """List one Actions run's jobs (read-only) — backs the rerun-ci
    preflight's "jobs that will re-run" facts row and the job-level
    post-fire verification.

    Returns ``{ok, repo, run_id, jobs, total, message}`` — ``jobs`` is the
    raw job list from GitHub (latest attempt: name, status, conclusion,
    html_url, …), ``total`` the run's total job count. ``per_page=100`` —
    this fleet's runs carry a handful of jobs; a >100-job run would need
    pagination this deliberately does not add. Honest degradation on any
    fetch failure (``ok=False`` + reason), never raises."""
    res = await api(
        f"/repos/{config.OWNER}/{repo}/actions/runs/{run_id}/jobs"
        "?per_page=100",
        refresh=refresh,
    )
    if not res["ok"] or not isinstance(res["data"], dict):
        reason = res["error"] or f"HTTP {res['status']}"
        return {
            "ok": False,
            "repo": repo,
            "run_id": run_id,
            "jobs": [],
            "total": 0,
            "message": f"could not list jobs: {reason}",
        }
    jobs = res["data"].get("jobs") or []
    total = res["data"].get("total_count")
    if not isinstance(total, int):
        total = len(jobs)
    return {
        "ok": True,
        "repo": repo,
        "run_id": run_id,
        "jobs": jobs,
        "total": total,
        "message": "",
    }


def failed_jobs(jobs: list) -> list:
    """The subset ``rerun-failed-jobs`` will actually re-run — pure filter,
    tolerant of malformed entries (skipped, never raised on)."""
    return [
        j
        for j in jobs
        if isinstance(j, dict) and j.get("conclusion") == "failure"
    ]


async def rerun_run(
    repo: str, run_id: int, run: Optional[dict] = None, branch: str = "main"
) -> dict:
    """POST rerun-failed-jobs at a PINNED run id — the FIRE half.

    Never resolves anything: the caller supplies the exact run id (and
    optionally the already-resolved run dict, used only for banner copy).
    Returns the same small status dict the owner UI renders — honest about
    the 401/403 scope case rather than 500ing.
    """
    posted = await api_post(
        f"/repos/{config.OWNER}/{repo}/actions/runs/{run_id}/rerun-failed-jobs"
    )
    name = (run or {}).get("name") or (run or {}).get("display_title") or "workflow"
    url = (run or {}).get("html_url", "")
    if posted["ok"]:
        return {
            "ok": True,
            "repo": repo,
            "run_id": run_id,
            "name": name,
            "url": url,
            "message": (
                f"re-ran failed jobs of run #{run_id} ({name}) on {repo}@{branch}"
            ),
        }
    reason = (
        "token lacks actions:write scope"
        if posted["status"] in (403, 401)
        else posted["error"] or f"HTTP {posted['status']}"
    )
    return {
        "ok": False,
        "repo": repo,
        "run_id": run_id,
        "url": url,
        "message": f"re-run rejected for run #{run_id} on {repo}: {reason}",
    }


async def rerun_latest_failed(repo: str, branch: str = "main") -> dict:
    """Re-run the latest FAILED Actions run on ``branch`` for ``repo``.

    Composition of the two halves above (resolve → fire) so the original
    contract keeps working; the owner console itself now goes through the
    preflight (preview pins the id, the confirm fires `rerun_run` only
    after re-verifying the pin), never through this resolve-at-fire-time
    path.
    """
    resolved = await latest_failed_run(repo, branch=branch)
    run = resolved["run"]
    if not resolved["ok"] or run is None:
        return {"ok": False, "repo": repo, "message": resolved["message"]}
    return await rerun_run(repo, run.get("id"), run=run, branch=branch)


async def repo_api(repo: str, subpath: str = "", refresh: bool = False) -> dict:
    return await api(f"/repos/{config.OWNER}/{repo}{subpath}", refresh=refresh)


async def fetch_file(
    repo: str, path: str, ref: str = "main", refresh: bool = False
) -> dict:
    """Fetch a file's text content.

    Raw host first (repos are public; no token burn, no base64), contents API
    as fallback. Result data is the decoded text.
    """
    raw_url = f"{config.GITHUB_RAW_BASE}/{config.OWNER}/{repo}/{ref}/{path}"
    res = await _get(raw_url, refresh=refresh, raw=True)
    if res["ok"] and isinstance(res["data"], (str, dict, list)):
        text = (
            res["data"]
            if isinstance(res["data"], str)
            else __import__("json").dumps(res["data"], indent=2)
        )
        out = dict(res)
        out["data"] = text
        return out
    # Fallback: contents API (base64 payload)
    api_res = await repo_api(repo, f"/contents/{path}?ref={ref}", refresh=refresh)
    if api_res["ok"] and isinstance(api_res["data"], dict) and api_res["data"].get(
        "content"
    ):
        out = dict(api_res)
        try:
            out["data"] = base64.b64decode(api_res["data"]["content"]).decode(
                "utf-8", "replace"
            )
            return out
        except Exception as exc:  # pragma: no cover - corrupt payload
            out["ok"] = False
            out["error"] = short_reason(f"decode failed: {exc}")
            return out
    return api_res if not res["ok"] else res


def cache_size() -> int:
    return len(_cache)


def clear_cache() -> int:
    """Empty the in-memory TTL cache; return how many entries were dropped.

    Backs the gated /owner "force refresh" action — the next page load
    re-fetches everything live. In-process only, no external creds.
    """
    n = len(_cache)
    _cache.clear()
    return n
