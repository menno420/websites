"""Pins for the static exporter (``review/gen_static.py``) and the
``static_export`` render mode — every one of these encodes a Codex #509
round-1 finding, so a regression re-opens a shipped defect:

* **Path mapping** is an explicit file-suffix set, never a "contains a dot"
  heuristic — the committed fleet carries the lane ``codetool-lab-opus4.8``,
  which the heuristic exported as a bare FILE instead of a directory index.
* **URL rewriting** covers ``action=`` (the list-filter GET forms) alongside
  ``href``/``src``, prefixes only ROOT-relative URLs, and moves the feed's
  host-rooted absolute URLs onto the published site URL.
* **Static render mode** (``REVIEW_STATIC_EXPORT=1``): the list-filter
  widget and the /ask live widget are server-backed interaction — the
  static tree must say they retired instead of shipping controls that
  silently no-op on GitHub Pages. Both directions pinned: the live render
  keeps them.

Zero network: the site renders from committed review/data/**.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from review import gen_static  # noqa: E402
from review.app import app  # noqa: E402


# --------------------------------------------------------------------------- #
# out_path — the explicit suffix mapping
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "url,expected",
    [
        ("/", "index.html"),
        ("/fleet", "fleet/index.html"),
        # THE regression case: a dotted page-route segment is a directory
        # index, not a file (codetool-lab-opus4.8 is in the committed fleet).
        ("/fleet/codetool-lab-opus4.8", "fleet/codetool-lab-opus4.8/index.html"),
        ("/story.json", "story.json"),
        ("/reviews/feed.xml", "reviews/feed.xml"),
        ("/robots.txt", "robots.txt"),
    ],
)
def test_out_path_mapping(tmp_path, url, expected):
    assert gen_static.out_path(url, tmp_path) == tmp_path / expected


def test_dotted_fleet_lane_is_actually_in_the_committed_data():
    """The regression case above must stay REAL — if the lane leaves the
    committed fleet, this test flags the pin for a conscious update instead
    of letting it decay into fiction."""
    urls = gen_static.export_urls()
    assert "/fleet/codetool-lab-opus4.8" in urls, (
        "codetool-lab-opus4.8 left the committed fleet — update the dotted-"
        "segment pin in this file to another real dotted route (or drop it "
        "with a note) rather than leaving it aimed at nothing"
    )


def test_export_urls_skip_process_probes():
    urls = gen_static.export_urls()
    for probe in ("/healthz", "/version"):
        assert probe not in urls


# --------------------------------------------------------------------------- #
# rewrite_urls — attributes, protocol-relative, feed absolutes
# --------------------------------------------------------------------------- #
HOST = "https://menno420.github.io"
SITE = "https://menno420.github.io/websites"


def _rw(body: str, ctype: str = "text/html") -> str:
    return gen_static.rewrite_urls(
        body.encode(), ctype, "/websites", HOST, SITE
    ).decode()


def test_rewrite_covers_href_src_and_form_action():
    out = _rw(
        '<a href="/fleet">f</a><img src="/static/x.svg">'
        '<form method="get" action="/reviews">'
    )
    assert 'href="/websites/fleet"' in out
    assert 'src="/websites/static/x.svg"' in out
    assert 'action="/websites/reviews"' in out


def test_rewrite_leaves_protocol_relative_and_full_urls_alone():
    out = _rw('<a href="//cdn.example/x">a</a><a href="https://example.com/y">b</a>')
    assert 'href="//cdn.example/x"' in out
    assert 'href="https://example.com/y"' in out


def test_rewrite_moves_feed_absolutes_onto_the_site_url():
    out = _rw(f'<id>{HOST}/reviews/x</id>', ctype="application/atom+xml")
    assert f"{SITE}/reviews/x" in out


def test_rewrite_is_idempotent_for_urls_already_under_the_base_path():
    """A full Pages URL already carrying the base path must survive the
    host-root pass untouched — the hardcoded fleet-strip self-link came out
    as …/websites/websites/ on every page (Codex #510 round 2, P1)."""
    body = f'<a href="{SITE}/">Review</a><id>{HOST}/reviews/x</id>'
    once = _rw(body)
    assert f'href="{SITE}/"' in once  # not re-prefixed
    assert f"{SITE}/reviews/x" in once  # host-rooted still moves
    assert "websites/websites" not in once
    assert _rw(once) == once  # a second pass changes nothing


def test_rewrite_skips_non_markup_bodies():
    body = b'{"href": "/fleet"}'
    assert (
        gen_static.rewrite_urls(body, "application/json", "/websites", HOST, SITE)
        == body
    )


# --------------------------------------------------------------------------- #
# static_export render mode — both directions
# --------------------------------------------------------------------------- #
@pytest.fixture()
def static_client(monkeypatch):
    monkeypatch.setenv("REVIEW_STATIC_EXPORT", "1")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def live_client(monkeypatch):
    monkeypatch.delenv("REVIEW_STATIC_EXPORT", raising=False)
    with TestClient(app) as c:
        yield c


def test_static_fleet_drops_the_filter_widget_and_says_so(static_client):
    r = static_client.get("/fleet")
    assert r.status_code == 200
    assert 'class="searchbox"' not in r.text
    # template line breaks split the phrase — compare whitespace-normalized
    assert "retired with the live service" in " ".join(r.text.split())


def test_live_fleet_keeps_the_filter_widget(live_client):
    r = live_client.get("/fleet")
    assert r.status_code == 200
    assert 'class="searchbox"' in r.text
    assert "retired with the live service" not in " ".join(r.text.split())


def test_static_ask_replaces_the_widget_with_the_retirement_notice(static_client):
    r = static_client.get("/ask")
    assert r.status_code == 200
    assert 'id="ai-static-notice"' in r.text
    assert 'id="ai-widget"' not in r.text
    # the live call path is gone (the notice may NAME /ask/api; the script
    # that would fetch it must not ship)
    assert 'fetch("/ask/api"' not in r.text
    assert 'id="btn-ask"' not in r.text
    # the seeded answers stay — the surviving surface
    assert "Archived answers" in r.text
    assert "Talk to the record" not in r.text
    assert "The live model handles" not in r.text


def test_static_archive_language_is_consistent_across_navigation(static_client):
    home = static_client.get("/").text
    ask = static_client.get("/ask").text
    questionnaire = static_client.get("/questionnaire").text
    assert "Archived answers" in home
    assert 'href="/ask">Browse archived answers</a>' in home
    assert "Ask the project / Review with an AI" not in home
    assert 'href="/ask">Archived answers</a>' in home
    assert "Archived answers" in ask
    assert "Ask AI" not in ask
    assert "Talk to the record" not in ask
    assert "Archived answers" in questionnaire
    assert "deliberately not built" not in questionnaire
    assert "this static archive does not accept new questions" not in questionnaire
    assert "issues/new" in questionnaire
    assert "GitHub issue link above remains the intake" in questionnaire
    assert "no service holds a credential" not in questionnaire
    assert "separate database" in questionnaire
    assert "in-memory dry runs" in questionnaire


def test_live_ask_keeps_the_widget(live_client):
    r = live_client.get("/ask")
    assert r.status_code == 200
    assert 'id="ai-widget"' in r.text
    assert 'id="ai-static-notice"' not in r.text


# --------------------------------------------------------------------------- #
# Round-2 pins (Codex #509): frozen-age anchor banner, robots meta, and the
# build-only drift classification.
# --------------------------------------------------------------------------- #
def test_static_pages_carry_the_export_anchor_banner(static_client):
    """Relative ages freeze at export — the banner anchors every one of them
    to the build moment so a weeks-old deploy never silently claims '17h
    ago' relative to now."""
    r = static_client.get("/fleet")
    assert "Static export built" in r.text
    assert 'name="robots" content="noindex, nofollow"' in r.text


def test_live_pages_carry_neither_anchor_nor_robots_meta(live_client):
    r = live_client.get("/fleet")
    assert "Static export built" not in r.text
    assert 'name="robots"' not in r.text


def test_build_only_var_never_reads_missing_live():
    """app/envdrift.annotate classifies a build_only declared var as
    'build-only' (informational), never 'missing-live' — whether the live
    service exists or not (Codex #509 round 2)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from app import envdrift

    def fresh(name, build_only=False):
        return {
            "services": [
                {
                    "name": "review",
                    "env_vars": [
                        {"name": name, "purpose": "t", "build_only": build_only}
                    ],
                }
            ],
            "live": {
                "state": "ok",
                "services": [{"name": "review", "variable_names": []}],
            },
        }

    data = fresh("REVIEW_STATIC_EXPORT", build_only=True)
    envdrift.annotate(data)
    svc = data["services"][0]
    assert svc["env_vars"][0]["live_state"] == "build-only"
    assert svc["drift"]["missing_live"] == []

    control = fresh("REVIEW_AI_MODEL")
    envdrift.annotate(control)
    csvc = control["services"][0]
    assert csvc["env_vars"][0]["live_state"] == "missing-live"
    assert csvc["drift"]["missing_live"] == ["REVIEW_AI_MODEL"]
