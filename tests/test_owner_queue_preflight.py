"""Queue writeback preflight tests (2026-07-15, PR B of the launch-console
pair).

Contract under test:

- POST /owner/queue/actions/preview (behind require_owner_action, like
  every queue POST) is STATELESS: no SQLite row, no commit, no
  github.api_post / api_request — pinned against recorders and the store,
  never inferred. It renders the EXACT composed block (writeback's own
  render_note_block / render_assist_block), the target file + branch, the
  write-token state, for assist the PROVISIONAL ORDER number with the
  honest renumbered-at-commit-time caveat, and for complete the ask's
  askverify verdict chip.
- The preview's confirm re-POSTs the SAME action/target/text verbatim to
  the existing UNCHANGED firing routes; cancel returns to /owner/queue.
- The one firing-route change: the complete confirm re-finds the targeted
  ask by headline and FAILS CLOSED (honest banner, nothing stored, nothing
  committed) ONLY when every source read successfully and the ask is gone.
  Unreadable sources never fake a "gone" — the owner's assertion proceeds
  exactly as the 17 ORDER-020 tests pin it.
- Retry (entry_id-pinned, content already stored + shown) and draft
  (stores nothing) stay preview-exempt; the queue page documents both.

Offline throughout, mirroring tests/test_owner_writeback.py: TestClient,
per-test SQLite, every GitHub seam faked; api_post/api_request raise if a
preview ever reaches them.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, owner, owner_assist, owner_queue, writeback  # noqa: E402
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
LUMEN_ASK = "Publish the lumen-drift v1.3 release on gba-homebrew"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _headers() -> dict:
    return {**_basic(), "Origin": SAME_ORIGIN}


def _offline(url=""):
    return {"ok": False, "status": 0, "data": None, "error": "offline test",
            "fetched_at": "", "cached": False, "url": url}


def _ask(headline: str) -> dict:
    return {
        "what": headline,
        "text": "",
        "fields": {},
        "sources": [{"label": "lane", "kind": "lane", "age_human": "1h",
                     "url": "https://example.test/src"}],
    }


def _overview_data(items, unreadable=(), fm_state="ok") -> dict:
    return {
        "items": items,
        "lane_notes": [],
        "fleet_manager": {"state": fm_state, "token_set": False, "url": "",
                          "items": [], "preamble": "", "body_html": "",
                          "reason": ""},
        "field_order": [],
        "summary": {"total": len(items), "deduped": 0,
                    "lanes_with_asks": 0, "lanes_total": 0},
        "unreadable_lanes": list(unreadable),
        "lane_source": {"label": "", "url": ""},
    }


def _patch_overview(monkeypatch, data: dict) -> None:
    async def fake(refresh=False):
        return data

    monkeypatch.setattr(owner_queue, "overview", fake)


@pytest.fixture(autouse=True)
def _reset_state():
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()
    yield
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Authed-ready, fully offline client. api_post/api_request RAISE by
    default — any preview reaching a write choke point fails the test."""
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    monkeypatch.delenv(owner_assist.ENV_API_KEY, raising=False)

    async def fake_get(url, refresh=False, raw=False):
        return _offline(url)

    monkeypatch.setattr(github, "_get", fake_get)

    async def fail_api_post(path, json_body=None):
        raise AssertionError(f"github.api_post({path}) reached in a preview")

    monkeypatch.setattr(github, "api_post", fail_api_post)

    async def fail_api_request(method, path, json_body=None, token=""):
        raise AssertionError(
            f"github.api_request({method} {path}) reached in a preview"
        )

    monkeypatch.setattr(github, "api_request", fail_api_request)
    with TestClient(app) as c:
        yield c


