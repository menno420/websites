"""Launch preflight verdicts (app/askverify.py) — read-only auto-verification
of the open ⚑ OWNER-ACTION asks.

Fully offline (the arcade_probe precedent: every network seam is
``github._get`` / ``railway.live_overview``, monkeypatched here — CI never
touches the network). tests/conftest.py pins GITHUB_TOKEN/RAILWAY_TOKEN to
the UNSET rung suite-wide, so the no-token honest-unknown tests hold by
default and token-armed tests opt in explicitly.

Coverage:

* matcher stability against the REAL committed docs/owner/OWNER-ACTIONS.md
  Open section (all 9 asks match, each a distinct registry entry);
* every live probe's full verdict ladder (done-detected / still-open /
  unknown), including the no-token rungs and the never-writes guarantee of
  the ORDER-020 PAT check;
* annotate(): unmatched-ask honesty, claim-once ambiguity, explicit
  not-machine-checkable registrations, fail-soft probe exceptions, rollup
  counts;
* wiring: public /queue never calls askverify and carries no chip markup
  (byte-identity pin), /owner/queue cards + /owner/briefing asks carry
  chips, the /owner board carries the rollup chip with its honest-unknown
  state.
"""

from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import (  # noqa: E402
    askverify,
    briefing,
    config,
    github,
    owner_queue,
    railway,
    writeback,
)
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
LEDGER_PATH = Path(__file__).resolve().parents[1] / "docs/owner/OWNER-ACTIONS.md"

BOTSITE_OWNER_URL = askverify._botsite_base() + "/testing/owner"


def _basic(pw: str = OWNER_PW, user: str = "owner") -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _envelope(url, *, ok=False, status=0, data=None, error="offline test"):
    return {
        "ok": ok, "status": status, "data": data,
        "error": error, "fetched_at": "", "cached": False, "url": url,
    }


def _install_get(monkeypatch, responder):
    """Monkeypatch the ONE http seam every probe rides."""
    async def fake_get(url, refresh=False, raw=False):
        return responder(url)

    monkeypatch.setattr(github, "_get", fake_get)


def _run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# Matcher stability — the REAL committed ledger is the fixture
# --------------------------------------------------------------------------- #
def _open_ledger_headlines() -> list[str]:
    text = LEDGER_PATH.read_text(encoding="utf-8")
    section, note = briefing.open_section(text)
    assert note == ""  # the ledger has its Open heading
    _pre, blocks = owner_queue.parse_owner_actions(section)
    return [b.get("what", "") for b in blocks]


def test_real_ledger_has_the_nine_open_asks():
    assert len(_open_ledger_headlines()) == 9


def test_every_real_open_ask_matches_a_distinct_registry_entry():
    headlines = _open_ledger_headlines()
    ids = []
    for h in headlines:
        entry = askverify.match(h)
        assert entry is not None, f"unmatched real ask: {h[:80]!r}"
        ids.append(entry["id"])
    assert len(set(ids)) == len(ids), f"registry entry matched twice: {ids}"


def test_real_ledger_matches_land_on_the_intended_probes():
    by_id = {askverify.match(h)["id"]: h for h in _open_ledger_headlines()}
    assert set(by_id) == {
        "q-0004", "discord-oauth", "armed-service", "botsite-database-url",
        "paypal-credentials", "botsite-gate", "order-020-pat", "bake-pat",
        "dashboard-site-password",
    }
    # Spot-check the two textually-overlapping PAT asks disambiguate.
    assert "BAKE_PAT" in by_id["bake-pat"]
    assert "BAKE_PAT" not in by_id["order-020-pat"]


def test_match_unmatched_and_empty_are_none():
    assert askverify.match("Answer the briefing fixture question.") is None
    assert askverify.match("") is None
    assert askverify.match("   ") is None


def test_match_is_case_and_whitespace_insensitive():
    entry = askverify.match("set  SITE_PASSWORD   on the BOTSITE service")
    assert entry is not None and entry["id"] == "botsite-gate"


# --------------------------------------------------------------------------- #
# Probe ladders — botsite SITE_PASSWORD gate
# --------------------------------------------------------------------------- #
def test_botsite_probe_503_is_still_open(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url, status=503))
    v = _run(askverify.probe_botsite_site_password())
    assert v["verdict"] == askverify.STILL_OPEN
    assert "503" in v["detail"]
    assert v["url"] == BOTSITE_OWNER_URL


def test_botsite_probe_401_is_done_detected_with_pending_wording(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url, status=401))
    v = _run(askverify.probe_botsite_site_password())
    assert v["verdict"] == askverify.DONE
    assert "ledger update pending" in v["label"]
    assert v["css"] == "ok"


