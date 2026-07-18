"""Offline tests for the owner environments hub (ORDER 021 slice 1):
the committed registry loader (app/envhub.py + app/data/environments.json),
the gated /owner/environments-hub route, the live variable-NAME merge, the
review-service SERVICES fix in app/railway.py, and graceful no-token behavior.

Held invariants:
- the registry stores variable NAMES and manage links only — the loader
  hard-rejects value-like fields, and no committed row can smuggle a value;
- Railway deep links are emitted ONLY from ids the repo records; unrecorded
  ids degrade to a project-level or console-home link, never a fabricated id;
- the route rides the same /owner gate as the rest of the area (401/503);
- with RAILWAY_TOKEN unset the page renders 200 from the committed registry
  alone (tests run without the token by construction);
- live names merge in for the superbot-websites group only, and variable
  VALUES never appear anywhere.
"""

import asyncio
import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, envhub, github, listfilter, railway  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture(autouse=True)
def _isolate_railway_cache():
    railway.clear_cache()
    yield
    railway.clear_cache()


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: password set, no Railway token (the
    default degraded state), GitHub fetches canned."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


# --- committed registry: shape + the no-values guarantee ---------------------


def test_registry_loads_and_has_expected_groups():
    reg = envhub.load_registry()
    ids = [g["id"] for g in reg["groups"]]
    # The ORDER 021 verified inventory: all five project groups present.
    for expected in ("superbot-websites", "reliable-grace", "superbot-mineverse",
                     "github-actions", "claude-cloud"):
        assert expected in ids, f"group {expected} missing from the registry"
    # Every group/surface carries the required fields (load_registry raised
    # otherwise); spot-check the estate group covers all four services.
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    names = {s["id"] for s in estate["surfaces"]}
    assert names == {"control-plane", "botsite", "dashboard", "review"}


def test_registry_file_carries_no_value_like_fields():
    """Defense in depth on the committed artifact itself: no dict key anywhere
    in the JSON looks like it could hold a secret value."""
    raw = json.loads(envhub.REGISTRY_PATH.read_text(encoding="utf-8"))

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                assert not any(
                    tok in k.lower() for tok in envhub.FORBIDDEN_KEY_TOKENS
                ), f"value-like registry key: {k}"
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(raw)


def test_registry_variable_names_are_bare_names():
    reg = envhub.load_registry()
    for group in reg["groups"]:
        for surface in group["surfaces"]:
            for name in surface["variable_names"]:
                assert "=" not in name and " " not in name
                assert len(name) < listfilter.MAX_VALUE_LEN


def test_loader_rejects_value_like_field(tmp_path):
    bad = {
        "as_of": "2026-07-12",
        "groups": [{
            "id": "g", "title": "g", "kind": "k", "purpose": "p",
            "surfaces": [{
                "id": "s", "name": "s", "kind": "k", "purpose": "p",
                "variable_names": ["A"],
                "variable_values": ["oops"],
            }],
        }],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="value-like"):
        envhub.load_registry(p)


def test_loader_rejects_value_shaped_variable_names(tmp_path):
    bad = {
        "as_of": "2026-07-12",
        "groups": [{
            "id": "g", "title": "g", "kind": "k", "purpose": "p",
            "surfaces": [{
                "id": "s", "name": "s", "kind": "k", "purpose": "p",
                "variable_names": ["GITHUB_PAT=ghp_notaname"],
            }],
        }],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="bare NAME"):
        envhub.load_registry(p)


