"""Durable ask IDs on the owner-action queue (C15).

The gated writeback console (`/owner/queue`) used to target an ask by its raw
HEADLINE TEXT — brittle to a rewording or a normalize-alike collision. C15 gives
each ask a durable, content-derived id (``owner_queue.ask_uid``) that is:

- STABLE across a reorder of the ledger (same ask → same id regardless of
  position) — the core regression this fixes;
- distinct for distinct asks;
- keyed on the ledger ``ID: ASK-NNNN`` when present, so it survives even a
  rewording of the ask's WHAT prose (where headline matching would break).

The writeback POST routes resolve the target ask BY that id and reject an
unknown/stale id safely — never acting on the wrong ask. These tests pin the
derivation, the resolution, the wrong-ask regression, the fail-closed safety,
that the C14 auto-clear still works with the id present, and that the CSRF /
same-origin floor is intact on the resolving route. Offline throughout
(TestClient, per-test SQLite, every GitHub seam faked), mirroring
tests/test_owner_queue_preflight.py.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import (  # noqa: E402
    askverify,
    config,
    github,
    owner,
    owner_assist,
    owner_queue,
    writeback,
)
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"
CROSS_ORIGIN = "https://evil.example"
COMMIT_SHA = "deadbeefcafe0123456789abcdef0123456789ab"


# --------------------------------------------------------------------------
# unit: the durable id derivation + lookup
# --------------------------------------------------------------------------
def _ask(what: str, *, ask_id: str | None = None, age: float = 1.0) -> dict:
    return {
        "what": what,
        "text": "",
        "ask_id": ask_id,
        "fields": {},
        "sources": [{"label": "lane", "kind": "lane", "age_hours": age,
                     "age_human": "1h", "url": "https://example.test/src"}],
    }


def test_uid_is_stable_across_a_reorder_of_the_ledger():
    """The SAME ask yields the SAME id regardless of its position — the id is
    derived from content, never from the index in the list."""
    a, b, c = _ask("Alpha ask"), _ask("Beta ask"), _ask("Gamma ask")
    forward = [owner_queue.ask_uid(x) for x in (a, b, c)]
    reversed_ = [owner_queue.ask_uid(x) for x in (c, b, a)]
    # each ask keeps its id wherever it sits
    assert owner_queue.ask_uid(a) == forward[0]
    assert forward == list(reversed(reversed_))
    # and a re-derivation is deterministic
    assert owner_queue.ask_uid(a) == owner_queue.ask_uid(dict(a))


def test_distinct_asks_get_distinct_ids():
    ids = {owner_queue.ask_uid(_ask(w))
           for w in ("one", "two", "three", "four")}
    assert len(ids) == 4
    # shape: an opaque, non-positional token
    assert all(i.startswith("ask-") and len(i) == len("ask-") + 12 for i in ids)


def test_uid_prefers_ask_id_and_survives_a_what_rewording():
    """An ask carrying a ledger ``ID: ASK-NNNN`` keys on that id, so a rewording
    of its WHAT prose keeps the SAME durable id — headline matching would not."""
    before = _ask("Mint the contents:write PAT", ask_id="ASK-0007")
    reworded = _ask("Please create the write-scoped token", ask_id="ASK-0007")
    assert owner_queue.ask_uid(before) == owner_queue.ask_uid(reworded)
    # two different ask_ids never collide
    assert owner_queue.ask_uid(before) != owner_queue.ask_uid(
        _ask("Mint the contents:write PAT", ask_id="ASK-0008")
    )


def test_resolve_uid_finds_the_right_ask_after_a_reorder():
    """resolve_uid points at the intended ask no matter where it sits — the
    core wrong-ask regression, at the unit level."""
    a, b, c = _ask("Alpha"), _ask("Beta"), _ask("Gamma")
    uid_b = owner_queue.ask_uid(b)
    assert owner_queue.resolve_uid([a, b, c], uid_b) is b
    assert owner_queue.resolve_uid([c, b, a], uid_b) is b  # reordered
    assert owner_queue.resolve_uid([a, c], uid_b) is None  # b removed
    assert owner_queue.resolve_uid([a, b, c], "ask-deadbeef0000") is None
    assert owner_queue.resolve_uid([a, b, c], "") is None


def test_contentless_item_has_empty_uid():
    assert owner_queue.ask_uid({"what": "", "text": "", "fields": {},
                                "sources": []}) == ""


# --------------------------------------------------------------------------
# route-level: the writeback console resolves BY the durable id
# --------------------------------------------------------------------------
def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _headers() -> dict:
    return {**_basic(), "Origin": SAME_ORIGIN}


def _offline(url=""):
    return {"ok": False, "status": 0, "data": None, "error": "offline test",
            "fetched_at": "", "cached": False, "url": url}


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
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    monkeypatch.delenv(owner_assist.ENV_API_KEY, raising=False)

    async def fake_get(url, refresh=False, raw=False):
        return _offline(url)

    monkeypatch.setattr(github, "_get", fake_get)
    with TestClient(app) as c:
        yield c


def _fake_contents_api(monkeypatch):
    """Recording GitHub fake for the confirm round-trips — the branch+PR flow
    (base ref → create branch → contents GET → PUT → open PR)."""
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
            return {"ok": True, "status": 200,
                    "data": {"content": base64.b64encode(
                        b"# Owner notes\n\nold entry\n").decode(),
                        "sha": "blobsha123"}, "error": ""}
        if method == "PUT" and "/contents/" in path:
            return {"ok": True, "status": 200,
                    "data": {"commit": {
                        "sha": COMMIT_SHA,
                        "html_url": ("https://github.com/menno420/websites/commit/"
                                     + COMMIT_SHA)}}, "error": ""}
        if method == "POST" and path.endswith("/pulls"):
            return {"ok": True, "status": 201,
                    "data": {"number": 4020,
                             "html_url": "https://github.com/menno420/websites/pull/4020"},
                    "error": ""}
        raise AssertionError(f"unexpected GitHub call {method} {path}")

    monkeypatch.setattr(github, "api_request", fake)
    return calls


def test_overview_exposes_uid_on_every_ask(client, monkeypatch):
    """The public overview() attaches a durable uid to each item (so
    /queue.json carries it and the gated forms can render it)."""
    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.startswith("control/status") and repo == "websites":
            return {"ok": True, "status": 200, "error": "", "data": (
                "# s\nupdated: 2026-07-10T22:00Z\nhealth: green\n"
                "⚑ needs-owner: one.\n  ⚑ OWNER-ACTION\n  ID: ASK-0007\n"
                "  WHAT: Mint the PAT.\n  WHERE: railway.\n  HOW: paste.\n")}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    monkeypatch.setattr(github, "fetch_file", fake_fetch)
    r = client.get("/queue.json")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and all(it["uid"].startswith("ask-") for it in items)
    # the ASK-0007 ask's uid is exactly the ask_id-derived one
    minted = next(it for it in items if it.get("ask_id") == "ASK-0007")
    assert minted["uid"] == owner_queue.ask_uid({"ask_id": "ASK-0007"})


def test_complete_confirm_resolves_correct_ask_after_reorder(client, monkeypatch):
    """The regression: the confirm carries the previewed ask's durable uid, so
    even after the ledger REORDERS between preview and confirm the fail-closed
    re-find still hits the intended ask — the completion stores against it."""
    target = _ask("Publish the lumen-drift release", ask_id="ASK-0010")
    other = _ask("Some unrelated ask", ask_id="ASK-0011")
    uid = owner_queue.ask_uid(target)
    # confirm-time overview is REORDERED (target now last, other first)
    _patch_overview(monkeypatch, _overview_data([other, target]))
    _fake_contents_api(monkeypatch)
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "Publish the lumen-drift release", "text": "done",
              "uid": uid},
        headers=_headers(),
    )
    assert r.status_code == 200
    # the ask WAS found by uid (not reported gone) → the completion committed
    e = writeback.list_entries()[0]
    assert e["status"] == "committed"
    assert e["action"] == "complete"
    assert "no longer in the readable sources" not in r.text


def test_complete_confirm_unknown_uid_fails_closed(client, monkeypatch):
    """A stale/unknown durable id with fully readable sources is rejected
    safely — nothing stored, nothing committed, no wrong-ask mutation."""
    _patch_overview(monkeypatch, _overview_data([_ask("Only ask", ask_id="ASK-1")]))
    # api_request left UNSET so any commit attempt would surface; assert none
    r = client.post(
        "/owner/queue/actions/complete",
        data={"target": "Only ask", "text": "did it",
              "uid": "ask-deadbeef0000"},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert "nothing stored, nothing committed" in r.text
    assert "no longer in the readable sources" in r.text
    assert 'action="/owner/queue/actions/complete"' not in r.text
    assert writeback.list_entries() == []


def test_complete_preview_confirm_form_carries_the_uid(client, monkeypatch):
    """The preview's confirm form threads the durable uid through to the
    firing route (so the confirm resolves the same ask)."""
    target = _ask("Publish the lumen-drift release", ask_id="ASK-0010")
    uid = owner_queue.ask_uid(target)
    _patch_overview(monkeypatch, _overview_data([target]))
    r = client.post(
        "/owner/queue/actions/preview",
        data={"action": "complete", "target": "Publish the lumen-drift release",
              "text": "done", "uid": uid},
        headers=_headers(),
    )
    assert r.status_code == 200
    assert f'name="uid" value="{uid}"' in r.text
    assert 'action="/owner/queue/actions/complete"' in r.text


def test_gated_queue_page_renders_uid_in_the_per_ask_forms(client, monkeypatch):
    """The live owner surface: each per-ask form carries the ask's durable uid
    as its hidden identifier."""
    target = _ask("Mint the PAT", ask_id="ASK-0007")
    _patch_overview(monkeypatch, _overview_data([target]))
    page = client.get("/owner/queue", headers=_basic())
    assert page.status_code == 200
    uid = owner_queue.ask_uid(target)
    assert f'name="uid" value="{uid}"' in page.text


def test_csrf_floor_intact_on_the_uid_resolving_route(client):
    """C15 must not weaken the CSRF / same-origin floor on the complete route
    that now resolves by uid: a cross-origin POST is still 403, an
    unauthenticated one still 401."""
    body = {"target": "x", "text": "y", "uid": "ask-deadbeef0000"}
    assert client.post(
        "/owner/queue/actions/complete", data=body,
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    ).status_code == 403
    assert client.post(
        "/owner/queue/actions/complete", data=body,
        headers={"Origin": SAME_ORIGIN},
    ).status_code == 401
    assert writeback.list_entries() == []


# --------------------------------------------------------------------------
# C14 auto-clear still works with the durable id present on the items
# --------------------------------------------------------------------------
def test_c14_auto_clear_survives_uid_on_items():
    """annotate + split_self_cleaned operate on the same ask objects; the
    added uid key must not disturb the partition."""
    import asyncio

    done = _ask("Publish the lumen-drift release", ask_id="ASK-0010")
    done["uid"] = owner_queue.ask_uid(done)
    still = _ask("Mint the PAT", ask_id="ASK-0007")
    still["uid"] = owner_queue.ask_uid(still)

    async def fake_lumen(refresh=False):
        return {"verdict": askverify.DONE, "label": "done", "css": "ok",
                "detail": "", "probe": "lumen-drift-release", "url": ""}

    async def fake_pat(refresh=False):
        return {"verdict": askverify.STILL_OPEN, "label": "open", "css": "warn",
                "detail": "", "probe": "order-020-pat", "url": ""}

    reg = {e["id"]: e for e in askverify.REGISTRY}
    orig_lumen = reg["lumen-drift-release"]["probe"]
    orig_pat = reg["order-020-pat"]["probe"]
    reg["lumen-drift-release"]["probe"] = fake_lumen
    reg["order-020-pat"]["probe"] = fake_pat
    try:
        items = [done, still]
        rollup = asyncio.run(askverify.annotate(items))
        active, cleared = askverify.split_self_cleaned(items)
    finally:
        reg["lumen-drift-release"]["probe"] = orig_lumen
        reg["order-020-pat"]["probe"] = orig_pat

    assert rollup["auto_cleared"] == 1
    assert [it["what"] for it in cleared] == ["Publish the lumen-drift release"]
    assert [it["what"] for it in active] == ["Mint the PAT"]
    # the uid rode through untouched on both partitions
    assert cleared[0]["uid"] == owner_queue.ask_uid(done)
    assert active[0]["uid"] == owner_queue.ask_uid(still)
