"""Dashboard smoke tests. Network-free: the data feeds are primed from fixtures so
tests never depend on raw.githubusercontent.com. The dashboard is PUBLIC ([D-0011]):
every route serves without credentials, so the pages are exercised with no auth header."""

from __future__ import annotations

import html
import json
import re

import pytest
from fastapi.testclient import TestClient

from dashboard import app as app_module  # noqa: E402
from dashboard import control_plane as cp  # noqa: E402
from dashboard import data_source as ds  # noqa: E402

DASHBOARD_FIXTURE = {
    "meta": {
        "generated_at": "2026-07-09T00:00:00Z",
        "build": {"commit": "abcdef1234", "subject": "test build", "committed_at": "2026-07-09T00:00:00Z"},
        "schema_version": 1,  # the live producer stamps meta.schema_version (int 1)
        "counts": {
            "functions": 2, "commands": 3, "setting_keys": 2, "setting_domains": 1,
            "env_vars": 1, "ideas": 1, "bugs": 1, "updates": 1, "synonyms": 1,
            "visible_subsystems": 2, "cogs": 1,
        },
    },
    "catalogue": [
        {"key": "economy", "display_name": "Economy", "description": "Coins & shop.", "emoji": "💰",
         "visibility_tier": "user", "visibility_mode": "normal", "category": "economy",
         "tags": ["coins"], "entry_points": ["economy"], "capabilities": ["economy.view"]},
        {"key": "ai", "display_name": "AI Platform", "description": "AI diagnostics.", "emoji": "🤖",
         "visibility_tier": "administrator", "visibility_mode": "normal", "category": "admin",
         "tags": ["ai"], "entry_points": ["ai"], "capabilities": ["ai.view"]},
    ],
    "cogs": [
        {"cog": "EconomyCog", "file": "disbot/cogs/economy.py", "subsystem": "economy", "is_cog": True,
         "commands": [
             {"name": "daily", "type": "prefix", "is_group": False, "parent": None, "aliases": ["d"],
              "brief": "Claim daily coins.", "button_backed": False},
             {"name": "shop", "type": "both", "is_group": True, "parent": None, "aliases": [],
              "brief": "Open the shop.", "button_backed": True},
             {"name": "buy", "type": "slash", "is_group": False, "parent": "shop", "aliases": [],
              "brief": "Buy an item.", "button_backed": False},
         ]},
    ],
    "settings": [
        {"domain": "economy", "purpose": "Economy settings.", "keys": [
            {"constant": "DAILY_AMOUNT", "key": "daily_amount", "type": "int", "hint": "Coins per daily.",
             "allowed_values": [], "default": 100},
            {"constant": "SHOP_ENABLED", "key": "shop_enabled", "type": "bool", "hint": "Master switch.",
             "allowed_values": [], "default": True},
        ]},
    ],
    "access": {
        "tiers": [
            {"tier": "user", "discord_permission": None, "subsystems": [
                {"key": "economy", "display_name": "Economy", "category": "economy", "emoji": "💰"}]},
            {"tier": "administrator", "discord_permission": "administrator", "subsystems": [
                {"key": "ai", "display_name": "AI Platform", "category": "admin", "emoji": "🤖"}]},
        ],
        "total_visible": 2, "internal_count": 0,
    },
    "env_usage": [
        {"name": "DATABASE_URL", "required": True, "usage_count": 1, "layers": ["utils"],
         "usages": [{"file": "disbot/utils/db/pool.py", "line": 41, "layer": "utils", "has_default": False}]},
    ],
    "ideas": [
        {"file": "some-idea-2026-07-08.md", "title": "A good idea", "status": "ideas",
         "date": "2026-07-08", "summary": "Do the thing.", "subsystems": None},
    ],
    "bugs": [
        {"id": "BUG-0001", "title": "Something broke", "status": "OPEN", "summary": "It broke."},
    ],
    "updates": [
        {"file": "2026-07-08-x.md", "date": "2026-07-08", "title": "Session X", "status": "complete",
         "run_type": "", "self_initiated": True},
    ],
    "synonyms": [{"canonical": "daily", "synonyms": ["dailies"]}],
    "bot_changelog": [{"date": "2026-06-19", "title": "New site", "kind": "improvement", "summary": "New."}],
}