def _fake_contents_api(monkeypatch):
    """Recording GitHub fake for the CONFIRM round-trips — the branch+PR flow
    (the one writeback path): base ref → create branch → contents GET → PUT →
    open PR."""
    calls: list[tuple] = []

    async def fake(method, path, json_body=None, token=""):
        calls.append((method, path, json_body, token))
        if method == "GET" and "/git/ref/heads/" in path:
            return {"ok": True, "status": 200,
                    "data": {"object": {"sha": "ba5e" + "0" * 36}}, "error": ""}
        if method == "POST" and path.endswith("/git/refs"):
            return {"ok": True, "status": 201,
                    "data": {"ref": (json_body or {}).get("ref")}, "error": ""}
        if method == "GET" and "/contents/" in path:
            return {
                "ok": True, "status": 200,
                "data": {"content": base64.b64encode(
                    b"# Owner notes\n\nold entry\n").decode(),
                    "sha": "blobsha123"},
                "error": "",
            }
        if method == "PUT" and "/contents/" in path:
            return {
                "ok": True, "status": 200,
                "data": {"commit": {
                    "sha": COMMIT_SHA,
                    "html_url": ("https://github.com/menno420/websites/commit/"
                                 + COMMIT_SHA),
                }},
                "error": "",
            }
        if method == "POST" and path.endswith("/pulls"):
            return {"ok": True, "status": 201,
                    "data": {"number": 4020,
                             "html_url": "https://github.com/menno420/websites/pull/4020"},
                    "error": ""}
        raise AssertionError(f"unexpected GitHub call {method} {path}")

    monkeypatch.setattr(github, "api_request", fake)
    return calls


# --------------------------------------------------------------------------
# The preview is stateless — zero writes, zero rows, block verbatim
# --------------------------------------------------------------------------
def test_note_preview_renders_block_and_stores_nothing(client):
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "note", "target": "the arcade page",
              "text": "idea: add sound toggle"},
        headers=_headers(),
    )
    assert r.status_code == 200
    # the EXACT composed block (writeback's own renderer), verbatim parts
    assert "owner note/correction/idea" in r.text
    assert "target: the arcade page" in r.text
    assert "idea: add sound toggle" in r.text
    # target file + the branch+PR landing + token state (unset → queued warning)
    assert "control/owner-notes.md" in r.text
    assert "auto-PR into main" in r.text
    assert "GITHUB_TOKEN not set" in r.text
    assert "stores the entry locally" in r.text
    # confirm re-POSTs the SAME payload to the UNCHANGED firing route
    assert 'action="/owner/queue/actions/note"' in r.text
    assert 'name="target" value="the arcade page"' in r.text
    assert 'name="text" value="idea: add sound toggle"' in r.text
    # cancel returns to the queue, not the board
    assert 'href="/owner/queue"' in r.text
    # STATELESS: nothing stored (api_post/api_request would have raised)
    assert writeback.list_entries() == []


def test_preview_zero_writes_even_with_token_armed(client, monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "note", "target": "", "text": "armed but previewing"},
        headers=_headers(),
    )
    assert r.status_code == 200  # api_post/api_request fakes raise if touched
    assert "GITHUB_TOKEN present" in r.text
    assert writeback.list_entries() == []


def test_assist_preview_shows_provisional_order_number(client, monkeypatch):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == "websites" and path == writeback.INBOX_PATH
        return {"ok": True, "status": 200, "data": FAKE_INBOX, "error": ""}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "assist", "target": "botsite payouts",
              "text": "please wire PayPal"},
        headers=_headers(),
    )
    assert r.status_code == 200
    # provisional number after the file's max (019 → 020), never pinned
    assert "ORDER 020" in r.text
    assert "provisional" in r.text
    assert "commit time" in r.text  # the honest renumbering caveat
    # the exact composed block, inbox grammar included
    assert "## ORDER 020 ·" in r.text
    assert "BEGIN ORDER TEXT" in r.text
    assert "please wire PayPal" in r.text
    assert "control/inbox.md" in r.text
    # the confirm carries NO order number — only action/target/text
    assert 'name="order"' not in r.text
    assert 'action="/owner/queue/actions/assist"' in r.text
    assert writeback.list_entries() == []


