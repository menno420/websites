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

from app import (  # noqa: E402
    activity,
    config,
    fleet,
    github,
    ideas,
    journal,
    owner,
    readiness,
)
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


def test_version_returns_env_sha(client, monkeypatch):
    """/version reports the control-plane's deployed SHA from the environment."""
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc12345def67890")
    r = client.get("/version")
    assert r.status_code == 200
    assert r.json() == {
        "service": "control-plane",
        "sha": "abc12345def67890",
        "short": "abc12345",
    }


def test_version_unknown_when_unset(client, monkeypatch):
    """No env var set → honest 'unknown', not a crash or a fabricated sha."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    assert client.get("/version").json() == {
        "service": "control-plane",
        "sha": "unknown",
        "short": "unknown",
    }


def _deploy_state_row(monkeypatch, head_sha, self_sha, service_short):
    """Build the websites row with mocked HEAD sha + service /version shas.

    Returns row["deploy_state"] after driving readiness.repo_readiness("websites")
    with a fake check-runs head_sha, a fake control-plane deployed sha (env), and
    a fake botsite/dashboard /version fetch reporting ``service_short``.
    """
    monkeypatch.setattr(config, "deployed_sha", lambda: self_sha)

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/commits/") and "check-runs" in subpath:
            return {
                "ok": True, "status": 200, "error": "", "cached": False,
                "fetched_at": "", "url": "",
                "data": {"check_runs": [
                    {"name": "quality", "status": "completed", "conclusion": "success",
                     "html_url": "u", "head_sha": head_sha, "app": {"name": "GA"}},
                ]},
            }
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_get(url, refresh=False, raw=False):
        # the botsite/dashboard /version fetches
        if url.endswith("/version"):
            return {"ok": True, "status": 200,
                    "data": {"service": "x", "sha": service_short + "00", "short": service_short},
                    "error": "", "fetched_at": "", "cached": False, "url": url}
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": url}

    async def run():
        orig_api, orig_get = github.repo_api, github._get
        github.repo_api = fake_repo_api
        github._get = fake_get
        try:
            row = await readiness.repo_readiness("websites")
        finally:
            github.repo_api, github._get = orig_api, orig_get
        return row

    return asyncio.run(run())["deploy_state"]


def test_deploy_state_in_sync_when_deployed_equals_head(monkeypatch):
    """deployed short-sha == head short-sha → in_sync for every service."""
    ds = _deploy_state_row(
        monkeypatch, head_sha="abc12345ffffffff", self_sha="abc12345ffffffff",
        service_short="abc12345",
    )
    assert ds is not None
    assert ds["head_short"] == "abc12345"
    assert ds["all_in_sync"] is True and ds["any_drift"] is False
    states = {s["service"]: s["state"] for s in ds["services"]}
    assert states == {
        "control-plane": "in_sync", "botsite": "in_sync", "dashboard": "in_sync",
        "review": "in_sync",
    }


def test_deploy_state_drift_when_deployed_differs(monkeypatch):
    """A different deployed short-sha → DRIFT, with both shas surfaced."""
    ds = _deploy_state_row(
        monkeypatch, head_sha="aaaaaaaabbbbbbbb", self_sha="99999999cccccccc",
        service_short="99999999",
    )
    assert ds["any_drift"] is True and ds["all_in_sync"] is False
    cp = next(s for s in ds["services"] if s["service"] == "control-plane")
    assert cp["state"] == "drift"
    assert cp["deployed_short"] == "99999999" and cp["head_short"] == "aaaaaaaa"


def test_deploy_state_unknown_sha_renders_clean(monkeypatch):
    """Env var absent (deployed sha unknown) is a clean non-error state, not a crash,
    and the board still renders."""
    monkeypatch.setattr(config, "deployed_sha", lambda: "")

    async def fake_get(url, refresh=False, raw=False):
        # /version fetch fails → that service is 'unknown' honestly
        return {"ok": False, "status": 0, "data": None, "error": "offline test",
                "fetched_at": "", "cached": False, "url": url}

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "deploy state" in r.text  # the cell renders
        assert "unknown" in r.text       # unknown state, never faked

    async def run():
        row = await readiness.repo_readiness("websites")
        return row["deploy_state"]

    ds = asyncio.run(run())
    cp = next(s for s in ds["services"] if s["service"] == "control-plane")
    assert cp["state"] == "unknown" and cp["known"] is False and cp["error"]


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


# --- /journal/{repo}/file render guard (fleet-lane widening) ---


def _mock_fetch_file(monkeypatch, text="# hello\n\nworld"):
    """Mock github.fetch_file so file renders need no network."""
    calls = []

    async def fake_fetch_file(repo, path, ref="main", refresh=False):
        calls.append((repo, path, ref))
        return {
            "ok": True, "status": 200, "data": text,
            "error": "", "fetched_at": "", "cached": False, "url": "",
        }

    monkeypatch.setattr(github, "fetch_file", fake_fetch_file)
    return calls


def test_journal_file_unknown_repo_still_404(client):
    r = client.get("/journal/not-a-repo/file", params={"path": "README.md"})
    assert r.status_code == 404


def test_journal_file_bad_path_still_400(client):
    for bad in ["../secrets.md", "docs/../../etc/passwd", "/etc/passwd"]:
        r = client.get("/journal/websites/file", params={"path": bad})
        assert r.status_code == 400, bad


def test_journal_file_fleet_lane_repo_renders(client, monkeypatch):
    # sim-lab is a FLEET_LANES repo that is NOT in config.REPOS — it must
    # now pass the guard and render.
    assert "sim-lab" not in config.REPOS
    assert "sim-lab" in config.JOURNAL_RENDER_REPOS
    calls = _mock_fetch_file(monkeypatch)
    r = client.get(
        "/journal/sim-lab/file", params={"path": "docs/current-state.md"}
    )
    assert r.status_code == 200
    assert "hello" in r.text
    assert calls == [("sim-lab", "docs/current-state.md", "main")]


def test_journal_file_original_repo_still_renders(client, monkeypatch):
    # An original REPOS repo keeps working through the widened guard.
    calls = _mock_fetch_file(monkeypatch)
    r = client.get(
        "/journal/superbot/file", params={"path": "docs/current-state.md"}
    )
    assert r.status_code == 200
    assert "hello" in r.text
    assert calls == [("superbot", "docs/current-state.md", "main")]


# --- live-monitoring auto-refresh (board / + /fleet only) ---


def _has_autorefresh(html: str) -> bool:
    """The auto-refresh indicator + poll script both present on a page."""
    return (
        'class="autorefresh"' in html
        and "data-autorefresh=" in html
        and 'id="live-content"' in html
        and "/static/autorefresh.js" in html
    )


def test_board_has_autorefresh_indicator_and_poll_script(client):
    r = client.get("/")
    assert r.status_code == 200
    assert _has_autorefresh(r.text)
    # the interval config constant is what the indicator advertises
    assert (
        "auto-refreshing every %ds" % config.AUTOREFRESH_SECONDS in r.text
    )
    assert 'data-autorefresh="%d"' % config.AUTOREFRESH_SECONDS in r.text
    # the pause/resume control is present
    assert 'id="ar-toggle"' in r.text


def test_fleet_has_autorefresh_indicator_and_poll_script(client):
    r = client.get("/fleet")
    assert r.status_code == 200
    assert _has_autorefresh(r.text)
    assert 'id="ar-toggle"' in r.text


def test_content_pages_do_not_autorefresh(client):
    # Journal / content surfaces stay static — no auto-refresh markup or script.
    for path in ["/journal", "/journal/superbot", "/activity", "/ideas"]:
        html = client.get(path).text
        assert "/static/autorefresh.js" not in html, path
        assert 'class="autorefresh"' not in html, path
        assert 'id="live-content"' not in html, path


def test_autorefresh_js_served_static(client):
    r = client.get("/static/autorefresh.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    # the module polls the current page and swaps the live region in place
    assert "live-content" in r.text and "setInterval" in r.text


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


def _owner_action_headers(pw: str = OWNER_PW) -> dict:
    """Basic auth + same-origin Origin header for the CSRF-guarded POST actions."""
    return {**_basic(pw), "Origin": "http://testserver"}


def test_owner_refresh_action(secrets_client, monkeypatch):
    """POST /owner/actions/refresh (authed, same-origin) clears the cache and 200s."""
    owner.reset_rate_limits()
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(github, "clear_cache", lambda: 7)
    c, _ = secrets_client
    # unauthed POST rejected (auth precedes the CSRF check)
    assert c.post("/owner/actions/refresh").status_code == 401
    r = c.post("/owner/actions/refresh", headers=_owner_action_headers())
    assert r.status_code == 200
    assert "cache cleared" in r.text and "7 entries" in r.text


def test_owner_rerun_ci_action(secrets_client, monkeypatch):
    """POST /owner/actions/rerun-ci (authed, same-origin) is reachable; external call mocked."""
    owner.reset_rate_limits()
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
        headers=_owner_action_headers(),
    )
    assert r.status_code == 200
    assert "re-ran failed jobs of run #42" in r.text
    # unknown repo handled honestly, still 200
    r2 = c.post(
        "/owner/actions/rerun-ci",
        data={"repo": "not-a-repo"},
        headers=_owner_action_headers(),
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


def test_render_markdown_produces_html_elements():
    """Session-log markdown → real HTML (headings, code, tables), not raw fences."""
    src = (
        "# Title\n\n"
        "## Section\n\n"
        "Some **bold** text and a [link](https://example.com).\n\n"
        "```python\nprint('hi')\n```\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |\n"
    )
    html = journal.render_markdown(src)
    assert "<h1" in html and "<h2" in html
    assert "<code>" in html or "<pre>" in html
    assert "<table>" in html and "<td>" in html
    assert 'href="https://example.com"' in html
    # the raw fence markers must be gone (rendered, not shown literally)
    assert "```" not in html


def test_render_markdown_sanitizes_script():
    """bleach strips a <script> even though the source is trusted (defense-in-depth)."""
    html = journal.render_markdown("ok text\n\n<script>alert(1)</script>\n")
    # The executable <script> tag must be gone; inert leftover text is harmless.
    assert "<script>" not in html
    assert "</script>" not in html


def test_search_journal_cross_repo(monkeypatch):
    """search_journal greps the corpus, ranks by match count, deep-links out."""

    async def fake_corpus(repo, refresh):
        return [{"path": ".sessions/x.md", "blob": f"https://github.com/menno420/{repo}/blob/main/.sessions/x.md", "kind": "session"}]

    async def fake_fetch(repo, path, ref="main", refresh=False):
        bodies = {
            "superbot": "line one\nRailway deploy Railway again\nend",
            "superbot-next": "no hit here",
            "substrate-kit": "one Railway mention",
            "websites": "nothing relevant",
        }
        return {"ok": True, "status": 200, "data": bodies[repo],
                "error": "", "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(journal, "_corpus", fake_corpus)
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        out = await journal.search_journal("railway")  # case-insensitive
        repos = [r["repo"] for r in out["results"]]
        assert repos == ["superbot", "substrate-kit"]  # 2 matches ranked first
        top = out["results"][0]
        assert top["matches"] == 2 and top["line"] == 2
        assert top["github_url"].endswith("#L2")
        assert "<mark>Railway</mark>" in top["snippet_html"]
        assert out["scanned"] == 4 and out["errors"] == []

    asyncio.run(run())


def test_search_journal_reports_fetch_errors(monkeypatch):
    """A failed corpus fetch lands in errors (honest banner), not silently dropped."""

    async def fake_corpus(repo, refresh):
        return [{"path": "docs/x.md", "blob": "b", "kind": "doc"}]

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == "superbot":
            return {"ok": True, "status": 200, "data": "has term here",
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 429, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(journal, "_corpus", fake_corpus)
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        out = await journal.search_journal("term")
        assert len(out["results"]) == 1 and out["results"][0]["repo"] == "superbot"
        assert len(out["errors"]) == 3
        assert all(e["status"] == 429 for e in out["errors"])

    asyncio.run(run())


def test_search_empty_query():
    out = asyncio.run(journal.search_journal("   "))
    assert out["empty"] is True and out["results"] == []


def test_search_route_registered_before_repo(client):
    """/journal/search is NOT captured as a repo path (route order)."""
    r = client.get("/journal/search?q=anything")
    assert r.status_code == 200
    assert "search the journal" in r.text
    rj = client.get("/journal/search.json?q=anything")
    assert rj.status_code == 200 and "results" in rj.json()


def test_websites_row_expects_quality_required_check():
    """The board's websites row now expects `quality` as a required check
    (owner set the ruleset, 2026-07-09) — no longer 'none required'."""
    assert config.REPOS["websites"]["expected_required_checks"] == ["quality"]


# --------------------------------------------------------------------------- #
# Cross-repo activity timeline
# --------------------------------------------------------------------------- #


def test_activity_timeline_merges_sorts_and_links(monkeypatch):
    """timeline() merges PRs across repos into one newest-first stream, collapses
    each into a display state, keeps the author, and deep-links to GitHub."""

    pulls = {
        "superbot": [
            {"number": 900, "title": "merge me", "state": "closed",
             "merged_at": "2026-07-09T15:00:00Z", "updated_at": "2026-07-09T15:00:00Z",
             "user": {"login": "alice"}, "html_url": "https://gh/superbot/900"},
        ],
        "superbot-next": [
            {"number": 44, "title": "open pr", "state": "open", "merged_at": None,
             "draft": False, "updated_at": "2026-07-09T16:00:00Z",
             "user": {"login": "bob"}, "html_url": "https://gh/next/44"},
        ],
        "substrate-kit": [
            {"number": 7, "title": "draft pr", "state": "open", "merged_at": None,
             "draft": True, "updated_at": "2026-07-09T12:00:00Z",
             "user": {"login": "carol"}, "html_url": "https://gh/kit/7"},
        ],
        "websites": [],
    }

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/pulls"):
            return {"ok": True, "status": 200, "data": pulls[repo], "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await activity.timeline()

    out = asyncio.run(run())
    # newest-first by merge/update time: next(16:00) > superbot(15:00) > kit(12:00)
    order = [(i["repo"], i["number"], i["state"]) for i in out["items"]]
    assert order == [
        ("superbot-next", 44, "open"),
        ("superbot", 900, "merged"),
        ("substrate-kit", 7, "draft"),
    ]
    assert out["items"][1]["url"] == "https://gh/superbot/900"
    assert out["items"][0]["author"] == "bob"
    assert out["errors"] == [] and out["total"] == 3


def test_activity_timeline_error_banner(monkeypatch):
    """A failing per-repo fetch lands in errors (honest banner), others still render."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        if repo == "superbot" and subpath.startswith("/pulls"):
            return {"ok": True, "status": 200,
                    "data": [{"number": 1, "title": "ok", "state": "open",
                              "merged_at": None, "updated_at": "2026-07-09T10:00:00Z",
                              "user": {"login": "x"}, "html_url": "u"}],
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await activity.timeline()

    out = asyncio.run(run())
    assert [i["repo"] for i in out["items"]] == ["superbot"]
    bad = {e["repo"] for e in out["errors"]}
    assert bad == {"superbot-next", "substrate-kit", "websites"}
    assert all(e["status"] == 403 for e in out["errors"])


def test_activity_route_degrades_no_auth(client):
    """/activity serves 200 with honest error banners when GitHub is unreachable."""
    r = client.get("/activity")
    assert r.status_code == 200
    assert "cross-repo activity" in r.text
    rj = client.get("/activity.json")
    assert rj.status_code == 200 and "items" in rj.json()


# --------------------------------------------------------------------------- #
# Atom feed (/activity.xml) — a subscribable serializer over the same timeline
# --------------------------------------------------------------------------- #

ATOM = "{http://www.w3.org/2005/Atom}"


def _atom_client(monkeypatch, pulls):
    """A TestClient whose repo_api serves the given per-repo PR lists (offline)."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/pulls"):
            return {"ok": True, "status": 200, "data": pulls.get(repo, []),
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)
    return TestClient(app)


def test_activity_xml_is_wellformed_atom_with_real_links(monkeypatch):
    """/activity.xml returns 200 + application/atom+xml, parses as well-formed
    Atom, and each entry carries the PR's real GitHub link + real timestamp."""
    import xml.etree.ElementTree as ET

    pulls = {
        "superbot": [
            {"number": 900, "title": "ship the feed", "state": "closed",
             "merged_at": "2026-07-09T15:00:00Z", "updated_at": "2026-07-09T15:00:00Z",
             "user": {"login": "alice"},
             "html_url": "https://github.com/menno420/superbot/pull/900"},
        ],
        "superbot-next": [], "substrate-kit": [], "websites": [],
    }
    with _atom_client(monkeypatch, pulls) as c:
        r = c.get("/activity.xml")

    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/atom+xml")

    root = ET.fromstring(r.text)  # raises on malformed XML
    assert root.tag == ATOM + "feed"
    assert root.findtext(ATOM + "title") == "SuperBot fleet activity"

    # feed self link points at the route
    self_hrefs = [
        ln.get("href") for ln in root.findall(ATOM + "link")
        if ln.get("rel") == "self"
    ]
    assert self_hrefs and self_hrefs[0].endswith("/activity.xml")
    # feed updated == the newest entry's real timestamp
    assert root.findtext(ATOM + "updated") == "2026-07-09T15:00:00Z"

    entries = root.findall(ATOM + "entry")
    assert len(entries) == 1
    e = entries[0]
    assert "#900" in (e.findtext(ATOM + "title") or "")
    assert e.findtext(ATOM + "id") == "https://github.com/menno420/superbot/pull/900"
    assert e.findtext(ATOM + "updated") == "2026-07-09T15:00:00Z"
    hrefs = [ln.get("href") for ln in e.findall(ATOM + "link")]
    assert "https://github.com/menno420/superbot/pull/900" in hrefs
    assert (e.find(ATOM + "author") or ET.Element("x")).findtext(ATOM + "name") == "alice"


def test_activity_xml_escapes_xml_special_chars(monkeypatch):
    """A PR title with XML metacharacters is escaped, not hand-concatenated raw —
    the payload never contains the unescaped markup and round-trips cleanly."""
    import xml.etree.ElementTree as ET

    raw_title = 'fix <tag> & "quotes" in PR'
    pulls = {
        "superbot": [
            {"number": 1, "title": raw_title, "state": "open", "merged_at": None,
             "draft": False, "updated_at": "2026-07-09T10:00:00Z",
             "user": {"login": "bob"},
             "html_url": "https://github.com/menno420/superbot/pull/1"},
        ],
        "superbot-next": [], "substrate-kit": [], "websites": [],
    }
    with _atom_client(monkeypatch, pulls) as c:
        r = c.get("/activity.xml")

    # the raw wire bytes must not carry the unescaped tag; must carry the escape
    assert "<tag>" not in r.text
    assert "&lt;tag&gt;" in r.text
    root = ET.fromstring(r.text)  # parses despite the special chars
    titles = [e.findtext(ATOM + "title") for e in root.findall(ATOM + "entry")]
    assert any(raw_title in (t or "") for t in titles)  # round-trips to original


def test_activity_xml_degrades_to_valid_feed_when_offline(client):
    """When GitHub is unreachable the feed still validates: a single honest
    diagnostic entry rather than a malformed feed or an invented PR."""
    import xml.etree.ElementTree as ET

    r = client.get("/activity.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/atom+xml")
    root = ET.fromstring(r.text)
    assert root.tag == ATOM + "feed"
    assert root.findtext(ATOM + "title") == "SuperBot fleet activity"
    entries = root.findall(ATOM + "entry")
    assert len(entries) == 1
    assert "status" in (entries[0].findtext(ATOM + "title") or "").lower()


def test_activity_page_has_atom_discovery_and_subscribe_link(client):
    """/activity advertises the feed: a discovery <link rel=alternate> in the head
    and a visible Subscribe link."""
    r = client.get("/activity")
    assert r.status_code == 200
    assert 'rel="alternate"' in r.text
    assert 'type="application/atom+xml"' in r.text
    assert '/activity.xml' in r.text
    assert "subscribe" in r.text.lower()


# --------------------------------------------------------------------------- #
# Idea backlog
# --------------------------------------------------------------------------- #


def test_parse_idea_frontmatter_and_oneline():
    """parse_idea strips frontmatter, takes the H1 (minus an 'Idea:' label) as the
    title, and prefers an explicit **One line:** marker for the summary."""
    src = (
        "---\nstate: captured\noutcome: open\n---\n\n"
        "# `bootstrap heartbeat` — a mechanical writer\n\n"
        "> **Status:** `ideas`\n\n"
        "**One line:** a verb that overwrites control/status.md in the exact shape.\n"
    )
    out = ideas.parse_idea(src, "fallback")
    assert out["title"] == "bootstrap heartbeat — a mechanical writer"
    assert out["summary"].startswith("a verb that overwrites control/status.md")

    # 'Idea:' label stripped; no One-line marker → first real paragraph is used.
    src2 = "# Idea: agent smoke check\n\nThe problem it solves is real and here.\n"
    out2 = ideas.parse_idea(src2, "fb")
    assert out2["title"] == "agent smoke check"
    assert out2["summary"] == "The problem it solves is real and here."


def test_ideas_lists_files_skips_readme(monkeypatch):
    """repo_ideas lists real idea files (README excluded), newest-first, each with
    a parsed title and deep-links."""

    listing = [
        {"type": "file", "name": "README.md", "path": "docs/ideas/README.md"},
        {"type": "file", "name": "alpha-2026-07-01.md",
         "path": "docs/ideas/alpha-2026-07-01.md",
         "html_url": "https://gh/websites/blob/main/docs/ideas/alpha-2026-07-01.md"},
        {"type": "file", "name": "beta-2026-07-08.md",
         "path": "docs/ideas/beta-2026-07-08.md", "html_url": "https://gh/beta"},
        {"type": "dir", "name": "sub", "path": "docs/ideas/sub"},
    ]
    bodies = {
        "docs/ideas/alpha-2026-07-01.md": "# Alpha idea\n\nDo the alpha thing.\n",
        "docs/ideas/beta-2026-07-08.md": "# Beta idea\n\n**One line:** be better.\n",
    }

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath == "/contents/docs/ideas":
            return {"ok": True, "status": 200, "data": listing, "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": True, "status": 200, "data": bodies[path], "error": "",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await ideas.repo_ideas("websites")

    out = asyncio.run(run())
    assert out["total"] == 2  # README excluded, dir excluded
    titles = [i["title"] for i in out["ideas"]]
    assert titles == ["Beta idea", "Alpha idea"]  # newest (by name) first
    beta = out["ideas"][0]
    assert beta["summary"] == "be better."
    assert beta["github_url"] == "https://gh/beta"
    assert beta["internal_url"] == "/journal/websites/file?path=docs/ideas/beta-2026-07-08.md"


def test_ideas_no_ideas_dir_is_absence_not_error(monkeypatch):
    """A 404 on docs/ideas is a legitimate absence (missing=True), never an error."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "Not Found",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await ideas.repo_ideas("substrate-kit")

    out = asyncio.run(run())
    assert out["missing"] is True and out["has_dir"] is False
    assert out["listing_error"] is None and out["total"] == 0


def test_ideas_listing_error_surfaces(monkeypatch):
    """A non-404 listing failure surfaces as an honest listing_error banner."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await ideas.repo_ideas("superbot")

    out = asyncio.run(run())
    assert out["missing"] is False and out["has_dir"] is False
    assert out["listing_error"] and "rate limited" in out["listing_error"]


def test_ideas_listing_error_names_missing_token(monkeypatch):
    """Token-unset + non-404 listing failure: the per-repo banner now NAMES
    the missing token (shared github.classify_listing ladder) instead of
    echoing only the raw fetch reason."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        monkeypatch.setattr(config, "GITHUB_TOKEN", "")
        return await ideas.repo_ideas("superbot")

    out = asyncio.run(run())
    assert out["missing"] is False and out["has_dir"] is False
    assert out["listing_error"] == (
        "GITHUB_TOKEN is not set on this service and the superbot "
        "`docs/ideas/` listing failed (fetch: rate limited)"
    )


def test_ideas_non_list_2xx_payload_is_an_honest_listing_error(monkeypatch):
    """An ok envelope whose data is not a directory listing is a listing
    error with the shared 'unexpected listing payload' reason — never a
    silent empty backlog."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": True, "status": 200, "data": "<!doctype html>oops",
                "error": "", "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
        return await ideas.repo_ideas("websites")

    out = asyncio.run(run())
    assert out["missing"] is False and out["has_dir"] is False
    assert out["listing_error"] == "unexpected listing payload (HTTP 200)"
    assert out["total"] == 0


def test_ideas_route_degrades_no_auth(client):
    """/ideas serves 200 even when GitHub is unreachable (honest empty state)."""
    r = client.get("/ideas")
    assert r.status_code == 200
    assert "what's queued to build" in r.text
    rj = client.get("/ideas.json")
    assert rj.status_code == 200 and isinstance(rj.json(), list)


# --------------------------------------------------------------------------- #
# Fleet heartbeat (/fleet) — ORDER 002
# --------------------------------------------------------------------------- #

# A real websites-lane heartbeat in the documented control/status.md format,
# with value colons (timestamp, "#PR — text") and a leading-⚑ needs-owner key.
_STATUS_MD = """# websites · status
updated: 2026-07-09T15:25Z
phase: shipped /activity + /ideas; control-plane auto-deployed to da35e21f
health: green (all three services in-sync at da35e21f)
last-shipped: #33 — cross-repo /activity timeline + /ideas backlog views
blockers: none
orders: acked=001,002 done=001
⚑ needs-owner: Q4 dashboard /admin live-bot control; Q5 botsite /submit Postgres
notes: dogfood row for the fleet page
"""


def test_parse_status_documented_format():
    """parse_status reads the documented status.md: heading → project name (the
    trailing '· status' stripped), key:value fields keyed by normalized name,
    with value colons (timestamps, '#PR — text') NOT splitting a new field, and
    the leading-⚑ 'needs-owner' key normalized."""
    out = fleet.parse_status(_STATUS_MD, "fallback-lane")
    assert out["project"] == "websites"
    f = out["fields"]
    assert f["updated"] == "2026-07-09T15:25Z"  # colon inside value preserved
    assert f["health"].startswith("green")
    assert f["last-shipped"].startswith("#33 — cross-repo")
    assert f["blockers"] == "none"
    assert f["orders"] == "acked=001,002 done=001"
    assert f["needs-owner"].startswith("Q4 dashboard")  # ⚑ stripped, normalized
    # A substrate-kit-style extra `kit:` line is captured, unknown lines don't
    # spuriously start fields.
    out2 = fleet.parse_status(
        "# kit · status\nkit: v1.3.0 · check: green · engaged: yes\n", "fb"
    )
    assert out2["fields"]["kit"].startswith("v1.3.0")


def test_classify_health_kinds():
    """green→ok, red-by-design→design (purple, NOT broken), broken→bad, ''→unknown."""
    assert fleet.classify_health("green (all in sync)")["kind"] == "ok"
    d = fleet.classify_health("red-by-design (golden-parity report red)")
    assert d["kind"] == "design" and d["badge"] == "design"
    assert fleet.classify_health("broken (pytest red)")["kind"] == "broken"
    assert fleet.classify_health("")["kind"] == "unknown"


def test_freshness_stale_threshold():
    """freshness computes an age and badges stale past FLEET_STALE_HOURS; an
    unparseable timestamp is honest (ok=False), never faked fresh."""
    from datetime import datetime, timezone

    now = datetime(2026, 7, 9, 18, 0, 0, tzinfo=timezone.utc)
    fresh = fleet.freshness("2026-07-09T15:25Z", now=now)  # ~2.5h old
    assert fresh["ok"] and fresh["stale"] is False and "ago" in fresh["age_human"]
    old = fleet.freshness("2026-07-07T00:00:00Z", now=now)  # >2 days old
    assert old["ok"] and old["stale"] is True
    bad = fleet.freshness("not-a-date", now=now)
    assert bad["ok"] is False and bad["stale"] is False


from datetime import datetime as _dt, timezone as _tz  # noqa: E402

# Frozen clock for every age-measuring fleet call (time-discipline guard:
# fixed fixture stamps + real wall clock = a test that flips on its own —
# see tests/test_time_discipline.py and the 2026-07-11T08:45Z incident).
FLEET_NOW = _dt(2026, 7, 11, 9, 0, 0, tzinfo=_tz.utc)


def _fleet_lane(repo="websites", lane="websites", path="control/status.md"):
    return {"lane": lane, "repo": repo, "status_path": path,
            "model": "unknown", "note": "n"}


def test_fleet_lane_renders_parsed_health_and_body(monkeypatch):
    """lane_status parses a lane's health + fields, renders the status body to
    HTML, and attaches last-commit age + open-PR count from the repo meta."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": True, "status": 200, "data": _STATUS_MD, "error": "",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/commits"):
            return {"ok": True, "status": 200,
                    "data": [{"commit": {"committer": {
                        "date": "2026-07-09T15:00:00Z"}}}],
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        if subpath.startswith("/pulls"):
            return {"ok": True, "status": 200,
                    "data": [{"number": 1}, {"number": 2}],
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.lane_status(_fleet_lane(), now=FLEET_NOW)

    out = asyncio.run(run())
    assert out["missing"] is False and out["fetch_error"] is None
    assert out["project"] == "websites"
    assert out["health"]["kind"] == "ok"
    assert out["fields"]["orders"] == "acked=001,002 done=001"
    assert out["open_prs"]["count"] == 2 and out["open_prs"]["display"] == "2"
    assert out["last_commit"]["ok"] is True
    # full body rendered as markdown (H1 became a heading)
    assert "<h1" in out["body_html"] and "websites" in out["body_html"]
    assert out["github_url"].endswith("/websites/blob/main/control/status.md")


def test_fleet_no_status_file_is_absence_not_error(monkeypatch):
    """A 404 status file is an honest absence (missing=True), NOT an error — the
    bare `superbot` lane (heartbeat lives in superbot-next) is the real case."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "Not Found",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.lane_status(
            _fleet_lane(repo="superbot", lane="superbot"), now=FLEET_NOW
        )

    out = asyncio.run(run())
    assert out["missing"] is True and out["fetch_error"] is None
    assert out["body_html"] == "" and out["health"]["kind"] == "unknown"


def test_fleet_fetch_error_is_honest_banner(monkeypatch):
    """A non-404 fetch failure surfaces as an honest fetch_error banner (never a
    faked heartbeat), and is NOT treated as a legitimate absence."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.lane_status(_fleet_lane(), now=FLEET_NOW)

    out = asyncio.run(run())
    assert out["missing"] is False
    assert out["fetch_error"] and "rate limited" in out["fetch_error"]
    assert out["open_prs"]["display"] == "?"  # meta degrades honestly too


def test_fleet_overview_sorts_attention_first_and_counts(monkeypatch):
    """overview() renders every configured lane, sorts problems to the top
    (broken/stale before healthy), and rolls up honest summary counts."""

    bodies = {
        # a broken lane
        "superbot-next": "# superbot-next · status\nupdated: 2026-07-09T17:30Z\n"
                         "health: broken (pytest red)\n",
        # a healthy fresh lane
        "websites": "# websites · status\nupdated: 2026-07-09T17:45Z\n"
                    "health: green (in sync)\n",
        # a healthy but STALE lane (old heartbeat)
        "substrate-kit": "# substrate-kit · status\nupdated: 2026-07-01T00:00:00Z\n"
                         "health: green (suite passing)\n",
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo in bodies:
            return {"ok": True, "status": 200, "data": bodies[repo], "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        # every other lane: no status file (honest absence)
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.overview(now=FLEET_NOW)

    out = asyncio.run(run())
    assert out["summary"]["total"] == len(config.FLEET_LANES)
    assert out["summary"]["broken"] == 1
    assert out["summary"]["stale"] >= 1
    # broken sorts before the stale-green sorts before healthy-green
    lanes = out["lanes"]
    broken_i = next(i for i, x in enumerate(lanes) if x["health"]["kind"] == "broken")
    web_i = next(i for i, x in enumerate(lanes) if x["repo"] == "websites")
    assert broken_i < web_i


def test_fleet_route_degrades_no_auth(client):
    """/fleet serves 200 with honest empty state when GitHub is unreachable;
    /fleet.json returns the parsed lanes without the rendered body."""
    r = client.get("/fleet")
    assert r.status_code == 200
    assert "fleet heartbeat" in r.text
    rj = client.get("/fleet.json")
    assert rj.status_code == 200
    body = rj.json()
    assert "lanes" in body and "summary" in body
    assert body["summary"]["total"] == len(config.FLEET_LANES)
    # body_html is stripped from the JSON payload
    assert all("body_html" not in lane for lane in body["lanes"])
    # GitHub unreachable -> the lane set falls back honestly, never a silent lie.
    assert body["lane_source"]["source"] == "fallback"


# --------------------------------------------------------------------------- #
# Fleet lane set derived LIVE from the manager's fleet-manifest
# --------------------------------------------------------------------------- #

# A representative fleet-manifest (menno420/superbot docs/eap/fleet-manifest.md):
# markdown table, one row per Project. Includes the `manager` control chair (no
# concrete repo -> not a lane), a multi-repo Project (SuperBot coordinator), and
# two shared-repo cohabitation lanes (superbot-games). Matches the real format.
_SAMPLE_REGISTRY = """
# roster generator excerpt (the registry literal /fleet parses live)
LANES = [
    {"lane": "superbot (hub)", "repo": "superbot", "disposition": "hub",
     "tokens": ["superbot"]},
    {"lane": "websites", "repo": "websites", "disposition": "live",
     "tokens": ["websites"]},
    {"lane": "superbot-games \u00b7 Seat A", "repo": "superbot-games",
     "disposition": "live", "tokens": ["superbot-games"]},
    {"lane": "retro-games coordinator (no repo)", "repo": None,
     "disposition": "registry-only", "tokens": ["retro"]},
    {"lane": "codetool-lab-fable5", "repo": "codetool-lab-fable5",
     "disposition": "archived", "tokens": ["codetool"]},
]

GITHUB_BASE = "https://github.com/menno420/"
"""


def test_parse_registry_yields_expected_lanes():
    """parse_registry + registry_to_lanes turn the gen_roster LANES literal
    into the lane set: registry-only seats (repo None) are skipped; hub and
    archived dispositions are kept with honest notes."""
    lanes = fleet.registry_to_lanes(fleet.parse_registry(_SAMPLE_REGISTRY))
    got = {(la["repo"], la["status_path"]) for la in lanes}
    assert got == {
        ("superbot", "control/status.md"),
        ("websites", "control/status.md"),
        ("superbot-games", "control/status.md"),
        ("codetool-lab-fable5", "control/status.md"),
    }
    notes = {la["repo"]: la["note"] for la in lanes}
    assert "hub seat" in notes["superbot"]
    assert "archived" in notes["codetool-lab-fable5"]


def test_registry_added_lane_auto_appears():
    """A lane ADDED to the registry appears in the derived set with no code
    change — the point of parsing the registry live (drift removed)."""
    added = _SAMPLE_REGISTRY.replace(
        'LANES = [',
        'LANES = [\n    {"lane": "new-lab", "repo": "new-lab", '
        '"disposition": "live", "tokens": ["new-lab"]},',
    )
    lanes = fleet.registry_to_lanes(fleet.parse_registry(added))
    assert "new-lab" in {la["repo"] for la in lanes}
    assert len(lanes) == 5


def test_parse_registry_honest_on_missing_or_malformed():
    """No LANES literal -> [] (never guessed); a malformed literal raises to
    the caller's fallback path."""
    assert fleet.parse_registry("print('no registry here')") == []
    assert fleet.parse_registry("") == []
    import pytest as _pytest
    with _pytest.raises(Exception):
        fleet.parse_registry("LANES = [\n    {unquoted: nope},\n]")


def test_resolve_lanes_uses_registry_when_available(monkeypatch):
    """resolve_lanes fetches + parses the registry as the PRIMARY source."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == fleet.REGISTRY_REPO and path == fleet.REGISTRY_PATH
        return {"ok": True, "status": 200, "data": _SAMPLE_REGISTRY, "error": "",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await fleet.resolve_lanes()

    lanes, source = asyncio.run(run())
    assert source["source"] == "registry" and source["ok"] is True
    assert source["count"] == 4 and len(lanes) == 4


def test_resolve_lanes_falls_back_on_fetch_failure(monkeypatch):
    """A manifest fetch failure falls back to config.FLEET_LANES, honestly
    labeled `source=fallback` with a reason (never a silent pretend-live)."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "Not Found",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        return await fleet.resolve_lanes()

    lanes, source = asyncio.run(run())
    assert source["source"] == "fallback" and source["ok"] is False
    assert source["reason"]  # a human-readable reason is present
    assert lanes == list(config.FLEET_LANES)


def test_fleet_overview_is_registry_sourced(monkeypatch):
    """overview() reports the lane set as registry-sourced when the registry is
    reachable, and renders the registry-derived lanes (not the fallback)."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path == fleet.REGISTRY_PATH:
            return {"ok": True, "status": 200, "data": _SAMPLE_REGISTRY, "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        # No lane has a status file in this test -> honest absences.
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.overview(now=FLEET_NOW)

    out = asyncio.run(run())
    assert out["lane_source"]["source"] == "registry"
    assert out["summary"]["total"] == 4
    assert {lane["repo"] for lane in out["lanes"]} >= {"superbot-games", "websites"}


def test_fleet_unreadable_repo_is_honest_not_dropped(monkeypatch):
    """A registry lane whose repo the token can't read (401/403) renders as an
    honest `unreadable` state — never dropped, never faked."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "Forbidden",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "Forbidden",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", fake_repo_api)
        return await fleet.lane_status(
            _fleet_lane(repo="private-lane", lane="private-lane"),
            now=FLEET_NOW,
        )

    out = asyncio.run(run())
    assert out["unreadable"] is True and out["missing"] is False
    assert "unreadable" in out["fetch_error"]


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


