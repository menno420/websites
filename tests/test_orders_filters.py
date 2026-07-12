"""Offline tests for the ORDER 019 /orders filters — the REUSE proof for the
centralized listfilter widget: repo / status / priority dimensions, search,
date+status sorts, cards without matching orders hiding while a filter is
active, honest unknown values, and a no-param page carrying every order
(live rows on top, done rows collapsed — the list-IA default; the
/orders.json contract stays untouched).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import clock, github, orders  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 11, 9, 0, 0, tzinfo=timezone.utc)

_INBOX = """# websites · inbox
> ORDERS to this Project. Never edit this file.

## ORDER 001 · 2026-07-09T12:07Z · status: new
priority: P1
do: Adopt the protocol; then build the drift cell.
why: it is the only agent-executable roadmap item.
done-when: drift cell live; status reports done=001.

## ORDER 002 · 2026-07-09T14:52Z · status: new
priority: P0
do: Build a FLEET page.
why: ten Projects run in parallel.
done-when: /fleet live.

## ORDER 003 · 2026-07-10T20:58:44Z · status: new
priority: P1
do: A brand new thing nobody started.
why: because.
done-when: it exists.
"""

_STATUS = """# websites · status
updated: 2026-07-10T21:58:00Z
health: green (fine)
orders: acked=001-003 done=001 claimed-by: 002 my-lane 2026-07-10T21:00Z
"""


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


def _world(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md" and repo == "websites":
            return _res(data=_INBOX)
        if path.startswith("control/status") and repo == "websites":
            return _res(data=_STATUS)
        return _res(ok=False, status=404, data=None, error="Not Found")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_orders_default_page_grouped_plus_widget(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders")
    assert r.status_code == 200
    # everything renders: all orders counted, absent repos honest
    assert "3 of 3" in r.text
    assert "full order text" in r.text
    assert "no <code>control/inbox.md</code>" in r.text  # missing-inbox cards
    # list-IA default view: live orders keep inbox order on top; the done
    # order tucks into a collapsed <details> below them (still in the DOM).
    i1 = r.text.index("ORDER 001")
    i2 = r.text.index("ORDER 002")
    i3 = r.text.index("ORDER 003")
    assert i2 < i3 < i1  # 001 is done -> renders in the collapsed section
    assert "1 done order — collapsed" in r.text
    # the same widget /queue uses (same partial markup)
    assert 'href="/orders?state=open"' in r.text
    assert "no items match" not in r.text


def test_orders_filter_by_state(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders?state=open")
    assert "1 of 3" in r.text
    assert "A brand new thing" in r.text
    assert "Adopt the protocol" not in r.text
    # cards with no matching orders hide while a filter is active
    assert "no <code>control/inbox.md</code>" not in r.text
    # multi-select: OR within the status dimension
    r = client.get("/orders?state=open&state=done")
    assert "2 of 3" in r.text


def test_orders_filter_by_repo_and_priority(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders?repo=websites")
    assert "3 of 3" in r.text
    r = client.get("/orders?priority=P0")
    assert "1 of 3" in r.text
    assert "Build a FLEET page" in r.text
    assert "A brand new thing" not in r.text
    # AND across dimensions
    r = client.get("/orders?repo=websites&priority=P0&state=claimed")
    assert "1 of 3" in r.text and "Build a FLEET page" in r.text
    r = client.get("/orders?repo=websites&priority=P0&state=open")
    assert "0 of 3" in r.text and "no items match" in r.text


def test_orders_search(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders?q=fleet")  # case-insensitive over the block text
    assert "1 of 3" in r.text and "Build a FLEET page" in r.text


def test_orders_sorts_by_date_and_status(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders?sort=newest")
    assert (r.text.index("ORDER 003") < r.text.index("ORDER 002")
            < r.text.index("ORDER 001"))
    r = client.get("/orders?sort=oldest")
    assert (r.text.index("ORDER 001") < r.text.index("ORDER 002")
            < r.text.index("ORDER 003"))
    r = client.get("/orders?sort=status")  # open < claimed < done < unknown
    assert (r.text.index("ORDER 003") < r.text.index("ORDER 002")
            < r.text.index("ORDER 001"))


def test_orders_unknown_repo_value_flagged_and_empty(monkeypatch):
    _world(monkeypatch)
    client = TestClient(app)
    r = client.get("/orders?repo=not-a-repo")
    assert r.status_code == 200
    assert "0 of 3" in r.text
    assert "not-a-repo · unknown" in r.text  # kept + flagged, never dropped
    assert "no items match" in r.text
    # chips carry a remove link; clear-all present
    r = client.get("/orders?state=done")
    assert "status: done ✕" in r.text and "clear all" in r.text


def test_orders_json_contract_untouched(monkeypatch):
    """The reuse lives in the HTML route only — /orders.json keeps its exact
    pinned shape (no filter key, no repo stamped into order dicts)."""
    _world(monkeypatch)
    client = TestClient(app)
    d = client.get("/orders.json").json()
    assert "filter" not in d
    card = next(c for c in d["cards"] if c["repo"] == "websites")
    assert "shown_orders" not in card
    assert all("repo" not in o for o in card["orders"])