def test_assist_preview_inbox_unreadable_stays_honest(client):
    # default offline _get → raw read and contents fallback both fail
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "assist", "target": "", "text": "need help"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "could not be read" in r.text
    assert "placeholder" in r.text  # the block's number is flagged as such
    assert "read at commit time" in r.text
    assert 'action="/owner/queue/actions/assist"' in r.text  # still confirmable
    assert writeback.list_entries() == []


# --------------------------------------------------------------------------
# Complete previews — the askverify verdict chip
# --------------------------------------------------------------------------
def test_complete_preview_shows_done_detected_chip(client, monkeypatch):
    _patch_overview(monkeypatch, _overview_data([_ask(LUMEN_ASK)]))

    async def fake_get(url, refresh=False, raw=False):
        if "releases/tags/lumen-drift-v1.3" in url:
            return {"ok": True, "status": 200,
                    "data": {"html_url": "https://github.example/rel"},
                    "error": "", "fetched_at": "", "cached": False,
                    "url": url}
        return _offline(url)

    monkeypatch.setattr(github, "_get", fake_get)
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "complete", "target": LUMEN_ASK, "text": "done"},
        headers=_headers(),
    )
    assert r.status_code == 200
    # the probe already says done — the preview says so
    assert "done-detected — ledger update pending" in r.text
    assert 'action="/owner/queue/actions/complete"' in r.text
    assert writeback.list_entries() == []


def test_complete_preview_probe_failure_is_honest_unknown(client, monkeypatch):
    _patch_overview(monkeypatch, _overview_data([_ask(LUMEN_ASK)]))
    # default offline _get → the probe ran and could not tell
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "complete", "target": LUMEN_ASK, "text": ""},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "verify: unknown" in r.text
    assert "done-detected" not in r.text
    assert writeback.list_entries() == []


def test_complete_preview_ask_gone_all_readable_no_confirm(client, monkeypatch):
    _patch_overview(monkeypatch, _overview_data([_ask("some other ask")]))
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "complete", "target": "vanished ask", "text": ""},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "nothing to confirm" in r.text
    assert "every source read successfully" in r.text
    assert 'action="/owner/queue/actions/complete"' not in r.text
    assert writeback.list_entries() == []


def test_complete_preview_sources_unreadable_still_confirms(client):
    # real overview, offline — sources unreadable, absence NOT proven
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "complete", "target": "Mint the PAT", "text": ""},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "sources partially unreadable" in r.text
    assert "absence is not proven" in r.text
    assert 'action="/owner/queue/actions/complete"' in r.text
    assert writeback.list_entries() == []


# --------------------------------------------------------------------------
# Confirm round-trip — the verbatim payload fires the unchanged route
# --------------------------------------------------------------------------
def test_confirm_roundtrip_fires_the_previewed_payload(client, monkeypatch):
    payload = {"action": "note", "target": "the arcade page",
               "text": "idea: add sound toggle"}
    preview = client.post(
        "/owner/queue/actions/preview", data=payload, headers=_headers()
    )
    assert preview.status_code == 200
    assert writeback.list_entries() == []
    # fire the confirm exactly as the form would: same fields, verbatim
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    calls = _fake_contents_api(monkeypatch)
    r = client.post(
        "/owner/queue/actions/note", data=payload, headers=_headers()
    )
    assert r.status_code == 200
    e = writeback.list_entries()[0]
    assert e["status"] == "committed"
    assert e["commit_sha"] == COMMIT_SHA
    # the committed block is the block the preview rendered — find the contents
    # PUT (the last call is now the POST that opens the PR)
    puts = [c for c in calls if c[0] == "PUT" and "/contents/" in c[1]]
    _method, path, body, _tok = puts[-1]
    assert writeback.NOTES_PATH in path
    assert body["branch"].startswith("claude/owner-writeback-")
    landed = base64.b64decode(body["content"]).decode()
    assert "owner note/correction/idea" in landed
    assert "target: the arcade page" in landed
    assert "idea: add sound toggle" in landed
    assert landed_matches_preview(preview.text, landed)