# --------------------------------------------------------------------------- #
# Owner queue (/queue) + environments registry (/environments) — ORDER 005
# --------------------------------------------------------------------------- #

from app import environments, owner_queue  # noqa: E402

# A needs-owner value as fleet.parse_status actually delivers it: continuation
# lines flattened onto one line, two six-field OWNER-ACTION blocks after a
# preamble sentence (the real websites heartbeat shape).
_NEEDS_OWNER_FLAT = (
    "two asks — canonical list lives in docs/owner/OWNER-ACTIONS.md. "
    "⚑ OWNER-ACTION WHAT: Mint a durable GitHub PAT and set it on the "
    "control-plane service. WHERE: github.com → Settings → Developer settings. "
    "HOW: token scoped to menno420 repos, set as GITHUB_TOKEN. "
    "WHY-IT-MATTERS: several board cells run degraded without it. "
    "UNBLOCKS: /queue's fleet-manager half. "
    "VERIFIED-NEEDED: live board shows unknown cells; printenv checked. "
    "⚑ OWNER-ACTION WHAT: Create a small Postgres for the botsite intake. "
    "WHERE: railway.app → superbot-websites → New → Database. "
    "HOW: add variable DATABASE_URL. "
    "WHY-IT-MATTERS: the submission form is a stub until a store exists. "
    "UNBLOCKS: the moderated submissions queue. "
    "VERIFIED-NEEDED: policy wall D-0005; no DATABASE_URL on the service today."
)


