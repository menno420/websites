"""Route-level clock freeze: whole-request rendering at a frozen instant.

The #114 static guard covers direct test calls to age-measuring functions;
this module pins the OTHER half: ``app/clock.py`` is the app's single
wall-clock read, so a TestClient route test can freeze an entire request's
rendering by monkeypatching ``clock.NOW_OVERRIDE`` — no more fixed fixture
stamps aging against real time through the endpoints (the 08:45Z class).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import clock, github  # noqa: E402
from app.main import app  # noqa: E402

NOW = datetime(2026, 7, 11, 13, 0, 0, tzinfo=timezone.utc)

# One hour before NOW — with the frozen clock this lane is EXACTLY 1h old,
# forever, no matter when the suite runs.
_STATUS_MD = (
    "# websites · status\n"
    "updated: 2026-07-11T12:00:00Z\n"
    "phase: frozen-clock fixture\n"
    "health: green (fixture)\n"
    "orders: acked=001 done=001\n"
)


def _frozen_offline(monkeypatch):
    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status"):
            return {"ok": True, "status": 200, "data": _STATUS_MD, "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_get(url, refresh=False, raw=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_api)
    monkeypatch.setattr(github, "_get", fake_get)


def test_clock_defaults_to_wall_and_override_wins(monkeypatch):
    """Production behavior: no override -> real wall clock (aware UTC).
    Test behavior: the override wins exactly."""
    monkeypatch.setattr(clock, "NOW_OVERRIDE", None)
    real = clock.now()
    assert real.tzinfo is not None
    assert abs((datetime.now(timezone.utc) - real).total_seconds()) < 5

    monkeypatch.setattr(clock, "NOW_OVERRIDE", NOW)
    assert clock.now() is NOW


def test_fleet_route_renders_deterministic_age_at_frozen_instant(monkeypatch):
    """A WHOLE /fleet.json request rendered at the frozen instant: the
    fixture lane is exactly 1.0h old and not stale — deterministically,
    no matter when (or in what decade) the suite runs. Before app/clock.py
    this request measured the fixture against the REAL wall clock, which
    is exactly how the 08:45Z time-bomb detonated."""
    _frozen_offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/fleet.json")
    assert r.status_code == 200
    lanes = [x for x in r.json()["lanes"] if x["freshness"].get("ok")]
    assert lanes, "no readable fixture lane came through the fleet pipeline"
    for lane in lanes:
        assert lane["freshness"]["age_hours"] == 1.0
        assert lane["freshness"]["stale"] is False


def test_orders_route_freezes_too(monkeypatch):
    """/orders.json rides the same clock: route stays 200 and renders under
    the frozen instant (claim aging measured from NOW, not real time)."""
    _frozen_offline(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/orders.json")
    assert r.status_code == 200
    assert "summary" in r.json()


def test_app_code_reads_the_clock_not_the_wall():
    """app/*.py must not call datetime.now()/utcnow() outside clock.py —
    otherwise a new module silently reopens the route-level blind spot the
    clock module closed (companion to the #114 static guard, which covers
    the TEST side)."""
    app_dir = Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for src in sorted(app_dir.glob("*.py")):
        if src.name == "clock.py":
            continue
        text = src.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if "datetime.now(" in line or "datetime.utcnow(" in line:
                offenders.append(f"{src.name}:{i} {line.strip()}")
    assert not offenders, (
        "wall-clock read outside app/clock.py — route through clock.now() "
        "so tests can freeze the request:\n  " + "\n  ".join(offenders)
    )
