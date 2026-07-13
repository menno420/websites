"""github.classify_listing — the ONE shared contents-listing honesty ladder.

Unit-pins the classifier's contract directly (a failed listing is never an
empty page; the 404 disposition is the caller's explicit parameter; an empty
list is still "ok"; every composed reason is hard-bounded at
REASON_MAX_CHARS). The per-page wiring is pinned in test_projects.py /
test_prompts.py / test_app.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, github  # noqa: E402


def _res(ok=True, status=200, data=None, error=""):
    return {"ok": ok, "status": status, "data": data, "error": error,
            "fetched_at": "", "cached": False, "url": ""}


# --------------------------------------------------------------------------- #
# ok rungs
# --------------------------------------------------------------------------- #


def test_ok_list_is_ok():
    state, reason = github.classify_listing(
        _res(data=[{"type": "dir", "name": "x"}]), on_404="empty"
    )
    assert (state, reason) == ("ok", "")


def test_ok_EMPTY_list_is_still_ok_callers_own_the_meaning():
    """An empty directory is a real, successfully-fetched fact — whether it
    means "empty registry", "no ideas", or "drift" is the caller's call."""
    state, reason = github.classify_listing(_res(data=[]), on_404="missing")
    assert (state, reason) == ("ok", "")


# --------------------------------------------------------------------------- #
# 404: explicit per-caller disposition
# --------------------------------------------------------------------------- #


def test_404_default_reason_is_the_fetch_reason():
    state, reason = github.classify_listing(
        _res(ok=False, status=404, error="Not Found"), on_404="missing"
    )
    assert state == "missing" and reason == "Not Found"


def test_404_custom_disposition_and_reason():
    state, reason = github.classify_listing(
        _res(ok=False, status=404, error="Not Found"),
        on_404="empty",
        reason_404="the registry has not landed upstream yet",
    )
    assert state == "empty"
    assert reason == "the registry has not landed upstream yet"


# --------------------------------------------------------------------------- #
# not-configured vs unavailable (token presence names itself)
# --------------------------------------------------------------------------- #


def test_403_with_token_set_is_unavailable(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    state, reason = github.classify_listing(
        _res(ok=False, status=403, error="rate limited"), on_404="empty"
    )
    assert state == "unavailable" and reason == "rate limited"


def test_403_with_token_unset_is_not_configured(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    state, reason = github.classify_listing(
        _res(ok=False, status=403, error="rate limited"),
        on_404="empty",
        subject="the owner/repo `projects/` listing",
    )
    assert state == "not-configured"
    assert reason == (
        "GITHUB_TOKEN is not set on this service and the owner/repo "
        "`projects/` listing failed (fetch: rate limited)"
    )


def test_network_exception_status_0_token_unset_is_not_configured(monkeypatch):
    """httpx exceptions mint status=0 envelopes with error='ExcType: msg'."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    state, reason = github.classify_listing(
        _res(ok=False, status=0, error="ConnectError: unreachable"),
        on_404="unknown",
    )
    assert state == "not-configured"
    assert "GITHUB_TOKEN is not set" in reason
    assert "ConnectError: unreachable" in reason


def test_status_0_with_token_set_is_unavailable(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    state, reason = github.classify_listing(
        _res(ok=False, status=0, error="ConnectError: unreachable"),
        on_404="unknown",
    )
    assert state == "unavailable" and reason == "ConnectError: unreachable"


# --------------------------------------------------------------------------- #
# non-list 2xx payload: honest about the wrong shape
# --------------------------------------------------------------------------- #


def test_ok_but_non_list_payload_is_unavailable_with_shape_reason(monkeypatch):
    """A 2xx whose body is not a directory listing (non-JSON text, or a dict)
    must NOT render as ok/empty — it says what actually arrived."""
    monkeypatch.setattr(config, "GITHUB_TOKEN", "tok")
    for data in ("<!doctype html>interstitial", {"message": "not a dir"}):
        state, reason = github.classify_listing(
            _res(ok=True, status=200, data=data), on_404="empty"
        )
        assert state == "unavailable"
        assert reason == "unexpected listing payload (HTTP 200)"


# --------------------------------------------------------------------------- #
# the #240 bound extends to COMPOSED reasons
# --------------------------------------------------------------------------- #


def test_overlong_composed_reason_is_hard_bounded(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    state, reason = github.classify_listing(
        _res(ok=False, status=502, error="x" * 139),  # bounded alone, not composed
        on_404="empty",
        subject="the owner/repo `projects/` listing",
    )
    assert state == "not-configured"
    assert len(reason) <= github.REASON_MAX_CHARS
    assert reason.endswith("…")


def test_overlong_custom_404_reason_is_hard_bounded():
    state, reason = github.classify_listing(
        _res(ok=False, status=404, error="Not Found"),
        on_404="missing",
        reason_404="registry prose " * 20,
    )
    assert state == "missing"
    assert len(reason) <= github.REASON_MAX_CHARS
    assert reason.endswith("…")