def test_parse_owner_actions_flattened_blocks():
    """The flattened lane shape parses into a preamble + two structured blocks
    with all six fields keyed."""
    preamble, blocks = owner_queue.parse_owner_actions(_NEEDS_OWNER_FLAT)
    assert preamble.startswith("two asks — canonical list")
    assert len(blocks) == 2
    b = blocks[0]
    assert b["what"].startswith("Mint a durable GitHub PAT")
    assert b["where"].startswith("github.com")
    assert b["how"].startswith("token scoped")
    assert b["why"].startswith("several board cells")
    assert b["unblocks"] == "/queue's fleet-manager half."
    assert b["verified"].startswith("live board shows unknown")
    assert blocks[1]["what"].startswith("Create a small Postgres")


def test_parse_owner_actions_multiline_markdown():
    """The raw multiline markdown form (owner-queue.md style, with emphasis
    around labels) parses the same way."""
    src = (
        "# Owner queue\n\nCurated asks, newest first.\n\n"
        "⚑ OWNER-ACTION\n"
        "**WHAT:** Approve the fleet budget.\n"
        "WHERE: claude.ai console\n"
        "HOW: click only\n"
        "WHY-IT-MATTERS: nothing runs without it.\n"
        "UNBLOCKS: everything.\n"
        "VERIFIED-NEEDED: agents cannot approve budgets (403 captured).\n"
    )
    preamble, blocks = owner_queue.parse_owner_actions(src)
    assert "Curated asks" in preamble
    assert len(blocks) == 1
    assert blocks[0]["what"] == "Approve the fleet budget."
    assert blocks[0]["how"] == "click only"


