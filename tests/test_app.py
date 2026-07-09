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

from app import activity, config, github, ideas, journal, readiness  # noqa: E402
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


def test_ideas_route_degrades_no_auth(client):
    """/ideas serves 200 even when GitHub is unreachable (honest empty state)."""
    r = client.get("/ideas")
    assert r.status_code == 200
    assert "what's queued to build" in r.text
    rj = client.get("/ideas.json")
    assert rj.status_code == 200 and isinstance(rj.json(), list)


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