def test_botsite_probe_other_statuses_are_unknown(monkeypatch):
    for status in (0, 200, 404, 500):
        _install_get(
            monkeypatch, lambda url, s=status: _envelope(url, status=s)
        )
        v = _run(askverify.probe_botsite_site_password())
        assert v["verdict"] == askverify.UNKNOWN, status
        assert v["detail"]  # always says why


# --------------------------------------------------------------------------- #
# Probe ladders — BAKE_PAT Actions-secret name
# --------------------------------------------------------------------------- #
def test_bake_pat_no_token_is_unknown_by_default(monkeypatch):
    # conftest pins GITHUB_TOKEN unset — the probe must not even fetch.
    def boom(url):
        raise AssertionError("no fetch may happen without a token")

    _install_get(monkeypatch, boom)
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.UNKNOWN
    assert "GITHUB_TOKEN" in v["detail"]


def test_bake_pat_present_and_absent(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")  # explicit opt-in
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"secrets": [{"name": "BAKE_PAT"}, {"name": "OTHER"}]},
    ))
    assert _run(askverify.probe_bake_pat_secret())["verdict"] == askverify.DONE
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"secrets": []},
    ))
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.STILL_OPEN


def test_bake_pat_scope_denied_is_unknown(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _install_get(monkeypatch, lambda url: _envelope(url, status=403))
    v = _run(askverify.probe_bake_pat_secret())
    assert v["verdict"] == askverify.UNKNOWN
    assert "admin scope" in v["detail"]


# --------------------------------------------------------------------------- #
# Probe ladders — ORDER-020 contents-write PAT (read-only, always)
# --------------------------------------------------------------------------- #
def test_order020_no_token_is_unknown_by_default(monkeypatch):
    def boom(url):
        raise AssertionError("no fetch may happen without a token")

    _install_get(monkeypatch, boom)
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.UNKNOWN
    assert "GITHUB_TOKEN" in v["detail"]


def test_order020_permissions_ladder(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"permissions": {"push": True, "pull": True}},
    ))
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.DONE
    assert "ledger update pending" in v["label"]
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"permissions": {"push": False, "pull": True}},
    ))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.STILL_OPEN
    )
    # No permissions object → honest unknown, never inferred.
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"name": "websites"},
    ))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.UNKNOWN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=0))
    assert (
        _run(askverify.probe_order020_write_pat())["verdict"]
        == askverify.UNKNOWN
    )


