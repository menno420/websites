"""Offline unit tests for the fleet polish batch: claim-timestamp extraction
+ stalled-claim aging on /orders, the /queue.json machine round-trip, and the
kit-version rollup on /fleet — all presentation/parse over already-fetched
data (no new fetch path).
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import fleet, github, orders, owner_queue  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 11, 12, 0, 0, tzinfo=timezone.utc)


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


# --------------------------------------------------------------------------- #
# (a) claim timestamp + stalled-claim aging
# --------------------------------------------------------------------------- #


def test_parse_orders_extracts_claim_timestamp():
    info = fleet.parse_orders(
        "acked=001-003 done=001 claimed-by: 002 my-lane 2026-07-10T21:07Z"
    )
    assert info["claimed_at"] == "2026-07-10T21:07:00+00:00"
    # no claim -> None; claim without a parseable stamp -> None (never guessed)
    assert fleet.parse_orders("acked=001 done=001")["claimed_at"] is None
    assert (
        fleet.parse_orders("acked=001 done= claimed-by: 001 my-lane soon")[
            "claimed_at"
        ]
        is None
    )


def _statuses(claim_iso):
    return [{
        "lane": "websites",
        "orders_info": fleet.parse_orders(
            f"acked=001-002 done=001 claimed-by: 002 my-lane {claim_iso}"
        ),
    }]


def test_classify_order_flags_stale_claim_past_threshold():
    # claimed 2026-07-10T09:00Z, now 2026-07-11T12:00Z -> 27h > 24h threshold
    cls = orders.classify_order("002", _statuses("2026-07-10T09:00Z"), now=NOW)
    assert cls["state"] == "claimed" and cls["claim_stale"] is True
    assert "ago" in cls["claim_age_human"]


def test_classify_order_fresh_claim_not_stale():
    cls = orders.classify_order("002", _statuses("2026-07-11T10:00Z"), now=NOW)
    assert cls["state"] == "claimed" and cls["claim_stale"] is False
    assert cls["claim_age_human"]  # age still shown


def test_classify_order_unparseable_claim_stamp_is_honest_unknown_age():
    statuses = [{
        "lane": "websites",
        "orders_info": fleet.parse_orders(
            "acked=001-002 done=001 claimed-by: 002 my-lane sometime"
        ),
    }]
    cls = orders.classify_order("002", statuses, now=NOW)
    assert cls["state"] == "claimed"
    assert cls["claim_stale"] is False and cls["claim_age_human"] == ""


def test_orders_page_badges_stale_claim(monkeypatch):
    inbox = (
        "# x · inbox\n\n"
        "## ORDER 002 · 2026-07-09T14:52Z · status: new\n"
        "priority: P1\ndo: something.\n"
    )
    status = (
        "# websites · status\nupdated: 2026-07-10T22:00Z\nhealth: green (ok)\n"
        "orders: acked=001-002 done=001 claimed-by: 002 my-lane 2026-07-01T00:00Z\n"
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == "control/inbox.md" and repo == "websites":
            return _res(data=inbox)
        if path.startswith("control/status") and repo == "websites":
            return _res(data=status)
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    client = TestClient(app)
    r = client.get("/orders")
    assert r.status_code == 200
    assert "claim stale?" in r.text
    assert "stale claim" in r.text  # summary badge

    d = client.get("/orders.json").json()
    top = next(c for c in d["cards"] if c["repo"] == "websites")
    assert top["orders"][0]["claim_stale"] is True
    assert d["summary"]["stale_claims"] == 1


# --------------------------------------------------------------------------- #
# (b) /queue.json
# --------------------------------------------------------------------------- #


def test_queue_json_round_trip_surfaces_filed_ask(monkeypatch):
    """The manager's round-trip: an ask filed in a lane heartbeat surfaces in
    machine-readable form at /queue.json (rendered HTML stripped)."""
    status = (
        "# websites · status\nupdated: 2026-07-10T22:00Z\nhealth: green (ok)\n"
        "orders: acked=001 done=001\n"
        "⚑ needs-owner: one ask.\n"
        "  ⚑ OWNER-ACTION\n"
        "  WHAT: Flip the test switch.\n"
        "  WHERE: the console.\n"
        "  HOW: click.\n"
        "  WHY-IT-MATTERS: round-trip proof.\n"
        "  UNBLOCKS: this test.\n"
        "  VERIFIED-NEEDED: owner-only switch.\n"
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status") and repo == "websites":
            return _res(data=status)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_repo_api)

    client = TestClient(app)
    r = client.get("/queue.json")
    assert r.status_code == 200
    d = r.json()
    texts = " ".join(
        (i.get("what") or "") + (i.get("text") or "") for i in d["items"]
    )
    assert "Flip the test switch" in texts
    assert "body_html" not in d["fleet_manager"]
    assert d["summary"]["total"] >= 1


# --------------------------------------------------------------------------- #
# (c) kit-version rollup
# --------------------------------------------------------------------------- #


def test_kit_version_token_extraction():
    assert fleet.kit_version("v1.7.1 · check: green · engaged: yes") == "v1.7.1"
    assert fleet.kit_version("kit v1.2.0 check green") == "v1.2.0"
    assert fleet.kit_version("no version here") == ""
    assert fleet.kit_version("") == ""


def test_kit_rollup_counts_and_buckets():
    def lane(kit=None, missing=False, err=None):
        return {
            "missing": missing,
            "fetch_error": err,
            "fields": {} if missing or err else (
                {"kit": kit} if kit is not None else {"updated": "x"}
            ),
        }

    lanes = [
        lane("v1.7.1 · check: green"),
        lane("v1.7.1 · check: green"),
        lane("v1.2.0"),
        lane(),                    # readable, no kit line -> none bucket
        lane(missing=True),        # says nothing about adoption
        lane(err="rate limited"),  # says nothing about adoption
    ]
    rollup = fleet.kit_rollup(lanes)
    assert rollup[0] == {"version": "v1.7.1", "count": 2}
    assert {"version": "v1.2.0", "count": 1} in rollup
    assert rollup[-1] == {"version": "none", "count": 1}


def test_fleet_page_shows_kit_rollup(monkeypatch):
    body = (
        "# lane · status\nupdated: 2026-07-10T22:00Z\nhealth: green (ok)\n"
        "kit: v1.7.1 · check: green · engaged: yes\n"
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status"):
            return _res(data=body)
        return _res(ok=False, status=404, data=None, error="nf")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return _res(ok=False, status=404, data=None, error="nf")

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_repo_api)
    client = TestClient(app)
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "kit adoption:" in r.text and "×v1.7.1" in r.text
