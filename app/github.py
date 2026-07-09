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


def _result(url: str, status: int, data: Any = None, error: str = "") -> dict:
    return {
        "ok": 200 <= status < 300,
        "status": status,
        "data": data,
        "error": error,
        "fetched_at": time.strftime("%H:%M:%S UTC", time.gmtime()),
        "cached": False,
        "url": url,
    }


async def _get(url: str, refresh: bool = False, raw: bool = False) -> dict:
    now = time.monotonic()
    if not refresh:
        hit = _cache.get(url)
        if hit and hit[0] > now:
            out = dict(hit[1])
            out["cached"] = True
            return out
    try:
        resp = await get_client(raw=raw).get(url)
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
            out["error"] = f"decode failed: {exc}"
            return out
    return api_res if not res["ok"] else res


def cache_size() -> int:
    return len(_cache)