def test_parse_owner_actions_none_and_free_text():
    """'none' (and variants) yield nothing; a plain ask with no block markers
    comes back as the preamble (one honest free-text item for the caller)."""
    assert owner_queue.parse_owner_actions("none") == ("", [])
    assert owner_queue.parse_owner_actions("  ") == ("", [])
    assert owner_queue.parse_owner_actions("`none`") == ("", [])
    text, blocks = owner_queue.parse_owner_actions(
        "Q4 dashboard /admin live-bot control; Q5 botsite /submit Postgres"
    )
    assert text.startswith("Q4 dashboard") and blocks == []


_QUEUE_STATUS_FRESH = (
    "# websites · status\n"
    "updated: 2026-07-10T02:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: preamble pointer sentence.\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Mint the control-plane PAT.\n"
    "  WHERE: github.com settings\n"
    "  HOW: set GITHUB_TOKEN\n"
    "  WHY-IT-MATTERS: cells degraded.\n"
    "  UNBLOCKS: /queue fleet-manager half.\n"
    "  VERIFIED-NEEDED: printenv checked by gen-1.\n"
    "notes: n\n"
)

_QUEUE_STATUS_OLDER = (
    "# substrate-kit · status\n"
    "updated: 2026-07-09T01:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner:\n"
    "  ⚑ OWNER-ACTION\n"
    "  WHAT: Mint the control-plane PAT.\n"
    "  WHERE: github.com settings\n"
    "  HOW: set GITHUB_TOKEN\n"
    "  WHY-IT-MATTERS: cells degraded.\n"
    "  UNBLOCKS: /queue fleet-manager half.\n"
    "  VERIFIED-NEEDED: printenv checked by gen-1.\n"
    "notes: n\n"
)

