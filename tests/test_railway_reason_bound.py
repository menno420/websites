"""Source-level bound on Railway error reasons (app/railway.py).

PR #240 bounded every GitHub-envelope error reason at the source
(``github.short_reason``: whitespace collapse, markup body -> generic
"HTTP <status> — non-JSON error body", hard 140-char ellipsis cap, short
plain reasons verbatim). ``app/railway.py`` minted its OWN GraphQL error
strings with only a bare ``[:300]`` cap and no bound at all on the httpx
exception path — so a Railway failure could paint raw upstream error
text, including HTML, onto the owner environments/envhub/envdrift
banners. These tests pin the alignment: every reason minted in
``railway._graphql`` rides the same ``short_reason`` bound.

Zero network: ``_graphql`` runs for real against an
``httpx.MockTransport`` client handed in through ``railway._make_client``
(the #240 idiom — monkeypatching ``_graphql`` itself, the usual idiom in
tests/test_owner_environments.py, would bypass the code under test). The
render test drives /owner/environments through the same mock transport.
"""

import asyncio
import base64
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, railway  # noqa: E402
from app.main import app  # noqa: E402

CAP = github.REASON_MAX_CHARS  # 140 — the #237/#240 precedent

# Distinctive marker that would only appear in a reason/page if a raw
# upstream error document leaked through.
SENTINEL = "HELLO-FUTURE-RAILWAYER-SENTINEL"

HTML_ERROR_PAGE = (
    "<!DOCTYPE html>\n<html>\n  <head><title>Server Error</title></head>\n"
    f"  <body>\n    <!-- {SENTINEL} -->\n    <h1>Unicorn!</h1>\n"
    + ("    <p>Something went terribly wrong.</p>\n" * 200)
    + "  </body>\n</html>\n"
)

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def _isolate_railway_cache():
    railway.clear_cache()
    yield
    railway.clear_cache()


def _graphql_via(monkeypatch, handler) -> dict:
    """Run the real ``_graphql`` against a canned httpx handler."""
    monkeypatch.setattr(
        railway,
        "_make_client",
        lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    return asyncio.run(railway._graphql("query { projectToken { projectId } }"))


def _assert_bounded_plain(reason: str):
    assert len(reason) <= CAP
    assert "\n" not in reason and "\r" not in reason
    assert "<" not in reason and ">" not in reason


# --------------------------------------------------------------------------- #
# (a) mint-level: the required body shapes, through the real _graphql
# --------------------------------------------------------------------------- #


def test_html_error_page_body_stays_out_of_the_reason(monkeypatch):
    """Upstream 503 serving a full HTML document → the bounded status
    phrase, never the document (the non-JSON-body mint site)."""
    res = _graphql_via(
        monkeypatch, lambda request: httpx.Response(503, text=HTML_ERROR_PAGE)
    )
    assert res["ok"] is False and res["data"] is None
    assert res["error"] == "HTTP 503: non-JSON response"
    _assert_bounded_plain(res["error"])
    assert SENTINEL not in res["error"]


def test_html_graphql_error_message_becomes_generic_phrase(monkeypatch):
    """A GraphQL errors[].message that is itself an HTML document (JSON
    envelope, 200) → the generic markup-replacement phrase, bounded."""
    res = _graphql_via(
        monkeypatch,
        lambda request: httpx.Response(
            200, json={"errors": [{"message": HTML_ERROR_PAGE}]}
        ),
    )
    assert res["ok"] is False
    assert res["error"] == "non-JSON error body"
    _assert_bounded_plain(res["error"])
    assert SENTINEL not in res["error"]


def test_huge_graphql_error_message_truncated_with_ellipsis(monkeypatch):
    """The old bare ``[:300]`` cap is gone: a multi-KB GraphQL error
    message lands at ≤140 chars with the head preserved."""
    huge = ("railway exploded spectacularly " * 2000).strip()  # ~62 KB
    assert len(huge) > 40_000
    res = _graphql_via(
        monkeypatch,
        lambda request: httpx.Response(200, json={"errors": [{"message": huge}]}),
    )
    assert res["ok"] is False
    _assert_bounded_plain(res["error"])
    assert res["error"].endswith("…")
    assert res["error"].startswith("railway exploded spectacularly")


def test_multiline_graphql_error_collapses_to_single_line(monkeypatch):
    body = {
        "errors": [
            {"message": "Not Authorized\n\n  token scope missing\n\ttrace-id 999"}
        ]
    }
    res = _graphql_via(
        monkeypatch, lambda request: httpx.Response(200, json=body)
    )
    assert res["ok"] is False
    _assert_bounded_plain(res["error"])
    assert res["error"] == "Not Authorized token scope missing trace-id 999"


def test_short_graphql_error_passes_verbatim(monkeypatch):
    res = _graphql_via(
        monkeypatch,
        lambda request: httpx.Response(
            200, json={"errors": [{"message": "Not Authorized"}]}
        ),
    )
    assert res["error"] == "Not Authorized"
    # Status failure without an errors array keeps the plain status phrase.
    res2 = _graphql_via(
        monkeypatch, lambda request: httpx.Response(500, json={"data": None})
    )
    assert res2["error"] == "HTTP 500"


def test_httpx_exception_reason_is_bounded_single_line(monkeypatch):
    """The exception mint site (previously completely unbounded)."""

    def boom(request):
        raise httpx.ConnectError(
            "connection failed\n"
            + "  retrying upstream backboard endpoint\n" * 200
            + f"trace {SENTINEL}\n"
        )

    res = _graphql_via(monkeypatch, boom)
    assert res["ok"] is False
    reason = res["error"]
    assert len(reason) <= CAP
    assert "\n" not in reason and "\r" not in reason
    assert reason.endswith("…")
    # The tail (thousands of chars in) never survives the cap.
    assert SENTINEL not in reason
    assert reason.startswith("ConnectError: connection failed")


def test_ok_responses_keep_empty_error(monkeypatch):
    res = _graphql_via(
        monkeypatch,
        lambda request: httpx.Response(
            200, json={"data": {"projectToken": {"projectId": "p1"}}}
        ),
    )
    assert res["ok"] is True and res["error"] == ""
    assert res["data"] == {"projectToken": {"projectId": "p1"}}


# --------------------------------------------------------------------------- #
# (b) render-level: the owner page inherits the bound
# --------------------------------------------------------------------------- #


def test_owner_environments_renders_bounded_reason_not_error_document(monkeypatch):
    """/owner/environments while Railway hands back a huge HTML error
    document inside its GraphQL errors array: the honest-degradation
    banner shows the bounded generic phrase, and the raw document appears
    nowhere in the rendered output."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")

    async def offline_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", offline_get)
    monkeypatch.setattr(
        railway,
        "_make_client",
        lambda: httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200, json={"errors": [{"message": HTML_ERROR_PAGE}]}
                )
            )
        ),
    )
    with TestClient(app) as c:
        r = c.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert SENTINEL not in r.text
    assert "Unicorn!" not in r.text
    # The honest-degradation banner still says WHY, in bounded form.
    assert "live Railway read failed" in r.text
    assert "non-JSON error body" in r.text
