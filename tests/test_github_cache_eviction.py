"""C11 — TTL-cache poison guard for ``app/github._get``.

The client caches every envelope keyed by URL for ``CACHE_TTL_SECONDS``, but
NOT unconditionally: the guard at ``github.py`` line 204 caches only successes
and *stable* negatives (404 absent file, 403/401 scope) — a transient failure
(429 rate limit, 5xx, or a network error → status 0) must never poison the cache
for the whole TTL, or one blip would freeze a page as broken until the TTL
lapses. Nothing pinned either half, so a regression that cached a 5xx (or
stopped caching a 200) would ship green.

These tests drive the REAL ``_get`` against an ``httpx.MockTransport`` (the
guard lives inside ``_get``, so monkeypatching ``_get`` would bypass the code
under test — the same idiom ``test_error_reason_bound`` uses) and read the
module cache directly: cached statuses populate it and serve a ``cached=True``
second read without re-hitting the transport; transient statuses leave it empty
and re-fetch every time. ``refresh=True`` bypass and ``clear_cache`` are pinned
alongside.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import github  # noqa: E402


@pytest.fixture(autouse=True)
def _empty_cache():
    """Every test starts and ends on an empty module cache — the cache is a
    process-global dict shared with every other suite file."""
    github.clear_cache()
    yield
    github.clear_cache()


class _CountingTransport(httpx.MockTransport):
    """A mock transport that counts how many requests actually reach it."""

    def __init__(self, handler):
        self.calls = 0

        def counting(request):
            self.calls += 1
            return handler(request)

        super().__init__(counting)


def _client_for(status: int, *, network_error: bool = False) -> _CountingTransport:
    if network_error:
        def handler(request):
            raise httpx.ConnectError("boom", request=request)
    else:
        def handler(request):
            return httpx.Response(status, json={"message": f"canned {status}"})

    transport = _CountingTransport(handler)
    client = httpx.AsyncClient(transport=transport)
    github.set_clients(client, client)
    return transport


def _get(url: str, refresh: bool = False) -> dict:
    return asyncio.run(github._get(url, refresh=refresh))


# --- statuses that SHOULD be cached: successes + stable negatives ----------

@pytest.mark.parametrize("status", [200, 201, 204, 404, 403, 401])
def test_success_and_stable_negatives_are_cached(status):
    url = f"https://api.test/cached/{status}"
    transport = _client_for(status)
    first = _get(url)
    assert first["status"] == status
    assert first["cached"] is False
    assert github.cache_size() == 1  # populated
    # a second read without refresh is served from the cache, no new request
    second = _get(url)
    assert second["cached"] is True
    assert second["status"] == status
    assert transport.calls == 1  # transport hit exactly once


# --- statuses that must NEVER poison the cache -----------------------------

@pytest.mark.parametrize("status", [429, 500, 502, 503])
def test_transient_failures_are_not_cached(status):
    url = f"https://api.test/transient/{status}"
    transport = _client_for(status)
    first = _get(url)
    assert first["status"] == status
    assert github.cache_size() == 0  # cache left untouched — no poison
    # the next request re-fetches instead of serving a stale failure
    second = _get(url)
    assert second["cached"] is False
    assert transport.calls == 2


def test_network_error_is_status_zero_and_not_cached():
    url = "https://api.test/network-error"
    transport = _client_for(0, network_error=True)
    res = _get(url)
    assert res["status"] == 0  # httpx.HTTPError → status 0 envelope
    assert res["ok"] is False
    assert github.cache_size() == 0  # never cached
    _get(url)
    assert transport.calls == 2  # retried, not frozen


# --- refresh bypass + clear_cache ------------------------------------------

def test_refresh_true_bypasses_and_repopulates_the_cache():
    url = "https://api.test/refresh"
    transport = _client_for(200)
    _get(url)
    assert transport.calls == 1
    # refresh=True ignores the warm entry and re-hits the transport
    fresh = _get(url, refresh=True)
    assert fresh["cached"] is False
    assert transport.calls == 2
    assert github.cache_size() == 1


def test_clear_cache_empties_and_reports_the_drop_count():
    _client_for(200)
    _get("https://api.test/a")
    _get("https://api.test/b")
    assert github.cache_size() == 2
    dropped = github.clear_cache()
    assert dropped == 2
    assert github.cache_size() == 0