_QUEUE_STATUS_FREETEXT = (
    "# superbot-next · status\n"
    "updated: 2026-07-09T12:00Z\n"
    "health: green (ok)\n"
    "⚑ needs-owner: decide the plugin cutover window\n"
    "notes: n\n"
)

_OWNER_QUEUE_MD = (
    "# Owner queue\n\n"
    "⚑ OWNER-ACTION\n"
    "WHAT: Arm the coordinator wake trigger.\n"
    "WHERE: claude.ai console\n"
    "HOW: click only\n"
    "WHY-IT-MATTERS: fleet is self-terminal without it.\n"
    "UNBLOCKS: unattended operation.\n"
    "VERIFIED-NEEDED: no scheduler primitive (probe error captured).\n"
)


def _queue_fakes(monkeypatch, fm_result=None):
    """Wire fetch_file/repo_api fakes: 3 lanes with asks (one duplicated WHAT),
    manifest 404 (fallback lane set), fleet-manager per fm_result."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo == owner_queue.FLEET_MANAGER_REPO:
            if fm_result is not None:
                return fm_result
            return {"ok": False, "status": 404, "data": None, "error": "Not Found",
                    "fetched_at": "", "cached": False, "url": ""}
        bodies = {
            "websites": _QUEUE_STATUS_FRESH,
            "substrate-kit": _QUEUE_STATUS_OLDER,
            "superbot-next": _QUEUE_STATUS_FREETEXT,
        }
        if repo in bodies and path == "control/status.md":
            return {"ok": True, "status": 200, "data": bodies[repo], "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    monkeypatch.setattr(github, "repo_api", fake_repo_api)


def test_queue_overview_dedups_sorts_and_reads_fleet_manager(monkeypatch):
    """overview() merges the duplicated WHAT across two lanes into ONE item
    keeping both sources, sorts newest heartbeat first, includes the free-text
    ask, and parses the fleet-manager doc when it is readable."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _queue_fakes(monkeypatch, fm_result={
        "ok": True, "status": 200, "data": _OWNER_QUEUE_MD, "error": "",
        "fetched_at": "", "cached": False, "url": ""})

    out = asyncio.run(owner_queue.overview())
    assert out["fleet_manager"]["state"] == "ok"
    whats = [i["what"] or i["text"] for i in out["items"]]
    # 4 raw asks (2 duplicate PAT + free-text + fleet-manager) -> 3 items
    assert len(out["items"]) == 3
    assert out["summary"]["deduped"] == 1
    pat = next(i for i in out["items"] if i["what"].startswith("Mint"))
    assert len(pat["sources"]) == 2  # both lanes kept on the merged item
    labels = {s["label"] for s in pat["sources"]}
    assert "websites" in labels and "substrate-kit" in labels
    # newest-first: the fresh websites heartbeat leads; the undated
    # fleet-manager item sorts last (never given an invented time).
    assert whats[0].startswith("Mint")
    assert whats[-1].startswith("Arm the coordinator")
    # the preamble pointer is a lane note, not an ask
    assert any(n["text"].startswith("preamble pointer") for n in out["lane_notes"])


