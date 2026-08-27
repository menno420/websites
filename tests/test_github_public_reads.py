"""Privacy and concurrency contract for the shared GitHub read client.

The estate catalogue is public while its server may hold a token that can
read private repositories.  These tests pin the boundary at the lowest
shared layer: public helpers use only the anonymous client, authenticated and
public responses never share cache entries, and simultaneous readers do not
fan out identical GitHub requests.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import github  # noqa: E402


@pytest.fixture(autouse=True)
def _empty_cache():
    github.clear_cache()
    yield
    github.clear_cache()


class _CountingTransport(httpx.MockTransport):
    def __init__(self, handler):
        self.calls = 0

        async def counting(request: httpx.Request) -> httpx.Response:
            self.calls += 1
            result = handler(request)
            if hasattr(result, "__await__"):
                result = await result
            return result

        super().__init__(counting)


def _install_clients(auth_handler, public_handler):
    auth_transport = _CountingTransport(auth_handler)
    public_transport = _CountingTransport(public_handler)
    auth_client = httpx.AsyncClient(
        transport=auth_transport,
        headers={"Authorization": "Bearer private-test-token"},
    )
    public_client = httpx.AsyncClient(transport=public_transport)
    github.set_clients(auth_client, public_client)
    return auth_transport, public_transport


def test_result_keeps_display_time_and_adds_full_utc_iso_instant():
    result = github._result("https://api.test/clock", 200, {})

    assert result["fetched_at"].endswith(" UTC")
    parsed = datetime.fromisoformat(
        result["fetched_at_iso"].replace("Z", "+00:00")
    )
    assert parsed.tzinfo == timezone.utc


def test_public_api_uses_anonymous_client_only():
    def authenticated(request: httpx.Request) -> httpx.Response:
        raise AssertionError("public_api must not use the authenticated client")

    def anonymous(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"visibility": "public"})

    auth, public = _install_clients(authenticated, anonymous)
    result = asyncio.run(github.public_api("/repos/menno420/example"))

    assert result["ok"] is True
    assert result["data"] == {"visibility": "public"}
    assert auth.calls == 0
    assert public.calls == 1


def test_public_file_404_never_falls_back_to_authenticated_contents():
    def authenticated(request: httpx.Request) -> httpx.Response:
        raise AssertionError(
            "fetch_public_file must not probe token-backed Contents"
        )

    def anonymous(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "raw.githubusercontent.com"
        return httpx.Response(404, text="not found")

    auth, public = _install_clients(authenticated, anonymous)
    result = asyncio.run(
        github.fetch_public_file("private-repo", "docs/current-state.md")
    )

    assert result["ok"] is False
    assert result["status"] == 404
    assert auth.calls == 0
    assert public.calls == 1


def test_public_file_preserves_exact_json_text_for_strict_readers():
    raw = '{"count": 0, "count": 1}\n'

    def authenticated(request: httpx.Request) -> httpx.Response:
        raise AssertionError("public file must stay anonymous")

    def anonymous(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=raw,
            headers={"content-type": "application/json"},
        )

    auth, public = _install_clients(authenticated, anonymous)
    result = asyncio.run(
        github.fetch_public_file("fleet-manager", "index.json")
    )

    assert result["data"] == raw
    assert auth.calls == 0
    assert public.calls == 1


def test_public_file_rejects_invalid_utf8_instead_of_replacing_owner_text():
    def anonymous(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b'{"comment":"bad-\xff-byte"}\n',
            headers={"content-type": "application/json"},
        )

    auth, public = _install_clients(
        lambda request: httpx.Response(500), anonymous
    )
    result = asyncio.run(
        github.fetch_public_file("fleet-manager", "comment.json")
    )

    assert result["ok"] is False
    assert result["status"] == 0
    assert "invalid UTF-8" in result["error"]
    assert result["data"] is None
    assert auth.calls == 0
    assert public.calls == 1


def test_authenticated_and_public_reads_have_isolated_cache_entries():
    def authenticated(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer private-test-token"
        return httpx.Response(200, json={"visibility": "private"})

    def anonymous(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(404, json={"message": "Not Found"})

    auth, public = _install_clients(authenticated, anonymous)
    path = "/repos/menno420/private-repo"

    private = asyncio.run(github.api(path))
    visible = asyncio.run(github.public_api(path))
    private_cached = asyncio.run(github.api(path))
    visible_cached = asyncio.run(github.public_api(path))

    assert private["status"] == 200
    assert visible["status"] == 404
    assert private_cached["cached"] is True
    assert visible_cached["cached"] is True
    assert auth.calls == 1
    assert public.calls == 1
    assert github.cache_size() == 2


def test_redirect_following_mode_is_part_of_cache_identity():
    start = "https://downloads.example.test/artifact"
    final = "https://cdn.example.test/artifact"

    def anonymous(request: httpx.Request) -> httpx.Response:
        if str(request.url) == start:
            return httpx.Response(302, headers={"location": final})
        return httpx.Response(200, text="artifact")

    _, public = _install_clients(
        lambda request: httpx.Response(500), anonymous
    )

    followed = asyncio.run(
        github._get(start, raw=True, follow_redirects=True)
    )
    bare = asyncio.run(github._get(start, raw=True))
    followed_cached = asyncio.run(
        github._get(start, raw=True, follow_redirects=True)
    )

    assert followed["status"] == 200
    assert bare["status"] == 302
    assert followed_cached["cached"] is True
    assert public.calls == 3  # redirect + final, then a distinct no-follow read


def test_identical_concurrent_public_misses_share_one_request():
    calls = 0

    async def anonymous(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return httpx.Response(200, json={"name": "example"})

    async def exercise() -> tuple[list[dict], dict]:
        public = httpx.AsyncClient(
            transport=httpx.MockTransport(anonymous)
        )
        authenticated = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            )
        )
        github.set_clients(authenticated, public)
        path = "/repos/menno420/example"
        results = await asyncio.gather(
            *(github.public_api(path) for _ in range(20))
        )
        cached = await github.public_api(path)
        return results, cached

    results, cached = asyncio.run(exercise())

    assert calls == 1
    assert all(result["status"] == 200 for result in results)
    assert all(result["cached"] is False for result in results)
    assert cached["cached"] is True
    assert github._inflight == {}


def test_fresh_uncoalesced_public_read_does_not_join_older_visibility_fetch():
    calls = 0
    old_started = asyncio.Event()
    release_old = asyncio.Event()

    async def anonymous(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        call_number = calls
        if call_number == 1:
            old_started.set()
            await release_old.wait()
            return httpx.Response(200, json=[{"name": "example"}])
        return httpx.Response(200, json=[])

    async def exercise() -> tuple[dict, dict, dict]:
        public = httpx.AsyncClient(transport=httpx.MockTransport(anonymous))
        authenticated = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            )
        )
        github.set_clients(authenticated, public)
        path = "/users/menno420/repos?type=owner"
        old = asyncio.create_task(github.public_api(path, refresh=True))
        await old_started.wait()
        mutation = await github.public_api(
            path,
            refresh=True,
            coalesce=False,
        )
        release_old.set()
        old_result = await old
        cached = await github.public_api(path)
        return mutation, old_result, cached

    mutation, old_result, cached = asyncio.run(exercise())

    assert calls == 2
    assert mutation["data"] == []
    assert old_result["data"] == [{"name": "example"}]
    assert cached["data"] == []
    assert cached["cached"] is True
    assert github._inflight == {}


def test_coalesced_transient_failure_is_not_cached_and_next_read_retries():
    calls = 0

    async def anonymous(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        if calls == 1:
            return httpx.Response(503, json={"message": "try again"})
        return httpx.Response(200, json={"name": "recovered"})

    async def exercise() -> tuple[list[dict], dict, dict]:
        public = httpx.AsyncClient(
            transport=httpx.MockTransport(anonymous)
        )
        authenticated = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            )
        )
        github.set_clients(authenticated, public)
        path = "/repos/menno420/flaky"
        failed = await asyncio.gather(
            *(github.public_api(path) for _ in range(12))
        )
        recovered = await github.public_api(path)
        cached = await github.public_api(path)
        return failed, recovered, cached

    failed, recovered, cached = asyncio.run(exercise())

    assert calls == 2
    assert all(result["status"] == 503 for result in failed)
    assert recovered["status"] == 200
    assert recovered["cached"] is False
    assert cached["cached"] is True
    assert github.cache_size() == 1
    assert github._inflight == {}
