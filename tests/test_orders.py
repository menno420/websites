"""Offline unit tests for /orders: per-repo inbox ORDER parsing, the
heartbeat cross-reference (done / claimed / open / unknown — never guessed),
attention-first sorting, and the honest degradation states. The route always
answers 200.
"""

import asyncio
import sys
from pathlib import Path

from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import github, orders  # noqa: E402

# Frozen clock (time-discipline guard — tests/test_time_discipline.py).
NOW = datetime(2026, 7, 11, 9, 0, 0, tzinfo=timezone.utc)
from app.main import app  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


_INBOX = """# websites · inbox
> ORDERS to this Project. Never edit this file.

## ORDER 001 · 2026-07-09T12:07Z · status: new
priority: P1
do: Adopt the protocol; then build the drift cell (docs/current-state.md
   § Next steps, item 3) and report via control/status.md.
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


def test_parse_inbox_blocks_and_fields():
    parsed = orders.parse_inbox(_INBOX)
    assert [o["id"] for o in parsed] == ["001", "002", "003"]
    o1 = parsed[0]
    assert o1["issued"].startswith("2026-07-09")
    assert o1["inbox_status"] == "new"
    assert o1["fields"]["priority"] == "P1"
    # wrapped do: line is joined as a continuation
    assert "item 3) and report" in o1["fields"]["do"]
    assert "ORDER 001" in o1["body"] and "ORDER 002" not in o1["body"]


def test_parse_inbox_no_orders_or_empty_is_empty():
    assert orders.parse_inbox("# inbox\n\nprose only\n") == []
    assert orders.parse_inbox("") == []


def test_classify_order_done_claimed_open_unknown():
    from app import fleet

    statuses = [{
        "lane": "websites",
        "orders_info": fleet.parse_orders(
            "acked=001-003 done=001 claimed-by: 002 my-lane 2026-07-10T21:00Z"
        ),
    }]
    assert orders.classify_order("001", statuses, now=NOW)["state"] == "done"
    c = orders.classify_order("002", statuses, now=NOW)
    assert c["state"] == "claimed" and "my-lane" in c["by"]
    assert orders.classify_order("003", statuses, now=NOW)["state"] == "open"
    # id "00" must not match inside "001" (boundary check)
    assert orders.classify_order("00", statuses, now=NOW)["state"] == "open"
    # no readable statuses -> unknown, never guessed
    assert orders.classify_order("001", [], now=NOW)["state"] == "unknown"


def _fake_world(monkeypatch, inbox_by_repo, status_by_repo):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md":
            body = inbox_by_repo.get(repo)
            if body is None:
                return _res(ok=False, status=404, data=None, error="Not Found")
            return _res(data=body)
        if path.startswith("control/status"):
            body = status_by_repo.get(repo)
            if body is None:
                return _res(ok=False, status=404, data=None, error="Not Found")
            return _res(data=body)
        # manifest fetch -> fail so resolve_lanes uses the honest fallback set
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_overview_cross_references_and_sorts(monkeypatch):
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": _STATUS},
    )

    out = asyncio.run(orders.overview(now=NOW))
    # websites has the only inbox -> it sorts first (open orders rise)
    top = out["cards"][0]
    assert top["repo"] == "websites"
    states = {o["id"]: o["state"] for o in top["orders"]}
    assert states == {"001": "done", "002": "claimed", "003": "open"}
    assert top["open_count"] == 1 and top["done_count"] == 1
    assert out["summary"]["open"] == 1 and out["summary"]["claimed"] == 1
    # repos without an inbox are honest absences, not errors
    absent = [c for c in out["cards"] if c["missing"]]
    assert absent and all(c["fetch_error"] is None for c in absent)


def test_overview_orders_without_status_are_unknown(monkeypatch):
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={},  # no readable status anywhere
    )
    out = asyncio.run(orders.overview(now=NOW))
    top = next(c for c in out["cards"] if c["repo"] == "websites")
    assert top["status_readable"] is False
    assert all(o["state"] == "unknown" for o in top["orders"])
    assert out["summary"]["unknown"] == 3


def test_orders_route_and_json(monkeypatch):
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": _STATUS},
    )
    client = TestClient(app)
    r = client.get("/orders")
    assert r.status_code == 200
    assert "ORDER 003" in r.text and "full order text" in r.text
    assert 'href="/orders"' in r.text  # nav link

    rj = client.get("/orders.json")
    assert rj.status_code == 200
    d = rj.json()
    top = d["cards"][0]
    assert top["repo"] == "websites"
    assert {o["id"]: o["state"] for o in top["orders"]}["003"] == "open"
    assert all("body_html" not in o for o in top["orders"])


def test_orders_route_degrades_offline(monkeypatch):
    async def all_fail(repo, path, ref="main", refresh=False):
        return _res(ok=False, status=503, data=None, error="offline")

    monkeypatch.setattr(github, "fetch_file", all_fail)
    client = TestClient(app)
    r = client.get("/orders")
    assert r.status_code == 200 and "unreachable" in r.text


def test_pickup_latency_filed_to_claimed():
    """filed→claimed latency: exact minutes from the two stamps /orders
    already parses; honest None on any unparseable/absent/negative delta."""
    from app import orders

    ok = orders.pickup_latency("2026-07-11T09:59Z", "2026-07-11T10:18Z")
    assert ok["mins"] == 19.0 and ok["human"]

    assert orders.pickup_latency("", "2026-07-11T10:18Z")["mins"] is None
    assert orders.pickup_latency("2026-07-11T09:59Z", None)["mins"] is None
    # claim stamp BEFORE filing (hand-written clock skew) -> honest unknown
    assert (
        orders.pickup_latency("2026-07-11T10:18Z", "2026-07-11T09:59Z")["mins"]
        is None
    )


def test_overview_carries_pickup_latency_for_claimed_orders(monkeypatch):
    """The claimed fixture order (002: filed 11:00Z, claimed 21:00Z the day
    before... see _INBOX/_STATUS stamps) carries latency keys; open/done
    orders carry the honest None."""
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": _STATUS},
    )
    out = asyncio.run(orders.overview(now=NOW))
    top = next(c for c in out["cards"] if c["repo"] == "websites")
    by_id = {o["id"]: o for o in top["orders"]}
    for o in by_id.values():
        assert "pickup_latency_mins" in o and "pickup_latency_human" in o
    claimed = by_id["002"]
    if claimed["pickup_latency_mins"] is not None:
        assert claimed["pickup_latency_mins"] >= 0
    # open + done orders have no claim stamp -> honest None
    assert by_id["003"]["pickup_latency_mins"] is None


def test_pickup_rollup_median_max_and_honest_none():
    """Median/max across measurable pickups; None (never zero) when nothing
    is measurable — stats are never invented."""
    from app import orders

    def card(lats):
        return {"orders": [{"pickup_latency_mins": v} for v in lats]}

    roll = orders._pickup_rollup([card([10.0, 30.0]), card([50.0])])
    assert roll["count"] == 3
    assert roll["median_mins"] == 30.0 and roll["max_mins"] == 50.0
    assert roll["median_human"] and roll["max_human"]

    assert orders._pickup_rollup([card([None, None]), card([])]) is None


def test_overview_summary_and_cards_carry_pickup_rollup(monkeypatch):
    """summary.pickup + per-card pickup_median_* present; honest None/""
    when the fixture world has no measurable claim stamps."""
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": _STATUS},
    )
    out = asyncio.run(orders.overview(now=NOW))
    assert "pickup" in out["summary"]
    top = next(c for c in out["cards"] if c["repo"] == "websites")
    assert "pickup_median_mins" in top and "pickup_median_human" in top
    if out["summary"]["pickup"] is None:
        assert all(
            o["pickup_latency_mins"] is None for o in top["orders"]
        )
    else:
        assert out["summary"]["pickup"]["count"] >= 1


def test_provenance_unverified_heuristic():
    """Advisory-only source check: recognizable identity tokens in
    provenance:/from: -> verified; absent/unrecognized -> flagged. Never
    affects state (relays stay legal)."""
    from app import orders

    def o(**fields):
        return {"fields": fields}

    # the real conventions seen on this repo's inbox
    assert orders.provenance_unverified(
        o(provenance="filed by fleet-manager on coordinator direction (cse_012o8py...)")
    ) is False
    assert orders.provenance_unverified(
        o(**{"from": "fleet-manager manager — ORDER 010 per-lane relay"})
    ) is False
    assert orders.provenance_unverified(
        o(provenance="see https://github.com/menno420/fleet-manager/pull/63")
    ) is False
    # absent or unrecognizable -> advisory flag
    assert orders.provenance_unverified(o()) is True
    assert orders.provenance_unverified(o(provenance="someone said so")) is True


def test_overview_orders_carry_provenance_flag(monkeypatch):
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": _STATUS},
    )
    out = asyncio.run(orders.overview(now=NOW))
    top = next(c for c in out["cards"] if c["repo"] == "websites")
    assert all("provenance_unverified" in o for o in top["orders"])
    # the flag never changes an order's state classification
    assert {o["state"] for o in top["orders"]} == {"done", "claimed", "open"}


def test_parse_pickup_history_tokens():
    """The persistence convention's consumer: `pickup: <id> <mins>m` notes
    tokens -> {id: mins}; tolerant of comma lists, later duplicates win,
    garbage never parses (never a guess)."""
    from app import orders

    hist = orders.parse_pickup_history(
        "rails held. pickup: 011 19m, 009 42.5m; later pickup: 011 20m"
    )
    assert hist == {"011": 20.0, "009": 42.5}
    assert orders.parse_pickup_history("") == {}
    assert orders.parse_pickup_history("pickup: soon-ish") == {}
    assert orders.parse_pickup_history("no tokens here 12m") == {}


def test_overview_falls_back_to_lane_reported_pickup(monkeypatch):
    """A DONE order (claim annotation gone) recovers its latency from the
    lane's `pickup:` notes token — the datum survives completion. Live
    stamps keep precedence for CLAIMED orders."""
    status_with_notes = _STATUS + "notes: rails held. pickup: 001 19m\n"
    _fake_world(
        monkeypatch,
        inbox_by_repo={"websites": _INBOX},
        status_by_repo={"websites": status_with_notes},
    )
    out = asyncio.run(orders.overview(now=NOW))
    top = next(c for c in out["cards"] if c["repo"] == "websites")
    by_id = {o["id"]: o for o in top["orders"]}
    # 001 is done (no claim stamp) -> lane-reported 19.0 recovered
    assert by_id["001"]["state"] == "done"
    assert by_id["001"]["pickup_latency_mins"] == 19.0
    assert by_id["001"]["pickup_latency_human"]
    # the recovered datum feeds the fleet rollup
    assert out["summary"]["pickup"] is not None
    assert out["summary"]["pickup"]["count"] >= 1
    # 003 is open, no token -> honest None unchanged
    assert by_id["003"]["pickup_latency_mins"] is None
