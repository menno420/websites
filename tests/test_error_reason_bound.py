"""Source-level bound on envelope error reasons (app/github.py).

PR #237 bounded raw upstream error bodies page-side on /freshness only;
these tests pin the SOURCE fix: ``github._result`` routes every envelope's
``error`` field through ``github.short_reason`` (whitespace collapse,
markup body -> generic "HTTP <status> — non-JSON error body", hard
140-char ellipsis cap, short plain reasons verbatim), so /fleet banners,
the owner UI, /directory probes and every other consumer inherit a short,
single-line, markup-free reason.

Zero network: ``_get`` runs for real against an ``httpx.MockTransport``
client (the sanitizer lives inside the envelope constructor, so
monkeypatching ``_get`` — the usual idiom — would bypass the code under
test). The render test drives /fleet through the same mock transport.
"""

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github  # noqa: E402
from app.main import app  # noqa: E402

CAP = github.REASON_MAX_CHARS  # 140 — the #237 precedent

# Distinctive marker that would only appear in a page if a raw upstream
# error document leaked through (echoes the live-observed GitHub page).
SENTINEL = "HELLO-FUTURE-GITHUBBER-SENTINEL"

HTML_ERROR_PAGE = (
    "<!DOCTYPE html>\n<html>\n  <head><title>Server Error</title></head>\n"
    f"  <body>\n    <!-- {SENTINEL} -->\n    <h1>Unicorn!</h1>\n"
    + ("    <p>Something went terribly wrong.</p>\n" * 200)
    + "  </body>\n</html>\n"
)


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _fetch(monkeypatch, response: httpx.Response, url: str) -> dict:
    """Run the real ``_get`` against a canned httpx response."""
    client = _mock_client(lambda request: response)
    monkeypatch.setattr(github, "get_client", lambda raw=False: client)
    try:
        return asyncio.run(github._get(url, refresh=True))
    finally:
        asyncio.run(client.aclose())


def _assert_bounded_plain(reason: str):
    assert len(reason) <= CAP
    assert "\n" not in reason and "\r" not in reason
    assert "<" not in reason and ">" not in reason


# --------------------------------------------------------------------------- #
# (a) envelope-level: the four required body shapes
# --------------------------------------------------------------------------- #

def test_html_error_page_body_becomes_generic_reason(monkeypatch):
    res = _fetch(
        monkeypatch,
        httpx.Response(503, text=HTML_ERROR_PAGE),
        "https://api.example/html-error",
    )
    assert res["ok"] is False and res["status"] == 503
    # The useful head survives: the status code leads the phrase.
    assert res["error"] == "HTTP 503 — non-JSON error body"
    _assert_bounded_plain(res["error"])
    assert SENTINEL not in res["error"]


def test_huge_plain_body_truncated_with_ellipsis(monkeypatch):
    huge = ("upstream exploded spectacularly " * 2000).strip()  # ~64 KB
    assert len(huge) > 40_000
    res = _fetch(
        monkeypatch,
        httpx.Response(500, text=huge),
        "https://api.example/huge-body",
    )
    assert res["ok"] is False
    _assert_bounded_plain(res["error"])
    assert res["error"].endswith("…")
    # Head preserved: the reason starts with the body's first words.
    assert res["error"].startswith("upstream exploded spectacularly")


def test_multiline_body_collapses_to_single_line(monkeypatch):
    body = "bad gateway: origin refused\n\n  retry later\n\ttrace-id 12345"
    res = _fetch(
        monkeypatch,
        httpx.Response(502, text=body),
        "https://api.example/multiline",
    )
    assert res["ok"] is False
    _assert_bounded_plain(res["error"])
    # First meaningful line leads; whitespace runs become single spaces.
    assert res["error"] == (
        "bad gateway: origin refused retry later trace-id 12345"
    )


def test_short_plain_reasons_pass_verbatim(monkeypatch):
    # JSON message path (the GitHub API's normal error shape).
    res = _fetch(
        monkeypatch,
        httpx.Response(404, json={"message": "Not Found"}),
        "https://api.example/short-json",
    )
    assert res["error"] == "Not Found"
    # Plain-text short body: a no-op.
    res2 = _fetch(
        monkeypatch,
        httpx.Response(429, text="rate limited"),
        "https://api.example/short-plain",
    )
    assert res2["error"] == "rate limited"


def test_ok_responses_keep_empty_error(monkeypatch):
    res = _fetch(
        monkeypatch,
        httpx.Response(200, json={"fine": True}),
        "https://api.example/ok",
    )
    assert res["ok"] is True and res["error"] == ""


def test_short_reason_helper_direct():
    # Empty stays empty; markup without a status gets the bare phrase.
    assert github.short_reason("") == ""
    assert github.short_reason(None) == ""
    assert github.short_reason("<html><body>x</body></html>") == (
        "non-JSON error body"
    )
    assert github.short_reason("HTTP 404") == "HTTP 404"
    long = "x" * 500
    out = github.short_reason(long)
    assert len(out) <= CAP and out.endswith("…")


# --------------------------------------------------------------------------- #
# (b) render-level: a consuming page inherits the bound
# --------------------------------------------------------------------------- #

def test_fleet_page_renders_bounded_reason_not_error_document(monkeypatch):
    """/fleet during a full upstream outage: every fetch returns the huge
    HTML error page; banners must show the generic bounded phrase, and the
    raw document must appear nowhere in the rendered output."""
    github.clear_cache()
    client = _mock_client(
        lambda request: httpx.Response(503, text=HTML_ERROR_PAGE)
    )
    monkeypatch.setattr(github, "get_client", lambda raw=False: client)
    try:
        with TestClient(app) as c:
            resp = c.get("/fleet")
    finally:
        asyncio.run(client.aclose())
        github.clear_cache()
    assert resp.status_code == 200
    assert SENTINEL not in resp.text
    assert "Unicorn!" not in resp.text
    # The honest-degradation banner still says WHY, in bounded form.
    assert "non-JSON error body" in resp.text