def test_order020_probe_never_attempts_a_write(monkeypatch):
    """The hard rail: the PAT check is a GET of the repo payload only —
    api_post/api_request (the write paths) must never be touched."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")

    async def no_post(*a, **k):
        raise AssertionError("askverify must never call a write path")

    monkeypatch.setattr(github, "api_post", no_post)
    monkeypatch.setattr(github, "api_request", no_post)
    seen: list[str] = []

    def responder(url):
        seen.append(url)
        return _envelope(url, ok=True, status=200, error="",
                         data={"permissions": {"push": True}})

    _install_get(monkeypatch, responder)
    v = _run(askverify.probe_order020_write_pat())
    assert v["verdict"] == askverify.DONE
    assert seen == [f"{config.GITHUB_API_BASE}/repos/menno420/websites"]


# --------------------------------------------------------------------------- #
# Probe ladders — dashboard SITE_PASSWORD deletion (Railway names-only)
# --------------------------------------------------------------------------- #
def _install_live(monkeypatch, payload):
    async def fake_live(refresh=False):
        return payload

    monkeypatch.setattr(railway, "live_overview", fake_live)


def test_dashboard_probe_no_railway_token_is_unknown_by_default(monkeypatch):
    _install_live(monkeypatch, {"state": "ok", "services": []})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.UNKNOWN
    assert "RAILWAY_TOKEN" in v["detail"]


def test_dashboard_probe_ladder_with_token(monkeypatch):
    monkeypatch.setattr(config, "RAILWAY_TOKEN", "tok")
    # still present → still-open
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard",
         "variable_names": ["PORT", "SITE_PASSWORD"], "error": ""},
    ]})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.STILL_OPEN
    # gone from a successful read → done-detected
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard", "variable_names": ["PORT"], "error": ""},
    ]})
    v = _run(askverify.probe_dashboard_site_password_gone())
    assert v["verdict"] == askverify.DONE
    # honest-unknown rungs: read failed / service absent / per-service error
    _install_live(monkeypatch, {"state": "unavailable", "reason": "boom"})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )
    _install_live(monkeypatch, {"state": "ok", "services": []})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )
    _install_live(monkeypatch, {"state": "ok", "services": [
        {"name": "dashboard", "variable_names": [], "error": "HTTP 500"},
    ]})
    assert (
        _run(askverify.probe_dashboard_site_password_gone())["verdict"]
        == askverify.UNKNOWN
    )


# --------------------------------------------------------------------------- #
# Probe ladders — arcade blockers (public reads)
# --------------------------------------------------------------------------- #
def test_lumen_drift_release_ladder(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="",
        data={"tag_name": "lumen-drift-v1.3", "html_url": "https://x/rel"},
    ))
    v = _run(askverify.probe_lumen_drift_release())
    assert v["verdict"] == askverify.DONE
    assert v["url"] == "https://x/rel"
    _install_get(monkeypatch, lambda url: _envelope(url, status=404))
    assert (
        _run(askverify.probe_lumen_drift_release())["verdict"]
        == askverify.STILL_OPEN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=0))
    assert (
        _run(askverify.probe_lumen_drift_release())["verdict"]
        == askverify.UNKNOWN
    )


def test_product_forge_pages_ladder(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(
        url, ok=True, status=200, error="", data={"status": "built"},
    ))
    assert (
        _run(askverify.probe_product_forge_pages())["verdict"]
        == askverify.DONE
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=404))
    assert (
        _run(askverify.probe_product_forge_pages())["verdict"]
        == askverify.STILL_OPEN
    )
    _install_get(monkeypatch, lambda url: _envelope(url, status=403))
    v = _run(askverify.probe_product_forge_pages())
    assert v["verdict"] == askverify.UNKNOWN
    assert "unreadable" in v["detail"]


# --------------------------------------------------------------------------- #
# annotate() — honesty semantics + rollup
# --------------------------------------------------------------------------- #
def test_annotate_unmatched_ask_stays_honestly_unverified(monkeypatch):
    items = [{"what": "A brand new ask nothing matches."}]
    rollup = _run(askverify.annotate(items))
    v = items[0]["verify"]
    assert v["verdict"] == askverify.NOT_CHECKABLE
    assert "no registered probe matches" in v["detail"]
    assert rollup == {
        "total": 1, "machine_verified": 0, "done": 0, "still_open": 0,
        "not_checkable": 1, "unknown": 0, "unmatched": 1,
    }


def test_annotate_not_checkable_registrations_carry_their_reason():
    items = [
        {"what": "Answer Q-0004 — decide WHERE live bot control lives."},
        {"what": "Set up PayPal Payouts for the tester program."},
    ]
    rollup = _run(askverify.annotate(items))
    assert items[0]["verify"]["verdict"] == askverify.NOT_CHECKABLE
    assert "Q-0004" in items[0]["verify"]["detail"]
    assert items[1]["verify"]["verdict"] == askverify.NOT_CHECKABLE
    assert "never be probed" in items[1]["verify"]["detail"]
    assert rollup["not_checkable"] == 2
    assert rollup["machine_verified"] == 0
    assert rollup["unmatched"] == 0


def test_annotate_claim_once_second_match_is_ambiguous_never_a_verdict():
    items = [
        {"what": "Set up PayPal Payouts for the tester program."},
        {"what": "Another paypal-flavoured duplicate ask."},
    ]
    _run(askverify.annotate(items))
    assert "never be probed" in items[0]["verify"]["detail"]
    v = items[1]["verify"]
    assert v["verdict"] == askverify.NOT_CHECKABLE
    assert v["detail"] == askverify.AMBIGUOUS_REASON


def test_annotate_probe_exception_is_honest_unknown(monkeypatch):
    async def boom(refresh):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(askverify.REGISTRY[0], "probe", boom)
    items = [{"what": "store it as BAKE_PAT."}]
    rollup = _run(askverify.annotate(items))
    v = items[0]["verify"]
    assert v["verdict"] == askverify.UNKNOWN
    assert "probe error" in v["detail"] and "kaboom" in v["detail"]
    assert rollup["unknown"] == 1 and rollup["machine_verified"] == 0


def test_annotate_rollup_counts_mixed_verdicts(monkeypatch):
    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)  # done-detected
        if "lumen-drift" in url:
            return _envelope(url, status=404)  # still-open
        return _envelope(url)

    _install_get(monkeypatch, responder)
    items = [
        {"what": "Set SITE_PASSWORD on the botsite Railway service."},
        {"what": "Publish the lumen-drift release."},
        {"what": "Answer Q-0004 please."},
        {"what": "Totally unmatched ask."},
    ]
    rollup = _run(askverify.annotate(items))
    assert rollup == {
        "total": 4, "machine_verified": 2, "done": 1, "still_open": 1,
        "not_checkable": 2, "unknown": 0, "unmatched": 1,
    }
    assert items[0]["verify"]["verdict"] == askverify.DONE
    assert items[1]["verify"]["verdict"] == askverify.STILL_OPEN


# --------------------------------------------------------------------------- #
# Wiring — public /queue stays chip-free and never calls askverify
# --------------------------------------------------------------------------- #
def _offline_client(monkeypatch, tmp_path, responder=None):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    _install_get(monkeypatch, responder or (lambda url: _envelope(url)))
    return TestClient(app)


def test_public_queue_never_calls_askverify_and_carries_no_chips(
    monkeypatch, tmp_path
):
    async def forbidden(items, refresh=False):
        raise AssertionError(
            "the PUBLIC /queue must never run preflight probes"
        )

    monkeypatch.setattr(askverify, "annotate", forbidden)
    with _offline_client(monkeypatch, tmp_path) as c:
        r = c.get("/queue")
        assert r.status_code == 200
        assert "preflight" not in r.text
        assert "machine-verified" not in r.text
        rj = c.get("/queue.json")
        assert rj.status_code == 200
        assert "verify" not in rj.json()


def test_owner_queue_renders_the_verdict_chip(monkeypatch, tmp_path):
    async def fake_overview(refresh=False):
        return {
            "items": [{
                "what": (
                    "Set SITE_PASSWORD on the botsite Railway service so "
                    "the tester-program owner queue becomes reachable."
                ),
                "text": "",
                "fields": {},
                "sources": [{
                    "kind": "lane", "label": "websites", "url": "https://x",
                    "updated_iso": "", "age_hours": 1.0, "age_human": "1h ago",
                }],
            }],
            "lane_notes": [],
            "fleet_manager": {"state": "ok", "reason": "", "items": [],
                              "preamble": "", "body_html": "",
                              "token_set": False, "url": ""},
            "field_order": owner_queue.FIELD_ORDER,
            "summary": {"total": 1, "deduped": 0, "lanes_with_asks": 1,
                        "lanes_total": 1},
            "unreadable_lanes": [],
            "lane_source": {},
        }

    monkeypatch.setattr(owner_queue, "overview", fake_overview)

    def responder(url):
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=503)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner/queue", headers=_basic())
        assert r.status_code == 200
        assert "preflight: still-open" in r.text
        assert "SITE_PASSWORD unset" in r.text
        assert "1 of 1 machine-verified" in r.text


def test_owner_briefing_asks_carry_verdict_chips(monkeypatch, tmp_path):
    ledger = (
        "# Owner actions\n\n"
        "## 🟡 Open — waiting on the owner\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set SITE_PASSWORD on the botsite Railway service.\n"
        "WHERE: railway.\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: A fixture ask no probe matches.\n"
        "WHERE: nowhere.\n\n"
        "## 🟢 Decided / resolved\n"
    )

    def responder(url):
        if "OWNER-ACTIONS.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=ledger)
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=401)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner/briefing", headers=_basic())
        assert r.status_code == 200
        assert "preflight verdict" in r.text
        assert "done-detected — ledger update pending" in r.text
        assert "no registered probe matches" in r.text
        assert "1 of 2 machine-verified" in r.text


def test_owner_board_rollup_chip_counts_and_honest_unknown(
    monkeypatch, tmp_path
):
    # Offline ledger → the chip is the honest unknown, nothing assumed done.
    with _offline_client(monkeypatch, tmp_path) as c:
        r = c.get("/owner", headers=_basic())
        assert r.status_code == 200
        assert "asks: preflight verdicts unknown" in r.text
        assert "machine-verified" not in r.text

    ledger = (
        "## 🟡 Open — waiting on the owner\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set SITE_PASSWORD on the botsite Railway service.\n\n"
        "⚑ OWNER-ACTION\n"
        "WHAT: Set up PayPal Payouts.\n\n"
        "## 🟢 Decided / resolved\n"
    )

    def responder(url):
        if "OWNER-ACTIONS.md" in url:
            return _envelope(url, ok=True, status=200, error="", data=ledger)
        if url == BOTSITE_OWNER_URL:
            return _envelope(url, status=503)
        return _envelope(url)

    with _offline_client(monkeypatch, tmp_path, responder) as c:
        r = c.get("/owner", headers=_basic())
        assert r.status_code == 200
        assert "1 of 2 machine-verified" in r.text
        assert "still-open" in r.text
        assert "not machine-checkable" in r.text


def test_briefing_asks_unknown_state_has_no_verify_rollup(monkeypatch):
    _install_get(monkeypatch, lambda url: _envelope(url))

    data = _run(briefing.asks())
    assert data["state"] == "unknown"
    assert data["verify"] is None
