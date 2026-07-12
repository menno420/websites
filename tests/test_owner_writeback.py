"""ORDER 020 — owner writeback console (/owner/queue) tests.

Offline, mirroring tests/test_owner_security.py: TestClient, monkeypatched
env + GitHub client seams, never the network. Pins the honest-capability
contract: auth/same-origin/rate-limit on every state change; submissions
stored locally FIRST; ``committed`` claimed ONLY when a mocked contents-API
PUT returns a commit SHA (never faked on failure); the AI drafting assist
degrades honestly without the key and never stores anything itself.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, owner, owner_assist, writeback  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"
CROSS_ORIGIN = "https://evil.example"

FAKE_INBOX = (
    "# Inbox\n\n"
    "## ORDER 018 · 2026-07-12T10:00Z · status: new\n"
    "do: something\n\n"
    "## ORDER 019 · 2026-07-12T15:42Z · status: new\n"
    "do: something else\n"
)
COMMIT_SHA = "deadbeefcafe0123456789abcdef0123456789ab"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _headers() -> dict:
    return {**_basic(), "Origin": SAME_ORIGIN}


@pytest.fixture(autouse=True)
def _reset_state():
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()
    yield
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Authed-ready, fully offline client: password set, per-test SQLite,
    no GITHUB_TOKEN / ANTHROPIC_API_KEY, every GitHub seam faked."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    monkeypatch.delenv(owner_assist.ENV_API_KEY, raising=False)

    async def fake_get(url, refresh=False, raw=False):
        return {
            "ok": False, "status": 0, "data": None,
            "error": "offline test", "fetched_at": "", "cached": False,
            "url": url,
        }

    monkeypatch.setattr(github, "_get", fake_get)

    async def fail_api_request(method, path, json_body=None, token=""):
        raise AssertionError(
            "github.api_request must not be reached in this test"
        )

    monkeypatch.setattr(github, "api_request", fail_api_request)
    with TestClient(app) as c:
        yield c


def _fake_api(monkeypatch, *, read_status=200, read_text=FAKE_INBOX,
              put_status=200, put_sha=COMMIT_SHA):
    """Install a recording contents-API fake; returns the call list."""
    calls: list[tuple] = []

    async def fake(method, path, json_body=None, token=""):
        calls.append((method, path, json_body, token))
        if method == "GET":
            if read_status != 200:
                return {"ok": False, "status": read_status, "data": None,
                        "error": "Not Found"}
            return {
                "ok": True, "status": 200,
                "data": {
                    "content": base64.b64encode(
                        read_text.encode()).decode(),
                    "sha": "blobsha123",
                },
                "error": "",
            }
        if put_status == 200:
            return {
                "ok": True, "status": 200,
                "data": {"commit": {
                    "sha": put_sha,
                    "html_url": (
                        "https://github.com/menno420/websites/commit/"
                        + put_sha
                    ),
                }},
                "error": "",
            }
        return {"ok": False, "status": put_status, "data": None,
                "error": "Resource not accessible by personal access token"}

    monkeypatch.setattr(github, "api_request", fake)
    return calls


# --------------------------------------------------------------------------
# security floor: auth → same-origin → rate limit, exactly like ORDER 013
# --------------------------------------------------------------------------
def test_console_requires_auth(client):
    assert client.get("/owner/queue").status_code == 401
    r = client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "hi"},
        headers={"Origin": SAME_ORIGIN},
    )
    assert r.status_code == 401


def test_every_writeback_post_rejects_cross_origin(client):
    for route, data in [
        ("complete", {"target": "x", "text": ""}),
        ("assist", {"target": "", "text": "help"}),
        ("note", {"target": "", "text": "note"}),
        ("retry", {"entry_id": "1"}),
        ("draft", {"action": "note", "target": "", "text": "x"}),
    ]:
        r = client.post(
            f"/owner/queue/actions/{route}",
            data=data,
            headers={**_basic(), "Origin": CROSS_ORIGIN},
        )
        assert r.status_code == 403, route


def test_rate_limit_trips_on_writeback_route(client):
    for i in range(owner.RATE_LIMIT_MAX_REQUESTS):
        r = client.post(
            "/owner/queue/actions/note",
            data={"target": "", "text": f"note {i}"},
            headers=_headers(),
        )
        assert r.status_code == 200, f"request {i + 1}: {r.status_code}"
    tripped = client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "over"},
        headers=_headers(),
    )
    assert tripped.status_code == 429
    assert "Retry-After" in tripped.headers


# --------------------------------------------------------------------------
# no token → stored + honestly queued (never a fake commit)
# --------------------------------------------------------------------------
def test_note_without_token_is_stored_and_queued(client):
    r = client.post(
        "/owner/queue/actions/note",
        data={"target": "the arcade page", "text": "idea: add sound toggle"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "queued" in r.text
    assert "write token not available" in r.text
    entries = writeback.list_entries()
    assert len(entries) == 1
    e = entries[0]
    assert e["status"] == "queued"
    assert e["commit_sha"] == ""
    assert e["action"] == "note"
    assert e["text"] == "idea: add sound toggle"
    # the audit listing renders it, with the ephemeral-disk caveat visible
    page = client.get("/owner/queue", headers=_basic())
    assert page.status_code == 200
    assert "the arcade page" in page.text
    assert "ephemeral" in page.text


# --------------------------------------------------------------------------
# token present + mocked PUT returning a SHA → committed, verified, linked
# --------------------------------------------------------------------------
def test_assist_commits_a_numbered_inbox_order(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    calls = _fake_api(monkeypatch)
    r = client.post(
        "/owner/queue/actions/assist",
        data={"target": "botsite payouts", "text": "please wire PayPal"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert COMMIT_SHA[:8] in r.text
    e = writeback.list_entries()[0]
    assert e["status"] == "committed"
    assert e["commit_sha"] == COMMIT_SHA
    assert e["path"] == writeback.INBOX_PATH
    assert e["commit_url"].endswith(COMMIT_SHA)
    # the PUT appended a new ORDER numbered after the file's max (019 → 020)
    method, path, body, token = calls[-1]
    assert method == "PUT" and writeback.INBOX_PATH in path
    assert token == "write-token"
    new_text = base64.b64decode(body["content"]).decode()
    assert new_text.startswith(FAKE_INBOX.rstrip("\n"))  # append-only
    assert "## ORDER 020 ·" in new_text
    assert "BEGIN ORDER TEXT\nplease wire PayPal\nEND ORDER TEXT" in new_text
    assert "owner via launch console" in new_text
    assert body["branch"] == "main"
    assert body["sha"] == "blobsha123"


def test_complete_appends_to_owner_notes(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    calls = _fake_api(monkeypatch, read_text="# Owner notes\n\nold entry\n")
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "Mint the PAT", "text": "done just now"},
        headers=_headers(),
    )
    assert r.status_code == 200
    e = writeback.list_entries()[0]
    assert e["status"] == "committed"
    assert e["path"] == writeback.NOTES_PATH
    _, path, body, _ = calls[-1]
    assert writeback.NOTES_PATH in path
    new_text = base64.b64decode(body["content"]).decode()
    assert "owner marked COMPLETE" in new_text
    assert "target: Mint the PAT" in new_text
    assert "completion assertion" in new_text


def test_notes_log_created_with_header_when_absent(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    calls = _fake_api(monkeypatch, read_status=404)
    r = client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "first ever note"},
        headers=_headers(),
    )
    assert r.status_code == 200
    _, _, body, _ = calls[-1]
    assert "sha" not in body  # create, not update
    new_text = base64.b64decode(body["content"]).decode()
    assert new_text.startswith("# Owner notes")
    assert "first ever note" in new_text


# --------------------------------------------------------------------------
# failure paths NEVER fake a commit
# --------------------------------------------------------------------------
def test_put_403_stays_queued_with_exact_error(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "read-only-token")
    _fake_api(monkeypatch, put_status=403)
    r = client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "will not land"},
        headers=_headers(),
    )
    assert r.status_code == 200
    e = writeback.list_entries()[0]
    assert e["status"] == "queued"
    assert e["commit_sha"] == ""
    assert "HTTP 403" in e["error"]
    assert "contents:write" in e["error"]
    assert COMMIT_SHA[:8] not in r.text  # no SHA link anywhere — not faked


def test_put_success_without_sha_is_not_claimed(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")

    async def fake(method, path, json_body=None, token=""):
        if method == "GET":
            return {"ok": True, "status": 200,
                    "data": {"content": base64.b64encode(b"x").decode(),
                             "sha": "s"}, "error": ""}
        return {"ok": True, "status": 200, "data": {}, "error": ""}

    monkeypatch.setattr(github, "api_request", fake)
    client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "n"},
        headers=_headers(),
    )
    e = writeback.list_entries()[0]
    assert e["status"] == "queued"
    assert e["commit_sha"] == ""
    assert "NO commit SHA" in e["error"]


def test_retry_commits_after_token_arrives(client, monkeypatch):
    # 1) no token → queued
    client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "flush me later"},
        headers=_headers(),
    )
    e = writeback.list_entries()[0]
    assert e["status"] == "queued"
    # 2) token pasted (env read per request — no restart) + working API
    monkeypatch.setenv(writeback.ENV_TOKEN, "fresh-write-token")
    _fake_api(monkeypatch, read_text="# Owner notes\n")
    r = client.post(
        "/owner/queue/actions/retry",
        data={"entry_id": str(e["id"])},
        headers=_headers(),
    )
    assert r.status_code == 200
    e2 = writeback.get_entry(e["id"])
    assert e2["status"] == "committed"
    assert e2["commit_sha"] == COMMIT_SHA
    assert COMMIT_SHA[:8] in r.text


# --------------------------------------------------------------------------
# input validation — hard caps, nothing stored on rejection
# --------------------------------------------------------------------------
def test_empty_text_rejected_and_not_stored(client):
    r = client.post(
        "/owner/queue/actions/note",
        data={"target": "", "text": "   "},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "rejected" in r.text
    assert writeback.list_entries() == []


def test_over_cap_text_rejected(client):
    r = client.post(
        "/owner/queue/actions/assist",
        data={"target": "", "text": "x" * (writeback.TEXT_MAX_CHARS + 1)},
        headers=_headers(),
    )
    assert "too long" in r.text
    assert writeback.list_entries() == []


def test_complete_requires_target(client):
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "  ", "text": "done"},
        headers=_headers(),
    )
    assert "rejected" in r.text
    assert writeback.list_entries() == []


# --------------------------------------------------------------------------
# AI drafting assist — mocked client; never stores; honest without the key
# --------------------------------------------------------------------------
def test_draft_with_mocked_model_prefills_form_only(client, monkeypatch):
    monkeypatch.setenv(owner_assist.ENV_API_KEY, "test-key")
    seen: dict = {}

    def fake_post(payload, headers):
        seen["payload"] = payload
        seen["auth"] = headers.get("x-api-key")
        return httpx.Response(200, json={"content": [
            {"type": "text",
             "text": "WHAT: wire PayPal payouts\nWHERE: botsite"},
        ]})

    monkeypatch.setattr(owner_assist, "_http_post", fake_post)
    r = client.post(
        "/owner/queue/actions/draft",
        data={"action": "assist", "target": "", "text": "paypal thing"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "WHAT: wire PayPal payouts" in r.text
    assert "draft ready below" in r.text
    # the AI NEVER writes back — nothing stored, nothing committed
    assert writeback.list_entries() == []
    # rough text went in as tagged untrusted data; key only in the header
    body = json.dumps(seen["payload"])
    assert "<owner_rough_text>" in body
    assert "untrusted" in seen["payload"]["system"].lower()
    assert seen["auth"] == "test-key"
    assert "test-key" not in r.text


def test_draft_degrades_honestly_without_key(client):
    r = client.post(
        "/owner/queue/actions/draft",
        data={"action": "note", "target": "", "text": "rough"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "AI draft unavailable" in r.text
    assert owner_assist.ENV_API_KEY in r.text
    assert writeback.list_entries() == []


def test_draft_rejects_unknown_action(client):
    r = client.post(
        "/owner/queue/actions/draft",
        data={"action": "hack", "target": "", "text": "x"},
        headers=_headers(),
    )
    assert "unknown action" in r.text


def test_console_page_shows_capability_state(client):
    page = client.get("/owner/queue", headers=_basic())
    assert page.status_code == 200
    assert "GITHUB_TOKEN not set" in page.text
    assert "AI drafting off" in page.text
    assert "owner writeback" in page.text
