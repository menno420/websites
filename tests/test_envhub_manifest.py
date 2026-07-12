"""Offline tests for the env-creation plan/manifest generator (ORDER 021
slice 2): ``envhub.manifest()`` + the gated
``GET /owner/environments-hub/manifest/{group}`` route.

Held invariants:
- the route rides the exact /owner gate (401 unauthenticated / wrong
  password, 503 fail-closed when the password is unset);
- one manifest renders per known registry group; unknown group → 404;
- PLACEHOLDERS NEVER VALUES: every generated variable assignment pairs the
  NAME with a ``<SET-...>`` placeholder — no ``NAME=<anything real>`` can
  appear, and no value-like string exists to leak (the registry stores
  names only, by loader construction);
- the owner-executes boundary notice (docs/RAILWAY-SAFETY.md: agents make
  no Railway mutations, RAILWAY_API_KEY never on an app service, this page
  only generates the plan) is present verbatim and prominently;
- the manifest is offered rendered AND as copyable plain-text + JSON blocks
  on the same gated page — no new unauthenticated endpoint;
- the generator makes no network call at all (pure committed-registry
  read), so these tests run fully offline.
"""

import base64
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, envhub, github  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"

GROUP_IDS = (
    "superbot-websites",
    "reliable-grace",
    "superbot-mineverse",
    "github-actions",
    "claude-cloud",
)


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def client(monkeypatch):
    """Offline authed-ready client: password set, no Railway token, GitHub
    fetches canned (same shape as tests/test_envhub.py)."""
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


# --- gate behavior ------------------------------------------------------------


def test_manifest_requires_auth(client):
    url = "/owner/environments-hub/manifest/superbot-websites"
    assert client.get(url).status_code == 401
    assert client.get(url, headers=_basic("wrong")).status_code == 401