def landed_matches_preview(preview_html: str, landed: str) -> bool:
    """Every non-volatile line of the landed block appeared in the preview
    (the stamp and audit-entry id are commit-time values by design)."""
    block = landed.split("## ")[-1]
    for line in block.splitlines():
        line = line.strip()
        if not line or "console audit entry" in line or line.startswith("## "):
            continue
        if line not in preview_html:
            return False
    return True


def test_complete_confirm_ask_vanished_fails_closed(client, monkeypatch):
    _patch_overview(monkeypatch, _overview_data([_ask("some other ask")]))
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    # api_request left at the RAISING default: a commit attempt would fail
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "vanished ask", "text": "did it"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "nothing stored, nothing committed" in r.text
    assert "no longer in the readable sources" in r.text
    # fail-closed re-preview: no confirm form re-inviting the same fire
    assert 'action="/owner/queue/actions/complete"' not in r.text
    assert writeback.list_entries() == []


def test_complete_confirm_sources_unreadable_proceeds(client):
    """Unreadable sources never fake a 'gone' — the owner's completion
    assertion stores exactly as the ORDER-020 suite pins it."""
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "Mint the PAT", "text": "done just now"},
        headers=_headers(),
    )
    assert r.status_code == 200
    e = writeback.list_entries()[0]
    assert e["status"] == "queued"  # no token → stored + honestly queued
    assert e["action"] == "complete"


def test_complete_confirm_ask_present_proceeds(client, monkeypatch):
    _patch_overview(monkeypatch, _overview_data([_ask("Mint the PAT")]))
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "Mint the PAT", "text": "done"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert writeback.list_entries()[0]["status"] == "queued"


# --------------------------------------------------------------------------
# Gate floor + input honesty on the preview POST
# --------------------------------------------------------------------------
def test_preview_requires_auth_and_same_origin(client):
    data = {"action": "note", "target": "", "text": "x"}
    assert client.post(
        "/owner/queue/actions/preview", data=data,
        headers={"Origin": SAME_ORIGIN},
    ).status_code == 401
    assert client.post(
        "/owner/queue/actions/preview", data=data,
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    ).status_code == 403
    assert writeback.list_entries() == []


def test_preview_unknown_action_honest(client):
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "hack", "target": "", "text": "x"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "unknown action" in r.text
    assert writeback.list_entries() == []


def test_preview_would_be_rejected_shows_reason_no_confirm(client):
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "note", "target": "", "text": "   "},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "would be rejected" in r.text
    assert "nothing to confirm" in r.text
    assert 'action="/owner/queue/actions/note"' not in r.text
    assert writeback.list_entries() == []


# --------------------------------------------------------------------------
# Wire-in — queue forms route through the preview; retry/draft exempt
# --------------------------------------------------------------------------
def test_queue_forms_route_through_preview_retry_draft_exempt(
    client, monkeypatch
):
    _patch_overview(monkeypatch, _overview_data([_ask("Mint the PAT")]))
    writeback.store_entry("note", "", "a queued row")  # renders a retry form
    page = client.get("/owner/queue", headers=_basic())
    assert page.status_code == 200
    # 2 general + 3 per-item forms all POST the preview first
    assert page.text.count('action="/owner/queue/actions/preview"') == 5
    # no form fires a writeback route directly anymore
    for route in ("complete", "assist", "note"):
        assert f'method="post" action="/owner/queue/actions/{route}"' \
            not in page.text
    # the two documented exemptions stay one-step, unchanged
    assert 'action="/owner/queue/actions/retry"' in page.text
    assert 'formaction="/owner/queue/actions/draft"' in page.text
    assert "one-step exemptions" in page.text