# Shaped per the pinned cross-repo contract (dashboard/console_data_contract.json,
# v1): ideas/bugs are counter DICTS, meta carries schema_version, telemetry exists.
CONSOLE_FIXTURE = {
    "meta": {"generated_at": "2026-07-08T16:20:05Z", "build": {"commit": "e9988b3b"},
             "schema_version": 1},
    "sessions": [{"file": "2026-07-08-x.md", "date": "2026-07-08", "title": "Session X",
                  "status": "complete", "run_type": "", "self_initiated": False}],
    "ideas": {"total": 221, "by_status": {"ideas": 200, "historical": 21}},
    "bugs": {"total": 30, "by_status": {"fixed": 27, "open": 3}, "open_count": 3,
             "open": [{"id": "BUG-0031", "title": "Something is off", "status": "open"}]},
    "bot_changelog": [{"date": "2026-06-19", "title": "New site", "kind": "improvement", "summary": "New."}],
    "telemetry": [{"session": "2026-07-08-x", "date": "2026-07-08", "model": "fable-5",
                   "effort": "high", "task_class": "docs-only", "tokens_out": None,
                   "outcome": {"ci_green_first_push": None, "checker_findings": None,
                               "merged_pr": None, "reverted_within_window": None}}],
}

# The committed arcade registry is a LIST of game entries (botsite/data/arcade.json).
# Mix chosen so live/blocked are both non-zero and distinguishable: a live game with
# a url, a download game with a url (both "live" = reachable link), and an
# unavailable game with no url (blocked). live=2, blocked=1, total=3.
ARCADE_FIXTURE = [
    {"slug": "live-game", "name": "Live Game", "tagline": "t", "description": "d",
     "maturity": "playable", "availability": "live", "source_repo": "menno420/x",
     "url": "https://live.example", "status_note": ""},
    {"slug": "dl-game", "name": "DL Game", "tagline": "t", "description": "d",
     "maturity": "beta", "availability": "download", "source_repo": "menno420/y",
     "url": "https://dl.example/rom", "status_note": ""},
    {"slug": "blocked-game", "name": "Blocked Game", "tagline": "t", "description": "d",
     "maturity": "beta", "availability": "unavailable", "source_repo": "menno420/z",
     "url": None, "status_note": "pending owner click",
     "blocker": {"owner_action": "click", "unblocks": "launch", "ask_id": "ASK-9999"}},
]

READ_ONLY_PATHS = [
    "/", "/functions", "/commands", "/aliases", "/settings", "/access",
    "/env", "/ideas", "/bugs", "/updates", "/status", "/console", "/admin",
    "/admin/settings/economy", "/admin/cogs", "/admin/help", "/admin/audit",
    "/admin/login",
]


@pytest.fixture()
def client():
    ds.clear_cache()
    cp.controller.clear()  # the dry-run audit log is per-process; isolate tests
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.prime_cache(ds.ARCADE_JSON_URL, ARCADE_FIXTURE)
    # /status now also fetches review's baked release-drift mirror; prime it empty
    # so the page never does a live fetch (no drift entries -> no drift card).
    ds.prime_cache(ds.RELEASES_JSON_URL, {"entries": [], "drift_count": 0})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()
    cp.controller.clear()


# --- public access (no auth) ---------------------------------------------
def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_version_returns_env_sha(client, monkeypatch):
    """/version reports the deployed SHA from RAILWAY_GIT_COMMIT_SHA (primary)."""
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "deadbeef1234567890")
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body == {"service": "dashboard", "sha": "deadbeef1234567890", "short": "deadbeef"}