def test_manifest_fails_closed_when_password_unset(client, monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", "")
    r = client.get(
        "/owner/environments-hub/manifest/superbot-websites", headers=_basic()
    )
    assert r.status_code == 503


def test_unknown_group_404s(client):
    r = client.get("/owner/environments-hub/manifest/nope", headers=_basic())
    assert r.status_code == 404
    assert envhub.manifest("nope") is None


# --- one manifest per known group ----------------------------------------------


def test_every_registry_group_has_a_rendering_manifest(client):
    reg = envhub.load_registry()
    assert [g["id"] for g in reg["groups"]] == list(GROUP_IDS)
    for group in reg["groups"]:
        r = client.get(
            f"/owner/environments-hub/manifest/{group['id']}", headers=_basic()
        )
        assert r.status_code == 200, f"manifest for {group['id']} did not render"
        assert group["title"] in r.text
        # every surface appears in the service definitions
        for surface in group["surfaces"]:
            assert surface["name"] in r.text
        # the copyable plain-text + JSON blocks ride the same gated page
        assert "setup commands" in r.text
        assert "manifest (JSON)" in r.text


def test_hub_links_each_group_manifest(client):
    r = client.get("/owner/environments-hub", headers=_basic())
    assert r.status_code == 200
    for gid in GROUP_IDS:
        assert f'href="/owner/environments-hub/manifest/{gid}"' in r.text


# --- the boundary notice (docs/RAILWAY-SAFETY.md) --------------------------------


def test_boundary_notice_present_and_prominent(client):
    r = client.get(
        "/owner/environments-hub/manifest/superbot-websites", headers=_basic()
    )
    assert r.status_code == 200
    # the single-source notice renders verbatim (module constant → page).
    assert "docs/RAILWAY-SAFETY.md" in r.text
    assert "no Railway" in envhub.BOUNDARY_NOTICE
    assert "RAILWAY_API_KEY never lives on an app service" in r.text
    assert "OWNER-EXECUTED PLAN ONLY" in r.text
    # ... and machine-readably inside the JSON manifest too.
    m = envhub.manifest("superbot-websites")
    assert json.loads(m["manifest_json"])["boundary"] == envhub.BOUNDARY_NOTICE


def test_no_provisioning_code_in_the_generator():
    """The generator module carries no Railway mutation strings — plan
    generation only (projectCreate/serviceCreate never appear)."""
    source = Path(envhub.__file__).read_text(encoding="utf-8")
    for mutation in ("projectCreate", "serviceCreate", "variableUpsert",
                     "serviceDelete", "environmentCreate"):
        assert mutation not in source


# --- placeholders, never values ---------------------------------------------------


def test_commands_pair_every_name_with_a_placeholder_only():
    """The invariant: in the generated commands, every ``NAME=`` for a
    registry variable is immediately followed by a ``<...>`` placeholder —
    never anything value-shaped."""
    reg = envhub.load_registry()
    for group in reg["groups"]:
        m = envhub.manifest(group["id"])
        text = m["commands_text"]
        for surface in group["surfaces"]:
            for name in surface["variable_names"]:
                assignments = re.findall(rf"{re.escape(name)}=(\S+)", text)
                assert assignments, f"{name} missing from {group['id']} plan"
                for rhs in assignments:
                    assert rhs.startswith("<"), (
                        f"{group['id']}: {name}= is not followed by a "
                        f"placeholder: {rhs!r}"
                    )


def test_estate_manifest_uses_railway_console_placeholder(client):
    r = client.get(
        "/owner/environments-hub/manifest/superbot-websites", headers=_basic()
    )
    # HTML-escaped placeholder assignment for a known committed name…
    assert "SITE_PASSWORD=&lt;SET-IN-RAILWAY-CONSOLE&gt;" in r.text
    assert "railway variables --service" in r.text
    # …and never NAME= followed by anything except the escaped placeholder.
    for name in ("SITE_PASSWORD", "GITHUB_TOKEN", "RAILWAY_TOKEN",
                 "ANTHROPIC_API_KEY"):
        for match in re.finditer(rf"{name}=(?!&lt;)", r.text):
            raise AssertionError(
                f"{name}= not followed by a placeholder at {match.start()}"
            )


def test_manifest_json_schema_carries_names_and_placeholders_only():
    m = envhub.manifest("superbot-websites")
    doc = json.loads(m["manifest_json"])
    assert doc["group"]["id"] == "superbot-websites"
    names = {s["name"] for s in doc["services"]}
    assert names == {"control-plane", "botsite", "dashboard", "review"}
    for svc in doc["services"]:
        for row in svc["env_schema"]:
            assert set(row) == {"name", "placeholder"}
            assert row["placeholder"].startswith("<")
            assert row["placeholder"].endswith(">")
            assert "=" not in row["name"] and " " not in row["name"]


def test_no_registry_value_like_leak_anywhere(client):
    """Defense in depth: nothing value-shaped exists to leak (loader
    guarantee), and the page never echoes the service password or any
    forbidden-key content — spot-checked with the test password itself."""
    r = client.get(
        "/owner/environments-hub/manifest/superbot-websites", headers=_basic()
    )
    assert OWNER_PW not in r.text  # the one real secret in play never renders


# --- honest gaps: groups with unrecorded variable names -----------------------------


def test_unrecorded_names_render_honest_note_not_guesses(client):
    r = client.get(
        "/owner/environments-hub/manifest/reliable-grace", headers=_basic()
    )
    assert r.status_code == 200
    assert "not recorded in this repo" in r.text
    m = envhub.manifest("reliable-grace")
    # production group: no fabricated variable assignments at all.
    assert "--set" not in m["commands_text"]


def test_github_group_manifest_names_the_secrets_console(client):
    r = client.get(
        "/owner/environments-hub/manifest/github-actions", headers=_basic()
    )
    assert r.status_code == 200
    assert "settings/secrets/actions" in r.text
    assert "gh secret set" in r.text
