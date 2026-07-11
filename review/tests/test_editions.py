"""Reviews section tests: editions parsing, pages, and Atom feed validity."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi.testclient import TestClient

from review import editions
from review.app import app

client = TestClient(app)

ATOM = "{http://www.w3.org/2005/Atom}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def test_parse_edition_well_formed():
    e = editions.parse_edition(
        "---\ntitle: Edition 9 — test\ndate: 2026-07-11\nsummary: a summary\n---\n## Body\ntext\n",
        "2026-07-11-edition-009",
    )
    assert e is not None
    assert e["title"].startswith("Edition 9")
    assert e["date"] == "2026-07-11"
    assert e["summary"] == "a summary"
    assert e["body_md"].startswith("## Body")
    assert e["source_url"].endswith("review/data/reviews/2026-07-11-edition-009.md")


def test_parse_edition_rejects_missing_frontmatter():
    assert editions.parse_edition("# just markdown\n", "x") is None
    assert editions.parse_edition("---\ntitle: no date\n---\nbody", "x") is None
    assert editions.parse_edition("---\ndate: 2026-07-11\n---\nbody", "x") is None
    assert editions.parse_edition("---\ntitle: t\ndate: not-a-date\n---\nbody", "x") is None


def test_list_editions_sorted_and_skips_malformed(tmp_path: Path):
    (tmp_path / "2026-07-01-edition-001.md").write_text(
        "---\ntitle: one\ndate: 2026-07-01\nsummary: s\n---\nbody", encoding="utf-8"
    )
    (tmp_path / "2026-07-05-edition-002.md").write_text(
        "---\ntitle: two\ndate: 2026-07-05\nsummary: s\n---\nbody", encoding="utf-8"
    )
    (tmp_path / "broken.md").write_text("no front matter", encoding="utf-8")
    (tmp_path / "BAD NAME.md").write_text("---\ntitle: x\ndate: 2026-07-06\n---\nb", encoding="utf-8")
    got = editions.list_editions(tmp_path)
    assert [e["slug"] for e in got] == ["2026-07-05-edition-002", "2026-07-01-edition-001"]


def test_list_editions_missing_dir_is_empty(tmp_path: Path):
    assert editions.list_editions(tmp_path / "nope") == []


def test_committed_edition_1_is_well_formed():
    got = editions.list_editions()
    assert got, "edition 1 must exist and parse"
    first = got[-1]  # oldest
    assert first["slug"] == "2026-07-11-edition-001"
    assert first["title"]
    assert first["summary"]
    # house rule: claims cite evidence — the founding edition links PRs/docs
    assert "github.com/menno420/websites" in first["body_md"]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def test_reviews_index_lists_edition_1():
    r = client.get("/reviews")
    assert r.status_code == 200
    assert "/reviews/2026-07-11-edition-001" in r.text
    assert "Atom feed" in r.text or "feed.xml" in r.text


def test_edition_page_renders_markdown():
    r = client.get("/reviews/2026-07-11-edition-001")
    assert r.status_code == 200
    assert "<h2" in r.text  # markdown rendered, not raw
    assert "ORDER 011" in r.text
    assert "view the source" in r.text


def test_unknown_edition_404():
    assert client.get("/reviews/2020-01-01-edition-999").status_code == 404


def test_reviews_index_empty_state(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(editions, "REVIEWS_DIR", tmp_path / "none")
    r = client.get("/reviews")
    assert r.status_code == 200
    assert "No editions published yet" in r.text


# ---------------------------------------------------------------------------
# Atom feed — must be VALID XML in every state
# ---------------------------------------------------------------------------
def test_feed_valid_atom_with_entries():
    r = client.get("/reviews/feed.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/atom+xml")
    root = ET.fromstring(r.text)  # raises on malformed XML
    assert root.tag == f"{ATOM}feed"
    assert root.find(f"{ATOM}title") is not None
    assert root.find(f"{ATOM}id") is not None
    assert root.find(f"{ATOM}updated") is not None
    entries = root.findall(f"{ATOM}entry")
    assert len(entries) >= 1
    for entry in entries:
        assert entry.find(f"{ATOM}title") is not None
        assert entry.find(f"{ATOM}id").text.startswith("https://github.com/menno420/websites/")
        assert entry.find(f"{ATOM}updated") is not None
        link = entry.find(f"{ATOM}link")
        assert link is not None and "/reviews/" in link.get("href", "")


def test_feed_valid_when_empty(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(editions, "REVIEWS_DIR", tmp_path / "none")
    r = client.get("/reviews/feed.xml")
    assert r.status_code == 200
    root = ET.fromstring(r.text)
    assert root.tag == f"{ATOM}feed"
    assert root.findall(f"{ATOM}entry") == []  # empty but valid — never fake


def test_feed_discovery_link_in_pages():
    r = client.get("/")
    assert 'type="application/atom+xml"' in r.text