def test_version_falls_back_to_git_sha(client, monkeypatch):
    """GIT_SHA (baked at Docker build) is the fallback when Railway's var is absent."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.setenv("GIT_SHA", "cafebabecafebabe")
    body = client.get("/version").json()
    assert body["sha"] == "cafebabecafebabe" and body["short"] == "cafebabe"


def test_favicon_ico_serves_site_icon(client):
    """/favicon.ico answers the browser's own probe (raw JSON views carry no
    <link rel="icon"> — the PR #321 fleet-wide 404 finding) with the same SVG
    the HTML pages declare."""
    r = client.get("/favicon.ico")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in r.content


def test_version_unknown_when_unset(client, monkeypatch):
    """Neither env var set → honest 'unknown', never a crash or a faked value."""
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GIT_SHA", raising=False)
    body = client.get("/version").json()
    assert body == {"service": "dashboard", "sha": "unknown", "short": "unknown"}


def test_root_is_public_no_auth(client):
    # The Basic-auth gate is gone ([D-0011]); every route serves without creds.
    r = client.get("/")
    assert r.status_code == 200
    assert "www-authenticate" not in {k.lower() for k in r.headers}


# --- consolidation redirects (/games, /reviews) --------------------------
# The OLD dashboard served /games and /reviews; on this NEW dashboard that
# content was deliberately RE-HOMED (games -> botsite service, reviews ->
# review service), so those paths would 404. The routes 302-forward to the
# re-homed surfaces so inbound links survive the duplicate-sites cutover.
def test_games_redirects_to_botsite(client):
    r = client.get("/games", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert "botsite" in loc and loc.endswith("/games")


def test_reviews_redirects_to_review_service(client):
    r = client.get("/reviews", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert "review" in loc and loc.endswith("/reviews")


def test_redirect_targets_are_env_overridable(client, monkeypatch):
    """The redirect targets resolve from BOTSITE_GAMES_URL / REVIEW_REVIEWS_URL
    (defaults otherwise). They are resolved into module constants at import, so
    the routes read those constants — patch them to prove the override path a
    cutover domain-rename would use lands in the Location header."""
    monkeypatch.setattr(app_module, "BOTSITE_GAMES_URL", "https://new-botsite.example/games")
    monkeypatch.setattr(app_module, "REVIEW_REVIEWS_URL", "https://new-review.example/reviews")
    assert client.get("/games", follow_redirects=False).headers["location"] == "https://new-botsite.example/games"
    assert client.get("/reviews", follow_redirects=False).headers["location"] == "https://new-review.example/reviews"


def test_redirect_degrades_honestly_when_target_unresolved(client, monkeypatch):
    """If a target resolves empty (env blanked, no default) the route serves a
    small linking page (200), never a redirect to "" or a 500."""
    monkeypatch.setattr(app_module, "BOTSITE_GAMES_URL", "")
    r = client.get("/games", follow_redirects=False)
    assert r.status_code == 200
    assert "moved" in r.text.lower() and 'href="/"' in r.text


# --- read-only pages -----------------------------------------------------
@pytest.mark.parametrize("path", READ_ONLY_PATHS)
def test_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert "SuperBot" in r.text


def test_overview_shows_real_counts(client):
    r = client.get("/")
    assert ">2<" in r.text  # subsystem count from the fixture
    assert "Economy" in r.text


def test_commands_lists_real_commands(client):
    r = client.get("/commands")
    assert "!daily" in r.text
    assert "!shop buy" in r.text  # subcommand rendered with parent


def test_env_map_shows_names_not_values(client):
    r = client.get("/env")
    assert "DATABASE_URL" in r.text
    assert "disbot/utils/db/pool.py:41" in r.text
    assert "never a value" in r.text.lower() or "never a secret" in r.text.lower()


def test_env_drift_clean_state_renders(client):
    """The default fixture's DATABASE_URL is required with a hard (no-default)
    read — consistent, so /env shows the honest clean state, no flags."""
    r = client.get("/env")
    assert 'data-drift="clean"' in r.text
    assert "No config drift detected" in r.text
    assert 'data-drift="flagged"' not in r.text


def test_env_drift_flags_render(client):
    """A feed carrying both drift shapes surfaces both flags on /env with their
    buckets and human labels; the consistent var is not flagged."""
    drifted = {
        **DASHBOARD_FIXTURE,
        "env_usage": [
            {"name": "DATABASE_URL", "required": True, "usage_count": 1, "layers": ["utils"],
             "usages": [{"file": "disbot/utils/db/pool.py", "line": 41, "has_default": False}]},
            {"name": "OPTIONAL_NO_DEFAULT", "required": False, "usage_count": 1, "layers": ["core"],
             "usages": [{"file": "disbot/core/x.py", "line": 7, "has_default": False}]},
            {"name": "REQUIRED_ALL_DEFAULTED", "required": True, "usage_count": 1, "layers": ["core"],
             "usages": [{"file": "disbot/core/y.py", "line": 9, "has_default": True}]},
        ],
    }
    with _client_with_dashboard(drifted) as c:
        r = c.get("/env")
        assert 'data-drift="flagged"' in r.text
        assert "Config drift" in r.text
        assert 'data-drift="optional_but_undefended"' in r.text
        assert 'data-drift="required_but_defaulted"' in r.text
        assert "optional but no default" in r.text
        assert "required but always defaulted" in r.text
        assert "OPTIONAL_NO_DEFAULT" in r.text
        assert "REQUIRED_ALL_DEFAULTED" in r.text
        # The consistent var is NOT presented as a flagged drift item.
        assert 'data-drift="clean"' not in r.text
    ds.clear_cache()


def test_settings_render(client):
    r = client.get("/settings")
    assert "daily_amount" in r.text
    assert "Coins per daily." in r.text


def test_access_ladder(client):
    r = client.get("/access")
    assert "AI Platform" in r.text
    assert "administrator" in r.text


def test_aliases_taken_map_embedded(client):
    r = client.get("/aliases")
    assert "dailies" in r.text  # existing synonym shown
    assert "taken-map" in r.text  # collision map embedded for the client checker


def test_nav_includes_console_and_aliases(client):
    """Clarity: /console and /aliases are discoverable from the primary nav.
    The aria-current marker proves they are real NAV entries, not drawer extras."""
    r = client.get("/")
    assert 'class="sb-nav-link" href="/aliases"' in r.text
    assert 'class="sb-nav-link" href="/console"' in r.text
    assert 'href="/aliases" aria-current="page"' in client.get("/aliases").text
    assert 'href="/console" aria-current="page"' in client.get("/console").text


# --- the control panel: DRY-RUN management UX (consciously updated from the
# --- four-inert-cards stub — the honest labels are pinned here) ------------
def test_admin_is_honestly_labeled_dry_run(client):
    r = client.get("/admin")
    assert r.status_code == 200
    assert "DRY-RUN" in r.text
    assert "cannot affect the live bot" in r.text.lower()
    assert "holds no credentials" in r.text.lower()
    assert "clears on restart" in r.text.lower()  # audit-log honesty label
    # The submission-moderation card stays inert, gated on Q5, with its honest tag.
    assert "requires owner wiring" in r.text.lower()
    assert "stub-action" in r.text


def test_no_control_api_token_or_url_anywhere():
    """Hard guarantee: this service references no production bot control-API URL/token —
    not in Python source and not in any served template. The literal env-var identifiers
    a live-write control panel would need never appear anywhere in this service."""
    import pathlib

    root = pathlib.Path(app_module.__file__).resolve().parent
    forbidden = ["CONTROL_API_TOKEN", "CONTROL_API_URL", "worker.railway.internal", "DISCORD_OAUTH_CLIENT_SECRET"]
    for f in list(root.rglob("*.py")) + list(root.rglob("*.html")):
        if "tests" in f.parts:
            continue
        text = f.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{needle} must not appear in {f}"


# --- dry-run controller seam + the pinned bot-control contract -------------
GUILD = "123456789012345678"


def _extract_request_json(page_text: str) -> dict:
    m = re.search(r'<pre class="snippet" id="request-json">(.*?)</pre>', page_text, re.S)
    assert m, "the page must embed the exact request JSON"
    return json.loads(html.unescape(m.group(1)))


def test_control_contract_parses_and_is_v1():
    contract = cp.load_control_contract()
    assert contract["version"] == 1
    # Every UI-previewable action is defined in the pin; requests carry schema_version.
    for action in cp.UI_ACTIONS:
        assert action in contract["actions"]
    assert "schema_version" in contract["request"]
    assert "dry_run" in contract["request"]


def test_every_ui_previewable_action_validates_against_contract(client):
    """Each action the /admin UI can build must produce a contract-valid request."""
    data = DASHBOARD_FIXTURE
    forms = {
        "setting.write": {"guild_id": GUILD, "domain": "economy", "key": "daily_amount", "value": "250"},
        "cog.set_enabled": {"guild_id": GUILD, "cog": "EconomyCog", "enabled": "true"},
        "help.appearance.set": {"guild_id": GUILD, "entity_type": "command", "entity": "daily",
                                "display_name": "Daily reward"},
    }
    assert set(forms) == set(cp.UI_ACTIONS)
    for action, form in forms.items():
        req = cp.controller.build_request(action, form, data)
        assert cp.contract_issue(req) == ""
        assert req["dry_run"] is True
        assert req["actor"]["display"] == "anonymous (OAuth not configured)"


def test_preview_shows_exact_typed_contract_request(client):
    r = client.post("/admin/actions/preview", data={
        "action": "setting.write", "guild_id": GUILD,
        "domain": "economy", "key": "daily_amount", "value": "250",
    })
    assert r.status_code == 200
    req = _extract_request_json(r.text)
    assert cp.contract_issue(req) == ""
    assert req["params"]["value"] == 250  # typed by the schema: int, not "250"
    assert req["dry_run"] is True
    assert "Confirm" in r.text and "record dry-run" in r.text
    assert cp.controller.entries() == []  # previewing records nothing


def test_preview_invalid_setting_value_rejected(client):
    r = client.post("/admin/actions/preview", data={
        "action": "setting.write", "guild_id": GUILD,
        "domain": "economy", "key": "shop_enabled", "value": "banana",
    })
    assert r.status_code == 400
    assert "nothing was recorded" in r.text.lower()
    assert "invalid_value" in r.text
    assert cp.controller.entries() == []


def test_preview_unknown_cog_rejected(client):
    r = client.post("/admin/actions/preview", data={
        "action": "cog.set_enabled", "guild_id": GUILD, "cog": "NopeCog", "enabled": "true",
    })
    assert r.status_code == 400
    assert "unknown_cog" in r.text


def test_preview_bad_guild_id_rejected(client):
    r = client.post("/admin/actions/preview", data={
        "action": "setting.write", "guild_id": "not-a-guild",
        "domain": "economy", "key": "daily_amount", "value": "5",
    })
    assert r.status_code == 400
    assert "digits" in r.text


def test_help_appearance_requires_a_change(client):
    r = client.post("/admin/actions/preview", data={
        "action": "help.appearance.set", "guild_id": GUILD,
        "entity_type": "command", "entity": "daily",
        "display_name": "", "description": "",
    })
    assert r.status_code == 400
    assert "no_changes" in r.text


def test_confirm_records_audit_entry_and_is_honest(client):
    r = client.post("/admin/actions/confirm", data={
        "action": "setting.write", "guild_id": GUILD,
        "domain": "economy", "key": "shop_enabled", "value": "false",
        "idempotency_key": "k-test-123", "requested_at": "2026-07-11T00:00:00Z",
    })
    assert r.status_code == 200
    assert "recorded, not sent" in r.text.lower()
    entries = cp.controller.entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "setting.write"
    assert entry["outcome"] == "dry-run: recorded, not sent"
    # The confirmed request preserves the previewed envelope fields verbatim.
    assert entry["request"]["idempotency_key"] == "k-test-123"
    assert entry["request"]["requested_at"] == "2026-07-11T00:00:00Z"
    assert entry["request"]["params"]["value"] is False
    assert cp.contract_issue(entry["request"]) == ""


def test_audit_page_renders_recorded_entries(client):
    client.post("/admin/actions/confirm", data={
        "action": "cog.set_enabled", "guild_id": GUILD, "cog": "EconomyCog", "enabled": "false",
    })
    r = client.get("/admin/audit")
    assert r.status_code == 200
    assert "cog.set_enabled" in r.text
    assert "anonymous (OAuth not configured)" in r.text
    assert "clears on restart" in r.text.lower()  # honest lifetime label


def test_admin_login_page_is_honest(client):
    r = client.get("/admin/login")
    assert r.status_code == 200
    assert "not configured" in r.text.lower()
    assert "separate service" in r.text.lower()


def test_unknown_settings_domain_404(client):
    assert client.get("/admin/settings/not-a-domain").status_code == 404


def test_settings_domain_lede_says_what_it_does(client):
    """Clarity: the domain page says what you can DO here — browse typed keys and
    stage a dry-run change — on top of the schema-fed purpose line."""
    r = client.get("/admin/settings/economy")
    assert r.status_code == 200
    assert "Economy settings." in r.text  # the domain purpose stays
    assert "Browse each key" in r.text
    assert "nothing is ever written to the bot" in r.text


# --- honest degradation --------------------------------------------------
def test_degrades_when_feed_unavailable():
    """No fake data: a failed feed shows the honest error banner, still 200."""
    ds.clear_cache()

    class _Boom:
        async def get(self, *a, **k):
            raise RuntimeError("network down")

        async def aclose(self):
            pass

    ds.set_client(_Boom())  # type: ignore[arg-type]
    with TestClient(app_module.app) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "temporarily unavailable" in r.text.lower()
    ds.clear_cache()


def test_palette_index(client):
    r = client.get("/palette.json")
    assert r.status_code == 200
    labels = [i.get("label") for i in r.json()]
    assert "Overview" in labels
    assert "Economy" in labels  # subsystem indexed


# --- dashboard.json schema version pin (cross-repo) ------------------------
def _client_with_dashboard(data):
    """A TestClient whose dashboard.json cache is primed with ``data`` (network-free)."""
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, data)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    ds.prime_cache(ds.ARCADE_JSON_URL, ARCADE_FIXTURE)
    ds.prime_cache(ds.RELEASES_JSON_URL, {"entries": [], "drift_count": 0})
    ds.set_client(ds.make_client())
    return TestClient(app_module.app)


def test_dashboard_matching_schema_version_renders_clean(client):
    """The fixture carries the pinned version (int 1, as the live producer ships):
    pages render normally with no drift banner."""
    r = client.get("/")
    assert r.status_code == 200
    assert "schema drift" not in r.text.lower()
    assert ds.dashboard_schema_issue(DASHBOARD_FIXTURE) == ""


def test_dashboard_string_schema_version_also_accepted():
    """A producer shipping "1" (string) instead of 1 (int) still matches the pin."""
    stringy = {**DASHBOARD_FIXTURE, "meta": {**DASHBOARD_FIXTURE["meta"], "schema_version": "1"}}
    assert ds.dashboard_schema_issue(stringy) == ""
    with _client_with_dashboard(stringy) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "schema drift" not in r.text.lower()
    ds.clear_cache()


def test_dashboard_newer_schema_version_shows_banner():
    """A version bump upstream degrades honestly: explicit banner, still 200."""
    drifted = {**DASHBOARD_FIXTURE, "meta": {**DASHBOARD_FIXTURE["meta"], "schema_version": 99}}
    with _client_with_dashboard(drifted) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "newer than this consumer" in r.text
    ds.clear_cache()


def test_dashboard_older_schema_version_shows_banner():
    older = {**DASHBOARD_FIXTURE, "meta": {**DASHBOARD_FIXTURE["meta"], "schema_version": 0}}
    with _client_with_dashboard(older) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "older than this consumer" in r.text
    ds.clear_cache()


def test_dashboard_missing_schema_version_shows_banner_never_crashes():
    """No meta.schema_version at all = explicit unknown state on every page, no 500."""
    meta_without = {k: v for k, v in DASHBOARD_FIXTURE["meta"].items() if k != "schema_version"}
    stripped = {**DASHBOARD_FIXTURE, "meta": meta_without}
    assert ds.dashboard_schema_issue(stripped) != ""
    with _client_with_dashboard(stripped) as c:
        for path in ("/", "/commands", "/status"):
            r = c.get(path)
            assert r.status_code == 200
            assert "schema drift" in r.text.lower()
            assert "no meta.schema_version" in r.text
    ds.clear_cache()


def test_dashboard_non_numeric_schema_version_degrades():
    """Garbage versions never raise — they fold into the explicit unknown message."""
    weird = {**DASHBOARD_FIXTURE, "meta": {**DASHBOARD_FIXTURE["meta"], "schema_version": "v2-beta"}}
    issue = ds.dashboard_schema_issue(weird)
    assert "not a version" in issue
    with _client_with_dashboard(weird) as c:
        r = c.get("/")
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
    ds.clear_cache()


# --- console feed shape contract (cross-repo pin) --------------------------
def test_console_renders_contracted_counter_dicts(client):
    """ideas/bugs are contracted counter DICTS; the tiles show total/open_count
    (the dict-vs-list defect the contract surfaced), and no drift banner shows."""
    r = client.get("/console")
    assert r.status_code == 200
    assert "221" in r.text  # ideas.total, not len(dict)==2
    assert "Open bugs" in r.text and "BUG-0031" in r.text
    assert "schema drift" not in r.text.lower()


def test_console_schema_version_mismatch_shows_banner():
    drifted = {**CONSOLE_FIXTURE, "meta": {**CONSOLE_FIXTURE["meta"], "schema_version": 99}}
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, drifted)
    ds.set_client(ds.make_client())
    with TestClient(app_module.app) as c:
        r = c.get("/console")
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "schema_version=99" in r.text
    ds.clear_cache()


def test_console_missing_family_shows_banner():
    shrunk = {k: v for k, v in CONSOLE_FIXTURE.items() if k != "telemetry"}
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, shrunk)
    ds.set_client(ds.make_client())
    with TestClient(app_module.app) as c:
        r = c.get("/console")
        assert r.status_code == 200
        assert "schema drift" in r.text.lower()
        assert "telemetry" in r.text
    ds.clear_cache()


def test_pinned_contract_matches_what_this_consumer_reads():
    """The pinned copy must cover everything the console route/template reads,
    and the fixture must satisfy it (so tests exercise the real shape)."""
    contract = ds.load_console_contract()
    assert isinstance(contract["version"], int)
    # Every family the route reads is contracted.
    for family in ("meta", "sessions", "ideas", "bugs", "bot_changelog"):
        assert family in contract["top_level"]
    # The fixture IS the contracted shape (version + families + counter dicts).
    assert ds.console_contract_issue(CONSOLE_FIXTURE) == ""
    assert set(CONSOLE_FIXTURE) == set(contract["top_level"])
    assert set(CONSOLE_FIXTURE["ideas"]) <= set(contract["ideas"])
    assert set(CONSOLE_FIXTURE["bugs"]) <= set(contract["bugs"])
    for row in CONSOLE_FIXTURE["sessions"]:
        assert set(row) == set(contract["session"])
    for row in CONSOLE_FIXTURE["telemetry"]:
        assert set(row) == set(contract["telemetry"])


# --- /ideas backlog hero: shipped count -----------------------------------
def test_idea_stats_counts_shipped_open_total():
    """Pure helper: shipped = done/implemented (badge's own set), open = rest,
    case/whitespace-insensitive; blank/missing status counts as open, no raise."""
    data = {"ideas": [
        {"title": "a", "status": "ideas"},
        {"title": "b", "status": "Done"},          # cased -> shipped
        {"title": "c", "status": " implemented "},  # padded -> shipped
        {"title": "d", "status": "proposed"},        # open
        {"title": "e"},                              # missing status -> open
    ]}
    assert ds.idea_stats(data) == {"total": 5, "shipped": 2, "open": 3}


def test_idea_stats_empty_and_none_safe():
    assert ds.idea_stats({}) == {"total": 0, "shipped": 0, "open": 0}
    assert ds.idea_stats({"ideas": None}) == {"total": 0, "shipped": 0, "open": 0}


def test_ideas_hero_shows_shipped_count():
    """A backlog with a shipped idea surfaces '· K shipped' on the hero — the
    same total·secondary idiom /bugs uses; K equals the shipped-status count."""
    data = {**DASHBOARD_FIXTURE, "ideas": [
        {"file": "x.md", "title": "Done thing", "status": "implemented",
         "date": "2026-07-01", "summary": "Shipped."},
        {"file": "y.md", "title": "Pending thing", "status": "ideas",
         "date": "2026-07-02", "summary": "Not yet."},
    ]}
    with _client_with_dashboard(data) as c:
        r = c.get("/ideas")
        assert r.status_code == 200
        assert "2 ideas" in r.text
        assert "1 shipped" in r.text
    ds.clear_cache()


def test_ideas_hero_omits_shipped_when_none():
    """No shipped idea -> the '· N shipped' segment is omitted (no noise), not
    '0 shipped'."""
    data = {**DASHBOARD_FIXTURE, "ideas": [
        {"file": "y.md", "title": "Pending", "status": "ideas", "summary": "x"},
    ]}
    with _client_with_dashboard(data) as c:
        r = c.get("/ideas")
        assert r.status_code == 200
        assert "1 ideas" in r.text
        assert "shipped" not in r.text
    ds.clear_cache()


# --- /ideas lifecycle-status filter pills ----------------------------------
def test_idea_bucket_lanes_shipped_vs_open():
    """Pure helper: shipped statuses (idea_stats' own set) bucket 'shipped';
    everything else — including cased/padded, blank, and missing — buckets
    'open', never raises."""
    assert ds.idea_bucket({"status": "done"}) == "shipped"
    assert ds.idea_bucket({"status": " Implemented "}) == "shipped"  # cased+padded
    assert ds.idea_bucket({"status": "ideas"}) == "open"
    assert ds.idea_bucket({"status": ""}) == "open"
    assert ds.idea_bucket({}) == "open"


def test_ideas_status_pills_render_and_bucket_cards():
    """A mixed backlog surfaces the all/open/shipped filter bar, and each card
    carries the data-cat lane the shared client-side filter keys on."""
    data = {**DASHBOARD_FIXTURE, "ideas": [
        {"file": "x.md", "title": "Done thing", "status": "implemented", "summary": "Shipped."},
        {"file": "y.md", "title": "Pending thing", "status": "ideas", "summary": "Not yet."},
    ]}
    with _client_with_dashboard(data) as c:
        r = c.get("/ideas")
        assert r.status_code == 200
        assert 'data-filter-pill="all"' in r.text
        assert 'data-filter-pill="open"' in r.text
        assert 'data-filter-pill="shipped"' in r.text
        assert 'data-cat="shipped"' in r.text  # the implemented idea's lane
        assert 'data-cat="open"' in r.text  # the still-open idea's lane
    ds.clear_cache()


def test_ideas_status_pills_hidden_on_uniform_backlog():
    """No shipped idea -> no filter bar (nothing to separate); the list stays a
    plain search-only page, no 'shipped'/'open' pill noise."""
    data = {**DASHBOARD_FIXTURE, "ideas": [
        {"file": "y.md", "title": "Pending", "status": "ideas", "summary": "x"},
    ]}
    with _client_with_dashboard(data) as c:
        r = c.get("/ideas")
        assert r.status_code == 200
        assert 'data-filter-pill="shipped"' not in r.text
        assert 'data-filter-pill="open"' not in r.text
        assert 'data-cat="open"' in r.text  # card still lane-tagged for when a pill appears
    ds.clear_cache()


# --- /status arcade live/blocked counts (B1) ------------------------------
def test_arcade_counts_known_fixture():
    """Pure helper: live = reachable link (availability live/download AND a url),
    blocked = the honest inverse, live+blocked == total. Mirrors
    botsite.arcade.availability_summary's live/blocked over the raw feed shape."""
    assert ds.arcade_counts(ARCADE_FIXTURE) == {"total": 3, "live": 2, "blocked": 1}


def test_arcade_counts_fail_soft_on_bad_input():
    """Never raises on feed content: a non-list input degrades to all-zero, a
    non-dict entry is skipped, and a live entry with no url is blocked (not a
    false live). Same degrade-don't-invent posture as the rest of the module."""
    assert ds.arcade_counts(None) == {"total": 0, "live": 0, "blocked": 0}
    assert ds.arcade_counts("nope") == {"total": 0, "live": 0, "blocked": 0}
    mixed = [
        "not-a-dict",
        {"availability": "live", "url": ""},        # live-claimed but no url -> blocked
        {"availability": "live", "url": "https://a"},  # reachable -> live
    ]
    assert ds.arcade_counts(mixed) == {"total": 2, "live": 1, "blocked": 1}


def test_status_shows_arcade_live_blocked_counts(client):
    """/status renders the arcade line with live and blocked counts from the feed."""
    r = client.get("/status")
    assert r.status_code == 200
    assert "3 games" in r.text
    assert "2 live" in r.text
    assert "1 blocked" in r.text


def test_status_arcade_degrades_honestly_when_feed_unavailable():
    """No fake data: a failed arcade fetch shows an honest 'unavailable' on /status
    (still 200) — never a false '0 live / 0 blocked'. The bot feeds stay warm from
    cache, so only the arcade fetch actually hits the (failing) client."""
    ds.clear_cache()
    ds.prime_cache(ds.DASHBOARD_JSON_URL, DASHBOARD_FIXTURE)
    ds.prime_cache(ds.CONSOLE_JSON_URL, CONSOLE_FIXTURE)
    # arcade.json is deliberately NOT primed -> fetch_arcade hits the client below.

    class _ArcadeBoom:
        async def get(self, url, *a, **k):
            raise RuntimeError("arcade feed down")

        async def aclose(self):
            pass

    ds.set_client(_ArcadeBoom())  # type: ignore[arg-type]
    with TestClient(app_module.app) as c:
        r = c.get("/status")
        assert r.status_code == 200
        assert "counts unavailable" in r.text.lower()
        assert "0 live" not in r.text  # honest '—', never a faked zero
    ds.clear_cache()