def test_queue_fleet_manager_not_configured_when_token_unset(monkeypatch):
    """Token unset + fetch failed -> honest 'not-configured' state; lane items
    still present (the readable half keeps working)."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    _queue_fakes(monkeypatch)
    out = asyncio.run(owner_queue.overview())
    fm = out["fleet_manager"]
    assert fm["state"] == "not-configured"
    assert "GITHUB_TOKEN is not set" in fm["reason"]
    assert len(out["items"]) == 2  # deduped PAT ask + free-text ask
    assert out["summary"]["deduped"] == 1


def test_queue_fleet_manager_unavailable_when_token_set(monkeypatch):
    """Token present but fetch failed -> 'unavailable' with the reason, never
    a fabricated queue."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _queue_fakes(monkeypatch)
    out = asyncio.run(owner_queue.overview())
    assert out["fleet_manager"]["state"] == "unavailable"
    assert out["fleet_manager"]["reason"]


def test_queue_route_degrades_honestly_offline(client, monkeypatch):
    """/queue serves 200 with the honest not-configured banner when GitHub is
    unreachable and the token is unset (the live production state today)."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    r = client.get("/queue")
    assert r.status_code == 200
    assert "owner queue" in r.text
    assert "not configured" in r.text
    assert "GITHUB_TOKEN is not set" in r.text
    # every lane unreadable -> the honest asks-may-be-missing banner
    assert "may be missing" in r.text


def test_queue_route_renders_structured_items(monkeypatch):
    """/queue happy path (mocked upstream): structured fields render in the
    table, source lane badges present, fleet-manager doc rendered."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _queue_fakes(monkeypatch, fm_result={
        "ok": True, "status": 200, "data": _OWNER_QUEUE_MD, "error": "",
        "fetched_at": "", "cached": False, "url": ""})
    with TestClient(app) as c:
        r = c.get("/queue")
    assert r.status_code == 200
    assert "Mint the control-plane PAT." in r.text
    assert "WHY-IT-MATTERS" in r.text and "VERIFIED-NEEDED" in r.text
    assert "decide the plugin cutover window" in r.text
    assert "Arm the coordinator wake trigger." in r.text
    assert "duplicate merged" in r.text


