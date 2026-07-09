"""Offline unit tests for the control-plane site (no network)."""

import asyncio
import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["SITE_PASSWORD"] = "test-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, readiness  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    # No network: every GitHub fetch returns a canned degraded result.
    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def test_healthz_unauthenticated(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_routes_reject_missing_and_wrong_auth(client):
    for path in ["/", "/journal", "/journal/superbot", "/api/readiness.json"]:
        assert client.get(path).status_code == 401
        assert client.get(path, auth=("x", "wrong")).status_code == 401


def test_board_renders_degraded_with_correct_auth(client):
    r = client.get("/", auth=("owner", "test-secret"))
    assert r.status_code == 200
    assert "superbot-next" in r.text
    assert "unknown" in r.text  # degraded cells, never fabricated values


def test_fail_closed_when_password_unset(monkeypatch, client):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    assert client.get("/", auth=("x", "")).status_code == 503


def test_unknown_repo_404(client):
    r = client.get("/journal/not-a-repo", auth=("owner", "test-secret"))
    assert r.status_code == 404


def test_red_by_design_annotation():
    # superbot-next's golden-parity `report` job: failure -> red-by-design,
    # never counted broken; a plain failing check stays broken.
    async def run():
        calls = {}

        async def fake_repo_api(repo, subpath="", refresh=False):
            calls.setdefault(repo, []).append(subpath)
            if subpath.startswith("/commits/") and "check-runs" in subpath:
                return {
                    "ok": True, "status": 200, "error": "", "cached": False,
                    "fetched_at": "", "url": "",
                    "data": {"check_runs": [
                        {"name": "report", "status": "completed",
                         "conclusion": "failure", "html_url": "u",
                         "head_sha": "abc", "app": {"name": "GA"}},
                        {"name": "tests", "status": "completed",
                         "conclusion": "failure", "html_url": "u",
                         "head_sha": "abc", "app": {"name": "GA"}},
                    ]},
                }
            return {"ok": False, "status": 404, "data": None, "error": "nf",
                    "fetched_at": "", "cached": False, "url": ""}

        orig = github.repo_api
        github.repo_api = fake_repo_api
        try:
            row = await readiness.repo_readiness("superbot-next")
        finally:
            github.repo_api = orig
        states = {r["name"]: r["effective"] for r in row["live_runs"]}
        assert states["report"] == "red-by-design"
        assert states["tests"] == "failure"
        broken = [r["name"] for r in row["broken_runs"]]
        assert broken == ["tests"]

    asyncio.run(run())


def test_cache_skips_transient_errors(monkeypatch):
    importlib.reload(github)

    class FakeResp:
        def __init__(self, status):
            self.status_code = status

        def json(self):
            return {"message": "x"}

    class FakeClient:
        def __init__(self, statuses):
            self.statuses = list(statuses)
            self.calls = 0

        async def get(self, url):
            self.calls += 1
            return FakeResp(self.statuses.pop(0))

    async def run():
        fake = FakeClient([429, 200, 200])
        github.set_clients(fake, fake)  # type: ignore[arg-type]
        r1 = await github._get("http://x/a")
        assert r1["status"] == 429 and not r1["ok"]
        r2 = await github._get("http://x/a")  # 429 was NOT cached -> refetch
        assert r2["status"] == 200 and r2["ok"]
        r3 = await github._get("http://x/a")  # 200 IS cached
        assert r3["cached"] is True
        assert fake.calls == 2

    asyncio.run(run())
