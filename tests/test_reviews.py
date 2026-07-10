"""Offline unit tests for /reviews (ORDER 009 increment 3): the fleet
review-queue ledger render — header-name table parsing with repo#N PR
deep-links, struck-row (reviewed) classification, findings/records link
extraction from the doc itself, and the honest degradation ladder. The route
always answers 200 and never fabricates a row.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, reviews  # noqa: E402
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


_LEDGER = """# Review queue — needs-second-review ledger

> **Status:** `living-ledger`

Sources: the launch record
([`planning/gen2-launch-record-2026-07-10.md`](planning/gen2-launch-record-2026-07-10.md)),
the night review
([`findings/night-review-2026-07-10.md`](findings/night-review-2026-07-10.md)),
and the economics ledger
([`findings/fleet-economics-2026-07.md`](findings/fleet-economics-2026-07.md)).

## Open items

| PR | What to re-check | Why-risky | Drain path · status |
|---|---|---|---|
| superbot#1920 | The checker semantics change | Enforcement surface, no non-author eyes | codex · **open** |
| trading-strategy#36 | Promotion-significance bar | Gates the one-shot holdout | codex? · **open** — time-sensitive |
| ~~websites#67~~ | ~~Heartbeat enrichment parse~~ | ~~KNOWN_KEYS change~~ | ~~reviewed 2026-07-10, ok~~ |
"""


def test_parse_rows_by_header_name_with_pr_links():
    rows = reviews.parse_rows(_LEDGER)
    assert len(rows) == 3
    r0 = rows[0]
    assert r0["pr_repo"] == "superbot" and r0["pr_number"] == "1920"
    assert r0["pr_url"].endswith("/superbot/pull/1920")
    assert r0["what"] == "The checker semantics change"
    assert "codex" in r0["status"] and r0["reviewed"] is False
    assert rows[1]["pr_repo"] == "trading-strategy"


def test_parse_rows_struck_row_counts_reviewed():
    rows = reviews.parse_rows(_LEDGER)
    struck = rows[2]
    assert struck["reviewed"] is True
    assert struck["pr_repo"] == "websites" and struck["pr_number"] == "67"
    assert "~~" not in struck["what"]


def test_parse_rows_no_table_is_empty_never_invented():
    assert reviews.parse_rows("# doc\n\njust prose, no tables\n") == []
    assert reviews.parse_rows("") == []


def test_extract_findings_links_resolved_and_deduped():
    links = reviews.extract_findings_links(_LEDGER)
    urls = [l["url"] for l in links]
    assert len(links) == 3 and len(set(urls)) == 3
    assert any(
        u.endswith("/fleet-manager/blob/main/docs/findings/night-review-2026-07-10.md")
        for u in urls
    )
    assert any("planning/gen2-launch-record" in u for u in urls)
    # labels stripped of markdown backticks
    assert all("`" not in l["label"] for l in links)


def test_overview_states(monkeypatch):
    async def fetch_404(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=404, data=None, error="Not Found")

    async def fetch_403(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=403, data=None, error="rate limited")

    def run(fake):
        monkeypatch.setattr(github, "fetch_file", fake)
        return asyncio.run(reviews.overview())

    out = run(fetch_404)
    assert out["state"] == "empty" and out["rows"] == []

    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    out = run(fetch_403)
    assert out["state"] == "not-configured" and "GITHUB_TOKEN" in out["reason"]

    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    out = run(fetch_403)
    assert out["state"] == "unavailable" and "rate limited" in out["reason"]


def test_overview_happy_counts_and_render(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_LEDGER)

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await reviews.overview()

    out = asyncio.run(run())
    assert out["state"] == "ok"
    assert out["open_count"] == 2 and out["reviewed_count"] == 1
    assert len(out["findings_links"]) == 3
    assert "<h1" in out["body_html"]  # full doc rendered, nothing hidden


def test_reviews_route_and_json(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(data=_LEDGER)

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/reviews")
    assert r.status_code == 200
    assert "superbot#1920" in r.text and "/superbot/pull/1920" in r.text
    assert "findings &amp; records" in r.text
    assert 'href="/reviews"' in r.text  # nav link

    rj = client.get("/reviews.json")
    assert rj.status_code == 200
    d = rj.json()
    assert d["open_count"] == 2 and "body_html" not in d
    assert d["rows"][0]["pr_url"].endswith("/pull/1920")


def test_reviews_route_empty_state_is_200(monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/reviews")
    assert r.status_code == 200 and "ledger not landed yet" in r.text
