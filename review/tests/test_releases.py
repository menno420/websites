"""Release-drift banner + loader tests (ORDER 033). Network-free; the loader
is pointed at fixture files via ``monkeypatch`` of ``fleetdata.RELEASES_PATH``
(the same seam ``test_fleet.py`` uses for ``FLEET_PATH``). The banner lives in
the shared ``base.html``, so any page (here ``/``) exercises it."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from review import fleetdata
from review.app import app

client = TestClient(app)


def _drift_mirror() -> dict:
    return {
        "generated_at": "2026-07-18T12:00:00Z",
        "note": "n",
        "entries": [
            {
                "slug": "lumen-drift",
                "name": "Lumen Drift",
                "source_repo": "menno420/gba-homebrew",
                "expected_tag": "lumen-drift-v1.3",
                "live_tag": None,
                "drift": True,
                "reason": "expected release lumen-drift-v1.3 is not published on the source repo",
            },
            {
                "slug": "mineverse",
                "name": "mineverse",
                "source_repo": "menno420/superbot-mineverse",
                "expected_tag": None,
                "live_tag": None,
                "drift": False,
                "reason": "no release tag is encoded in the arcade registry for this game",
            },
        ],
        "drift_count": 1,
    }


def _no_drift_mirror() -> dict:
    m = _drift_mirror()
    m["entries"][0]["drift"] = False
    m["entries"][0]["live_tag"] = "lumen-drift-v1.3"
    m["drift_count"] = 0
    return m


# ---------------------------------------------------------------------------
# Loader — degrades honestly to the empty default
# ---------------------------------------------------------------------------
def test_load_releases_missing_is_empty_default(tmp_path: Path):
    res = fleetdata.load_releases(tmp_path / "nope.json")
    assert res["entries"] == [] and res["drift_count"] == 0
    assert res["generated_at"] is None


def test_load_releases_corrupt_is_empty_default(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not valid json", encoding="utf-8")
    res = fleetdata.load_releases(p)
    assert res["entries"] == [] and res["drift_count"] == 0


def test_load_releases_malformed_shape_is_empty_default(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"entries": "not a list"}), encoding="utf-8")
    res = fleetdata.load_releases(p)
    assert res["entries"] == [] and res["drift_count"] == 0


def test_load_releases_recomputes_drift_count(tmp_path: Path):
    p = tmp_path / "releases.json"
    p.write_text(json.dumps(_drift_mirror()), encoding="utf-8")
    res = fleetdata.load_releases(p)
    assert res["drift_count"] == 1
    assert [e["slug"] for e in res["entries"]] == ["lumen-drift", "mineverse"]


def test_committed_releases_mirror_loads_and_is_well_shaped():
    """The real committed releases.json loads and every entry is honest —
    values regenerate at every bake, so only shape is asserted here."""
    res = fleetdata.load_releases()
    assert isinstance(res["entries"], list) and res["entries"]  # bake committed a non-empty mirror
    for e in res["entries"]:
        assert e["drift"] in (True, False)
        assert e["reason"].strip()
        assert e["source_repo"]


# ---------------------------------------------------------------------------
# Banner — present on drift, absent otherwise (shared base.html, any page)
# ---------------------------------------------------------------------------
def test_banner_renders_when_a_game_drifts(monkeypatch, tmp_path: Path):
    p = tmp_path / "releases.json"
    p.write_text(json.dumps(_drift_mirror()), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "RELEASES_PATH", p)
    r = client.get("/")
    assert r.status_code == 200
    assert "rv-drift" in r.text
    assert "Lumen Drift" in r.text
    assert "lumen-drift-v1.3" in r.text  # the expected tag named
    assert "vs live" in r.text
    # the tagless, non-drifting game is not listed in the banner
    assert "1 arcade game" in r.text


def test_banner_absent_when_no_game_drifts(monkeypatch, tmp_path: Path):
    p = tmp_path / "releases.json"
    p.write_text(json.dumps(_no_drift_mirror()), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "RELEASES_PATH", p)
    r = client.get("/")
    assert r.status_code == 200
    assert "rv-drift" not in r.text


def test_banner_absent_when_mirror_missing(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(fleetdata, "RELEASES_PATH", tmp_path / "gone.json")
    r = client.get("/")
    assert r.status_code == 200
    assert "rv-drift" not in r.text  # honest empty default → no banner, no 500


# ---------------------------------------------------------------------------
# /releases.json — machine-readable sibling
# ---------------------------------------------------------------------------
def test_releases_json_endpoint(monkeypatch, tmp_path: Path):
    p = tmp_path / "releases.json"
    p.write_text(json.dumps(_drift_mirror()), encoding="utf-8")
    monkeypatch.setattr(fleetdata, "RELEASES_PATH", p)
    r = client.get("/releases.json")
    assert r.status_code == 200
    body = r.json()
    assert body["drift_count"] == 1
    assert body["entries"][0]["slug"] == "lumen-drift"


def test_releases_json_endpoint_missing_is_empty(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(fleetdata, "RELEASES_PATH", tmp_path / "gone.json")
    r = client.get("/releases.json")
    assert r.status_code == 200
    assert r.json()["entries"] == []