def test_loader_rejects_missing_required_fields(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"groups": [{"id": "g"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field"):
        envhub.load_registry(p)


# --- manage-link degradation (never a fabricated id) --------------------------


def test_manage_link_full_deep_link_when_all_ids_recorded():
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    cp = next(s for s in estate["surfaces"] if s["id"] == "control-plane")
    link = envhub.manage_link(estate, cp)
    assert link["url"] == (
        "https://railway.com/project/70198ece-cbc0-484e-86d9-f8a1eca4f045"
        "/service/2c840017-a505-4144-b2ff-b2450430a7d9"
        "/variables?environmentId=31485ecd-b3fe-4a8f-b136-337f6f099dc2"
    )


def test_manage_link_degrades_to_project_then_console():
    reg = envhub.load_registry()
    estate = next(g for g in reg["groups"] if g["id"] == "superbot-websites")
    # review: no service id recorded → project-level link, not an invented id.
    review = next(s for s in estate["surfaces"] if s["id"] == "review")
    assert envhub.manage_link(estate, review)["url"] == (
        "https://railway.com/project/70198ece-cbc0-484e-86d9-f8a1eca4f045"
    )
    # reliable-grace: no ids at all (production, by design) → console home.
    rg = next(g for g in reg["groups"] if g["id"] == "reliable-grace")
    worker = next(s for s in rg["surfaces"] if s["id"] == "superbot-worker")
    assert envhub.manage_link(rg, worker)["url"] == envhub.CONSOLE_HOME


def test_manage_link_explicit_manage_url_wins_without_railway_ids():
    reg = envhub.load_registry()
    gh = next(g for g in reg["groups"] if g["id"] == "github-actions")
    websites = next(s for s in gh["surfaces"] if s["id"] == "gh-websites")
    assert envhub.manage_link(gh, websites)["url"] == (
        "https://github.com/menno420/websites/settings/secrets/actions"
    )


# --- gate behavior ------------------------------------------------------------


def test_requires_auth(client):
    assert client.get("/owner/environments-hub").status_code == 401
    assert (
        client.get("/owner/environments-hub", headers=_basic("wrong")).status_code
        == 401
    )


def test_fails_closed_when_password_unset(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    assert client.get("/owner/environments-hub", headers=_basic()).status_code == 503


# --- rendering from the committed registry (no token — the test default) ------


def test_hub_renders_all_groups_without_token(client):
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    for title_bit in ("superbot-websites", "reliable-grace",
                      "superbot-mineverse", "GitHub Actions secrets",
                      "claude.ai cloud environments"):
        assert title_bit in r.text, f"group {title_bit!r} missing"
    # committed variable names render; live degradation is honest.
    assert "SITE_PASSWORD" in r.text and "ANTHROPIC_API_KEY" in r.text
    assert "RAILWAY_TOKEN is not set" in r.text
    # deep link built from the recorded SAFE ids only.
    assert (
        "https://railway.com/project/70198ece-cbc0-484e-86d9-f8a1eca4f045"
        "/service/2c840017-a505-4144-b2ff-b2450430a7d9"
        "/variables?environmentId=31485ecd-b3fe-4a8f-b136-337f6f099dc2"
    ) in r.text
    # unrecorded production ids degrade to the console home, never fabricated.
    assert envhub.CONSOLE_HOME in r.text
    # per-repo GitHub secrets manage links.
    assert "https://github.com/menno420/websites/settings/secrets/actions" in r.text
    assert "https://github.com/menno420/fleet-manager/settings/secrets/actions" in r.text


def test_hub_cross_links_and_group_anchors(client):
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    # cross-links to the two existing environment pages, not duplication.
    assert 'href="/owner/environments"' in r.text
    assert 'href="/environments"' in r.text
    # list-IA summary header: jump links target the per-group sections.
    assert "jump to:" in r.text
    for anchor in ("group-superbot-websites", "group-reliable-grace",
                   "group-github-actions", "group-claude-cloud"):
        assert f'href="#{anchor}"' in r.text
        assert f'id="{anchor}"' in r.text


def test_existing_pages_link_to_the_hub(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    r = client.get("/owner/environments", headers=_basic())
    assert 'href="/owner/environments-hub"' in r.text
    r = client.get("/environments")
    assert r.status_code == 200
    assert 'href="/owner/environments-hub"' in r.text


def test_hub_group_filter_sections_and_unknown_value(client):
    # ORDER 019 reuse: ?group= narrows to one separately reviewable section.
    r = client.get(
        "/owner/environments-hub?group=github-actions", headers=_basic()
    )
    assert r.status_code == 200
    assert 'id="group-github-actions"' in r.text
    assert 'id="group-reliable-grace"' not in r.text
    # unknown filter value stays visible and matches nothing (listfilter core).
    r = client.get("/owner/environments-hub?group=nope", headers=_basic())
    assert r.status_code == 200
    assert "unknown" in r.text
    assert 'id="group-superbot-websites"' not in r.text


# --- live merge (token set, GraphQL mocked) ------------------------------------

_SENTINEL_VALUE = "sekret-live-value-456"


def _fake_graphql_ok():
    async def fake(query, variables=None):
        if "projectToken" in query:
            return {
                "ok": True,
                "data": {"projectToken": {"projectId": "p1", "environmentId": "e1"}},
                "error": "",
            }
        if "services" in query:
            return {
                "ok": True,
                "data": {
                    "project": {
                        "name": "superbot-websites",
                        "services": {
                            "edges": [
                                {"node": {"id": "s1", "name": "control-plane"}},
                                {"node": {"id": "s4", "name": "review"}},
                            ]
                        },
                    }
                },
                "error": "",
            }
        return {
            "ok": True,
            "data": {
                "variables": {
                    "LIVE_ONLY_NAME": _SENTINEL_VALUE,
                    "ANTHROPIC_API_KEY": _SENTINEL_VALUE,
                }
            },
            "error": "",
        }

    return fake


def test_live_names_merge_into_estate_rows_values_never(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql_ok())
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    assert "LIVE_ONLY_NAME" in r.text  # a name only the live read knows
    assert "set (live)" in r.text
    assert _SENTINEL_VALUE not in r.text
    assert "test-project-token" not in r.text


def _offline_repo_api(monkeypatch):
    """No-network github layer for direct overview() calls (the schema index
    half degrades honestly instead of touching the lifespan client)."""
    async def fake_repo_api(repo, subpath="", refresh=False):
        return {"ok": False, "status": 0, "data": None, "error": "offline",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)


def test_overview_merges_live_only_into_estate_group(monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    monkeypatch.setattr(railway, "_graphql", _fake_graphql_ok())
    _offline_repo_api(monkeypatch)
    data = asyncio.run(envhub.overview(refresh=True))
    assert _SENTINEL_VALUE not in repr(data)
    rows = {
        (row["group_id"], row["surface"]["id"]): row for row in data["rows"]
    }
    assert rows[("superbot-websites", "control-plane")]["live_names"] == [
        "ANTHROPIC_API_KEY", "LIVE_ONLY_NAME",
    ]
    # no live match for a service the API didn't return → committed only.
    assert rows[("superbot-websites", "botsite")]["live_names"] is None
    # live data never leaks onto other groups.
    assert rows[("reliable-grace", "superbot-worker")]["live_names"] is None


def test_overview_degrades_when_live_read_fails(monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "test-project-token")
    _offline_repo_api(monkeypatch)

    async def fake(query, variables=None):
        return {"ok": False, "data": None, "error": "ConnectError: boom"}

    monkeypatch.setattr(railway, "_graphql", fake)
    data = asyncio.run(envhub.overview(refresh=True))
    assert data["live"]["state"] == "unavailable"
    assert all(row["live_names"] is None for row in data["rows"])


# --- consolidation: the hub is THE environments home ---------------------------
#
# Owner refinement 2026-07-12: env info previously lived on three pages
# (/environments schemas, /owner/environments live estate detail, the hub).
# The hub is now the single front door — it embeds the schema INDEX and the
# live-name merge, and the two old pages are clearly-labeled sub-views.

_SCHEMA_FILES = [
    {"type": "file", "name": "README.md", "path": "environments/README.md"},
    {"type": "file", "name": "env-vars.md", "path": "environments/env-vars.md"},
]


def _schema_fakes(monkeypatch):
    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath == "/contents/environments":
            return {"ok": True, "status": 200, "data": _SCHEMA_FILES,
                    "error": "", "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "repo_api", fake_repo_api)


def test_hub_schema_section_degrades_honestly_offline(client, monkeypatch):
    """Offline + no GITHUB_TOKEN → the hub's schema section shows the honest
    not-configured banner, never invented files."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    assert 'id="schemas"' in r.text
    assert "GITHUB_TOKEN is not set" in r.text


def test_hub_schema_section_lists_registry_files(client, monkeypatch):
    """Happy path: the fleet-manager schema INDEX (names + links, no bodies)
    renders on the hub, deep-linking the full render sub-view."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _schema_fakes(monkeypatch)
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    assert "README.md" in r.text and "env-vars.md" in r.text
    assert "fleet-manager/blob/main/environments/env-vars.md" in r.text
    assert 'href="#schemas"' in r.text  # jump link in the summary header


def test_environments_index_lists_paths_without_bodies(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _schema_fakes(monkeypatch)
    from app import environments

    out = asyncio.run(environments.index())
    assert out["state"] == "ok"
    assert [f["name"] for f in out["files"]] == ["README.md", "env-vars.md"]
    assert all("body_html" not in f and "text" not in f for f in out["files"])


def test_old_pages_are_labeled_sub_views(client, monkeypatch):
    """The two pre-existing environment pages carry the sub-view framing and
    point at the hub as the front door (no scattered duplicates)."""
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    r = client.get("/owner/environments", headers=_basic())
    assert "environments-hub sub-view" in r.text
    assert 'href="/owner/environments-hub"' in r.text
    r = client.get("/environments")
    assert r.status_code == 200
    assert "environments-hub sub-view" in r.text
    assert 'href="/owner/environments-hub"' in r.text


# --- the SERVICES review fix (app/railway.py) ----------------------------------


def test_railway_services_include_review():
    names = [svc["name"] for svc in railway.SERVICES]
    assert names == ["control-plane", "botsite", "dashboard", "review"]
    review = next(s for s in railway.SERVICES if s["name"] == "review")
    assert review["package"] == "review/"
    assert review["url"] == "https://review-production-fc91.up.railway.app"
    assert review["self"] is False
    var_names = [v["name"] for v in review["env_vars"]]
    assert "ANTHROPIC_API_KEY" in var_names and "PORT" in var_names


def test_owner_environments_page_shows_review_service(client, monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "")
    r = client.get("/owner/environments", headers=_basic())
    assert r.status_code == 200
    assert "review/" in r.text
    assert "review-production-fc91.up.railway.app" in r.text
    assert "REVIEW_AI_MODEL" in r.text