# ---- /environments ---------------------------------------------------------

_ENV_LISTING_ROOT = [
    {"type": "file", "name": "README.md", "path": "environments/README.md"},
    {"type": "file", "name": "multi-repo.md", "path": "environments/multi-repo.md"},
    {"type": "file", "name": "SPEC-TEMPLATE.md", "path": "environments/SPEC-TEMPLATE.md"},
    {"type": "dir", "name": "templates", "path": "environments/templates"},
]
_ENV_LISTING_TEMPLATES = [
    {"type": "file", "name": "setup-universal.sh",
     "path": "environments/templates/setup-universal.sh"},
    {"type": "file", "name": "env-vars.md",
     "path": "environments/templates/env-vars.md"},
]
_ENV_BODIES = {
    "environments/README.md": "# Environments registry\n\nHow to use this.\n",
    "environments/multi-repo.md": "# Multi-repo\n\nSpanning notes.\n",
    "environments/SPEC-TEMPLATE.md": "# Spec template\n\nFill me in.\n",
    "environments/templates/setup-universal.sh":
        "#!/usr/bin/env bash\npip install -r requirements.txt\n",
    "environments/templates/env-vars.md":
        "# Env vars\n\n```\nGITHUB_TOKEN=<placeholder>\n```\n",
}


def _env_fakes(monkeypatch):
    async def fake_repo_api(repo, subpath="", refresh=False):
        assert repo == environments.REPO
        if subpath == "/contents/environments":
            return {"ok": True, "status": 200, "data": _ENV_LISTING_ROOT,
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        if subpath == "/contents/environments/templates":
            return {"ok": True, "status": 200, "data": _ENV_LISTING_TEMPLATES,
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path in _ENV_BODIES:
            return {"ok": True, "status": 200, "data": _ENV_BODIES[path],
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)
    monkeypatch.setattr(github, "fetch_file", fake_fetch)


def test_environments_overview_renders_registry(monkeypatch):
    """overview() lists root + templates/, README first, markdown rendered to
    HTML, the setup script kept as raw text for the copyable code block."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _env_fakes(monkeypatch)
    out = asyncio.run(environments.overview())
    assert out["state"] == "ok" and out["listing_errors"] == []
    paths = [f["path"] for f in out["files"]]
    assert paths[0] == "environments/README.md"
    assert set(paths) == set(_ENV_BODIES)
    readme = out["files"][0]
    assert readme["kind"] == "markdown" and "<h1" in readme["body_html"]
    sh = next(f for f in out["files"] if f["path"].endswith(".sh"))
    assert sh["kind"] == "code" and "pip install" in sh["text"]
    assert sh["github_url"].endswith("/fleet-manager/blob/main/" + sh["path"])


def test_environments_not_configured_when_token_unset(monkeypatch):
    """Listing failed + token unset -> honest 'not-configured' (the live
    production state today), never a 500 or invented files."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "Not Found",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)
    out = asyncio.run(environments.overview())
    assert out["state"] == "not-configured" and out["files"] == []
    assert "GITHUB_TOKEN is not set" in out["reason"]


def test_environments_unavailable_when_token_set(monkeypatch):
    """Listing failed with a token present -> 'unavailable' + the reason."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 403, "data": None, "error": "rate limited",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)
    out = asyncio.run(environments.overview())
    assert out["state"] == "unavailable" and "rate limited" in out["reason"]


def test_environments_route_degrades_honestly_offline(client, monkeypatch):
    """/environments serves 200 with the honest not-configured banner when the
    upstream is unreachable and the token is unset."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    r = client.get("/environments")
    assert r.status_code == 200
    assert "environments" in r.text
    assert "not configured" in r.text
    assert "GITHUB_TOKEN is not set" in r.text


def test_environments_route_renders_files_with_copy_blocks(monkeypatch):
    """/environments happy path: README HTML, script inside <pre>, and the
    copy-to-clipboard JS wired in."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _env_fakes(monkeypatch)
    with TestClient(app) as c:
        r = c.get("/environments")
        js = c.get("/static/copycode.js")
    assert r.status_code == 200
    assert "Environments registry" in r.text
    assert "pip install -r requirements.txt" in r.text
    assert "/static/copycode.js" in r.text
    assert js.status_code == 200 and "clipboard" in js.text


def test_queue_and_environments_do_not_autorefresh(client, monkeypatch):
    """The two ORDER 005 pages are content surfaces — no auto-refresh markup
    (D-0023 scoped auto-refresh to `/` + `/fleet` only)."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    for path in ["/queue", "/environments"]:
        html = client.get(path).text
        assert "/static/autorefresh.js" not in html, path
        assert 'class="autorefresh"' not in html, path


def test_queue_fleet_manager_doc_without_blocks_is_not_flattened(monkeypatch):
    """An owner-queue.md with NO ⚑ OWNER-ACTION blocks yields ZERO list items
    (a whole document is not an 'ask') — the full rendered document is the
    honest surface instead."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    _queue_fakes(monkeypatch, fm_result={
        "ok": True, "status": 200,
        "data": "# Owner queue\n\nA curated narrative list, no blocks yet.\n",
        "error": "", "fetched_at": "", "cached": False, "url": ""})
    out = asyncio.run(owner_queue.overview())
    fm = out["fleet_manager"]
    assert fm["state"] == "ok" and fm["items"] == []
    assert "<h1" in fm["body_html"]
    # only the lane asks remain in the list
    assert all(s["kind"] == "lane" for i in out["items"] for s in i["sources"])
