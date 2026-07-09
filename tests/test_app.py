"""Offline unit tests for the control-plane site (no network).

The public site serves every route without credentials. The one non-public
datum — the GitHub Actions secret *names* — is masked to a count on the public
board and must never appear in the served public HTML or /api/readiness.json.
The gated `/owner` area (HTTP Basic on SITE_PASSWORD) un-masks those names and
exposes privileged actions; the tests below hold both invariants.
"""

import asyncio
import base64
import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, readiness  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def secrets_client(monkeypatch):
    """Client whose /actions/secrets fetch returns real secret NAMES."""
    real_names = ["ANTHROPIC_API_KEY", "DATABASE_URL", "ROUTINE_PAT"]

    async def fake_get(url, refresh=False, raw=False):
        if url.endswith("/actions/secrets"):
            return {
                "ok": True, "status": 200,
                "data": {"secrets": [{"name": n} for n in real_names]},
                "error": "", "fetched_at": "", "cached": False, "url": url,
            }
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False, "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c, real_names


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


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_routes_public_no_auth(client):
    # No credentials: every route serves 200 (the auth gate is gone).
    for path in ["/", "/journal", "/journal/superbot", "/api/readiness.json"]:
        assert client.get(path).status_code == 200


def test_board_renders_degraded_no_auth(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "superbot-next" in r.text
    assert "unknown" in r.text  # degraded cells, never fabricated values


def test_unknown_repo_404(client):
    r = client.get("/journal/not-a-repo")
    assert r.status_code == 404


def test_secret_names_never_reach_served_html(monkeypatch):
    """The public board masks secrets to a COUNT: the real GitHub secret NAMES
    (admin-scope-only data) must be absent from the served HTML, and the count
    must be shown instead."""

    real_names = ["ANTHROPIC_API_KEY", "DATABASE_URL", "ROUTINE_PAT"]

    async def fake_get(url, refresh=False, raw=False):
        if url.endswith("/actions/secrets"):
            return {
                "ok": True, "status": 200,
                "data": {"secrets": [{"name": n} for n in real_names]},
                "error": "", "fetched_at": "", "cached": False, "url": url,
            }
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False, "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        html = c.get("/").text
        js = c.get("/api/readiness.json").text
    for name in real_names:
        assert name not in html, f"{name} leaked into served board HTML"
        assert name not in js, f"{name} leaked into /api/readiness.json"
    # the count is what the public board shows instead
    assert "3 secret(s)" in html


def test_secrets_cell_carries_count_not_names():
    """readiness.repo_readiness builds a secrets cell with a count and no names."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath == "/actions/secrets":
            return {
                "ok": True, "status": 200, "error": "", "cached": False,
                "fetched_at": "", "url": "",
                "data": {"secrets": [{"name": "ANTHROPIC_API_KEY"},
                                     {"name": "DATABASE_URL"}]},
            }
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        orig = github.repo_api
        github.repo_api = fake_repo_api
        try:
            row = await readiness.repo_readiness("superbot")
        finally:
            github.repo_api = orig
        secrets_cell = row["secrets"]
        assert secrets_cell["count"] == 2
        assert secrets_cell["detail"] == "2 secret(s)"
        assert "names" not in secrets_cell  # names never carried
        # the whole cell, serialized, contains no secret name
        assert "ANTHROPIC_API_KEY" not in repr(row["secrets"])

    asyncio.run(run())


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


def test_owner_requires_auth(secrets_client, monkeypatch):
    """/owner without credentials → 401 (public routes stay open)."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    c, _ = secrets_client
    assert c.get("/owner").status_code == 401
    assert c.get("/owner/api/readiness.json").status_code == 401
    # a wrong password is still 401
    assert c.get("/owner", headers=_basic("wrong")).status_code == 401
    # public routes are unaffected
    assert c.get("/").status_code == 200
    assert c.get("/healthz").status_code == 200


def test_owner_fails_closed_when_password_unset(secrets_client, monkeypatch):
    """SITE_PASSWORD unset → /owner 503, but the public site keeps working."""
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    c, _ = secrets_client
    assert c.get("/owner", headers=_basic(OWNER_PW)).status_code == 503
    assert c.get("/").status_code == 200  # public site unaffected
    assert c.get("/api/readiness.json").status_code == 200


def test_public_masks_secrets_but_owner_reveals(secrets_client, monkeypatch):
    """The invariant pair: PUBLIC HTML/JSON have ZERO secret names; the AUTHED
    /owner view (HTML + JSON) DOES contain them."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    c, real_names = secrets_client

    public_html = c.get("/").text
    public_json = c.get("/api/readiness.json").text
    owner_html = c.get("/owner", headers=_basic(OWNER_PW)).text
    owner_json = c.get(
        "/owner/api/readiness.json", headers=_basic(OWNER_PW)
    ).text

    for name in real_names:
        assert name not in public_html, f"{name} leaked into public HTML"
        assert name not in public_json, f"{name} leaked into public JSON"
        assert name in owner_html, f"{name} missing from authed /owner HTML"
        assert name in owner_json, f"{name} missing from authed /owner JSON"
    # public still shows the count
    assert "3 secret(s)" in public_html


def test_owner_reveal_secrets_flag_threads_names():
    """readiness.repo_readiness(reveal_secrets=True) carries names; default hides."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath == "/actions/secrets":
            return {
                "ok": True, "status": 200, "error": "", "cached": False,
                "fetched_at": "", "url": "",
                "data": {"secrets": [{"name": "ANTHROPIC_API_KEY"}]},
            }
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        orig = github.repo_api
        github.repo_api = fake_repo_api
        try:
            public_row = await readiness.repo_readiness("superbot")
            owner_row = await readiness.repo_readiness(
                "superbot", reveal_secrets=True
            )
        finally:
            github.repo_api = orig
        assert "names" not in public_row["secrets"]
        assert "ANTHROPIC_API_KEY" not in repr(public_row["secrets"])
        assert owner_row["secrets"]["names"] == ["ANTHROPIC_API_KEY"]
        assert owner_row["secrets"]["count"] == 1

    asyncio.run(run())


def test_owner_refresh_action(secrets_client, monkeypatch):
    """POST /owner/actions/refresh (authed) clears the cache and 200s."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(github, "clear_cache", lambda: 7)
    c, _ = secrets_client
    # unauthed POST rejected
    assert c.post("/owner/actions/refresh").status_code == 401
    r = c.post("/owner/actions/refresh", headers=_basic(OWNER_PW))
    assert r.status_code == 200
    assert "cache cleared" in r.text and "7 entries" in r.text


def test_owner_rerun_ci_action(secrets_client, monkeypatch):
    """POST /owner/actions/rerun-ci (authed) is reachable; external call mocked."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)

    async def fake_rerun(repo, branch="main"):
        return {"ok": True, "repo": repo, "run_id": 42,
                "url": "https://example/run/42",
                "message": f"re-ran failed jobs of run #42 on {repo}@{branch}"}

    monkeypatch.setattr(github, "rerun_latest_failed", fake_rerun)
    c, _ = secrets_client
    # unauthed rejected
    assert c.post(
        "/owner/actions/rerun-ci", data={"repo": "superbot"}
    ).status_code == 401
    r = c.post(
        "/owner/actions/rerun-ci",
        data={"repo": "superbot"},
        headers=_basic(OWNER_PW),
    )
    assert r.status_code == 200
    assert "re-ran failed jobs of run #42" in r.text
    # unknown repo handled honestly, still 200
    r2 = c.post(
        "/owner/actions/rerun-ci",
        data={"repo": "not-a-repo"},
        headers=_basic(OWNER_PW),
    )
    assert r2.status_code == 200 and "unknown repo" in r2.text


def test_rerun_latest_failed_no_failed_run(monkeypatch):
    """github.rerun_latest_failed reports honestly when there is nothing to re-run."""

    async def fake_get(url, refresh=False, raw=False):
        return {"ok": True, "status": 200,
                "data": {"workflow_runs": []},
                "error": "", "fetched_at": "", "cached": False, "url": url}

    async def run():
        monkeypatch.setattr(github, "_get", fake_get)
        res = await github.rerun_latest_failed("superbot")
        assert res["ok"] is False and "no failed run" in res["message"]

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
