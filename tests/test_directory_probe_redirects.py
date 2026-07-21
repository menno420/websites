"""Slice 6 — the /directory .gba download probe follows redirects.

The web-presence directory (`app/web_presence.py`, ORDER 021) probes each
`probe:true` row's URL live through the shared tokenless raw client
(`github._get(url, raw=True)`). A release-download URL (the Lumen Drift `.gba`
asset) 302-redirects to a CDN, so the probe must follow the redirect and judge
the FINAL status — otherwise a live download false-negatives as
"degraded (HTTP 302)".

These tests drive the REAL `github._get` against an `httpx.MockTransport` (the
`test_github_cache_eviction` idiom — monkeypatching `_get` would bypass the
follow-redirects code under test) and pin the contract BOTH ways:

* with `follow_redirects=True` (what `web_presence.overview` passes) a
  302 → 200 chain resolves to a reachable 200, and a 302 → 404 chain surfaces
  the final 404 — the probe judges the END of the chain, never the hop;
* with the DEFAULT `follow_redirects=False` a 302 stays a 302 — the no-follow
  contract `app/askverify.py`'s Discord-login probes depend on (they read the
  bare 302 status itself as the "configured" signal) is preserved.

A final `overview()` integration test asserts a redirect-hosted download row
renders `data-health="live"`, not degraded.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import github, web_presence  # noqa: E402

RELEASE_URL = "https://github.com/menno420/gba-homebrew/releases/download/lumen-drift-v1.3/lumen-drift.gba"
CDN_URL = "https://cdn.example.net/objects/lumen-drift.gba"


@pytest.fixture(autouse=True)
def _empty_cache():
    """The module cache is a process-global dict shared across suites — start
    and end each test on an empty one so a canned envelope never leaks."""
    github.clear_cache()
    yield
    github.clear_cache()


def _install(handler) -> None:
    """Route the real raw + api clients through a MockTransport — no socket."""
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    github.set_clients(client, client)


def _get(url: str, **kw) -> dict:
    return asyncio.run(github._get(url, **kw))


# --- _get follow-redirects contract --------------------------------------------


def test_302_to_200_chain_is_reachable_when_following():
    """The slice's core pin: a release-download 302 → CDN 200 chain probed with
    follow_redirects=True yields a reachable FINAL 200 (not the 302 hop)."""
    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == RELEASE_URL:
            return httpx.Response(302, headers={"location": CDN_URL})
        return httpx.Response(200, text="rom bytes")

    _install(handler)
    res = _get(RELEASE_URL, raw=True, follow_redirects=True)
    assert res["ok"] is True
    assert res["status"] == 200


def test_302_to_404_chain_surfaces_the_final_404_when_following():
    """Honest to the END of the chain: a redirect landing on a dead asset is
    degraded on the FINAL 404, never a green pass off the 302 hop."""
    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == RELEASE_URL:
            return httpx.Response(302, headers={"location": CDN_URL})
        return httpx.Response(404)

    _install(handler)
    res = _get(RELEASE_URL, raw=True, follow_redirects=True)
    assert res["ok"] is False
    assert res["status"] == 404


def test_302_stays_302_by_default_preserving_the_askverify_signal():
    """Default (no follow): a 302 returns the bare 302 status — the signal
    app/askverify.py's Discord-login probes read as 'configured'. This is why
    the fix is opt-in per call, not a client-level change."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": CDN_URL})

    _install(handler)
    res = _get(RELEASE_URL, raw=True)  # follow_redirects defaults False
    assert res["status"] == 302
    assert res["ok"] is False


# --- /directory overview integration -------------------------------------------


def test_directory_overview_renders_redirect_hosted_download_as_live():
    """End-to-end through web_presence.overview: with the probe following
    redirects, the Lumen Drift .gba row (302 → CDN 200) reports health 'live'."""
    def handler(req: httpx.Request) -> httpx.Response:
        if str(req.url) == RELEASE_URL:
            return httpx.Response(302, headers={"location": CDN_URL})
        return httpx.Response(200, text="ok")

    _install(handler)
    data = asyncio.run(web_presence.overview())
    rows = data["our_sites"] + data["external"]
    lumen = next(r for r in rows if r.get("id") == "lumen-drift")
    assert lumen.get("probe") is True  # the committed registry row is probed now
    assert lumen["health"]["state"] == "live"
    assert lumen["health"]["detail"] == "HTTP 200"
