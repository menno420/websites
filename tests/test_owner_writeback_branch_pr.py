"""O-020 owner writeback — the branch + auto-PR path (Q2=b, owner-confirmed).

main is ruleset-protected (required `quality` check), so a direct contents PUT
to main is impossible with the PAT. Each gated writeback therefore commits its
append to a per-submit `claude/owner-writeback-<entry-id>` branch and opens an
auto-merging PR into main. These tests pin that path end to end, network-free
(every GitHub seam mocked):

  (a) happy path — the ordered call sequence (base ref → create branch → PUT to
      the branch → open PR) and that the entry records the PR/commit ONLY on
      full success.
  (b) the committed target is control/**-only for assist AND note/complete —
      the CI control fast-lane invariant that lets the runtime PR merge with no
      session card.
  (c) honest-degrade — no token / branch-create rejected / PR-open failure all
      stay `queued` with the exact error; never a claimed commit/PR.
  (d) the generated assist ORDER passes the real inbox append-only grammar gate.
  (e) the CSRF/same-origin/rate-limit floor is still enforced on the POST routes.
  (f) the state_summary + audit-row contract (the branch/pr columns).
"""

from __future__ import annotations

import asyncio
import base64
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bootstrap  # noqa: E402  (the kit gate — the real inbox grammar checker)
from fastapi.testclient import TestClient  # noqa: E402

from app import config, github, owner, owner_assist, writeback  # noqa: E402
from app.main import app  # noqa: E402

OWNER_PW = "test-owner-pw"
SAME_ORIGIN = "http://testserver"
CROSS_ORIGIN = "https://evil.example"

COMMIT_SHA = "deadbeefcafe0123456789abcdef0123456789ab"
BASE_SHA = "ba5e0000000000000000000000000000000000ba"
PR_NUMBER = 4020
PR_URL = "https://github.com/menno420/websites/pull/4020"
FAKE_INBOX = (
    "# Inbox\n\n"
    "## ORDER 019 · 2026-07-12T15:42Z · status: new\n"
    "priority: P1\ndo: x\nwhy: y\ndone-when: z\n"
)


@pytest.fixture(autouse=True)
def _engine_env(monkeypatch, tmp_path):
    """Per-test SQLite, a write token present, default (branch+PR) mode."""
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    monkeypatch.setenv(writeback.ENV_TOKEN, "write-token")
    yield


def _install_fake(monkeypatch, *, read_text=FAKE_INBOX, read_status=200,
                  ref_status=200, create_status=201, put_status=200,
                  put_sha=COMMIT_SHA, pr_status=201, existing_prs=None):
    """Record every GitHub call and script the branch+PR sequence."""
    calls: list[tuple] = []

    def _err(status, msg="Not Found"):
        return {"ok": False, "status": status, "data": None, "error": msg}

    async def fake(method, path, json_body=None, token=""):
        calls.append((method, path, json_body, token))
        if method == "GET" and "/git/ref/heads/" in path:
            if ref_status != 200:
                return _err(ref_status)
            return {"ok": True, "status": 200,
                    "data": {"object": {"sha": BASE_SHA}}, "error": ""}
        if method == "POST" and path.endswith("/git/refs"):
            if create_status in (200, 201):
                return {"ok": True, "status": create_status,
                        "data": {"ref": (json_body or {}).get("ref")}, "error": ""}
            return _err(create_status, "Resource not accessible by personal access token")
        if method == "GET" and "/contents/" in path:
            if read_status != 200:
                return _err(read_status)
            return {"ok": True, "status": 200,
                    "data": {"content": base64.b64encode(read_text.encode()).decode(),
                             "sha": "blobsha123"}, "error": ""}
        if method == "PUT" and "/contents/" in path:
            if put_status == 200:
                return {"ok": True, "status": 200,
                        "data": {"commit": {"sha": put_sha,
                                            "html_url": "https://gh/commit/" + put_sha}},
                        "error": ""}
            return _err(put_status, "Resource not accessible by personal access token")
        if method == "POST" and path.endswith("/pulls"):
            if pr_status in (200, 201):
                return {"ok": True, "status": pr_status,
                        "data": {"number": PR_NUMBER, "html_url": PR_URL}, "error": ""}
            return _err(pr_status, "Validation Failed")
        if method == "GET" and "/pulls?" in path:
            return {"ok": True, "status": 200, "data": existing_prs or [], "error": ""}
        raise AssertionError(f"unexpected GitHub call {method} {path}")

    monkeypatch.setattr(github, "api_request", fake)
    return calls


def _submit(action, target="", text="hello"):
    return asyncio.run(writeback.submit(action, target, text))


# --------------------------------------------------------------------------
# (a) happy path — the sequence + record-only-on-success
# --------------------------------------------------------------------------
def test_branch_pr_happy_path_commits_then_opens_pr(monkeypatch):
    calls = _install_fake(monkeypatch)
    entry = _submit("assist", "botsite payouts", "please wire PayPal")

    assert entry["status"] == "committed"
    assert entry["commit_sha"] == COMMIT_SHA
    assert entry["pr_number"] == PR_NUMBER
    assert entry["pr_url"] == PR_URL
    assert entry["commit_url"] == PR_URL
    wb_branch = writeback.writeback_branch_name(entry)
    assert entry["branch"] == wb_branch
    assert wb_branch.startswith("claude/owner-writeback-")

    kinds = [(m, p.split("?")[0].split("/repos/menno420/websites")[-1]) for m, p, _, _ in calls]
    # base ref → create branch → read on branch → PUT on branch → open PR
    assert kinds[0] == ("GET", "/git/ref/heads/main")
    assert kinds[1] == ("POST", "/git/refs")
    assert calls[1][2]["ref"] == f"refs/heads/{wb_branch}"
    assert calls[1][2]["sha"] == BASE_SHA
    put = next(c for c in calls if c[0] == "PUT" and "/contents/" in c[1])
    assert put[2]["branch"] == wb_branch  # commit lands on the BRANCH, not main
    pr = next(c for c in calls if c[0] == "POST" and c[1].endswith("/pulls"))
    assert pr[2]["base"] == "main"
    assert pr[2]["head"] == wb_branch
    assert pr[2]["draft"] is False
    # the PR POST is the last call — the commit precedes the PR open
    assert calls[-1] is pr


def test_pr_recorded_only_after_the_commit_verified(monkeypatch):
    # PUT carries no SHA → nothing may be claimed and NO PR is opened
    calls = _install_fake(monkeypatch, put_status=200, put_sha="")
    entry = _submit("note", "", "n")
    assert entry["status"] == "queued"
    assert entry["commit_sha"] == ""
    assert entry["pr_number"] == 0 and entry["pr_url"] == ""
    assert not any(c[0] == "POST" and c[1].endswith("/pulls") for c in calls)


# --------------------------------------------------------------------------
# (b) targets are control/**-only — the fast-lane invariant
# --------------------------------------------------------------------------
def test_targets_are_control_only(monkeypatch):
    _install_fake(monkeypatch, read_text="# Owner notes\n")
    assist = _submit("assist", "x", "help")
    note = _submit("note", "", "an idea")
    complete = _submit("complete", "Mint the PAT", "done")

    assert assist["path"] == "control/inbox.md"
    assert note["path"] == "control/owner-notes.md"
    assert complete["path"] == "control/owner-notes.md"
    for e in (assist, note, complete):
        assert e["path"].startswith("control/"), e["path"]
        assert e["status"] == "committed"


# --------------------------------------------------------------------------
# (c) honest-degrade — never a claimed commit/PR that did not land
# --------------------------------------------------------------------------
def test_no_token_stays_queued_and_makes_no_calls(monkeypatch):
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    calls = _install_fake(monkeypatch)
    entry = _submit("note", "", "flush me later")
    assert entry["status"] == "queued"
    assert entry["commit_sha"] == "" and entry["pr_url"] == ""
    assert "write token not available" in entry["error"]
    assert calls == []  # nothing was attempted against GitHub


def test_branch_create_rejected_stays_queued(monkeypatch):
    calls = _install_fake(monkeypatch, create_status=403)
    entry = _submit("assist", "x", "help")
    assert entry["status"] == "queued"
    assert entry["commit_sha"] == ""
    assert "HTTP 403" in entry["error"]
    assert "contents:write" in entry["error"]
    # never reached the PUT or the PR open
    assert not any(c[0] == "PUT" for c in calls)
    assert not any(c[1].endswith("/pulls") for c in calls)


def test_pr_open_failure_stays_queued_after_commit(monkeypatch):
    # the commit lands on the branch, but opening the PR fails → queued, no
    # false success (the commit sha is recorded so a retry re-opens the PR)
    _install_fake(monkeypatch, pr_status=500)
    entry = _submit("note", "", "n")
    assert entry["status"] == "queued"
    assert entry["commit_sha"] == COMMIT_SHA  # the branch commit is verified
    assert entry["pr_number"] == 0 and entry["pr_url"] == ""
    assert "opening the auto-merge" in entry["error"]


# --------------------------------------------------------------------------
# (d) the generated ORDER passes the REAL inbox append-only grammar gate
# --------------------------------------------------------------------------
def test_generated_assist_order_passes_inbox_gate_grammar():
    entry = {"id": 12, "action": "assist", "target": "botsite payouts",
             "text": "please wire PayPal"}
    block = writeback.render_assist_block(entry, FAKE_INBOX)
    # the header shape the gate requires
    assert bootstrap.ORDER_HEADER_RE.match(block.splitlines()[0])
    # all four required fields (priority/do/why/done-when) — done-when was the
    # one previously missing that would have red'd the gate
    for field in bootstrap.ORDER_REQUIRED_FIELDS:
        assert any(ln.lstrip().startswith(field) for ln in block.splitlines()), field
    # the checker itself finds nothing on the appended region (pure-append)
    appended = "\n\n" + block
    assert bootstrap._order_grammar_findings(appended) == []


# --------------------------------------------------------------------------
# (e) the security floor is still enforced on the POST routes (default path)
# --------------------------------------------------------------------------
@pytest.fixture()
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PW)
    monkeypatch.setenv(writeback.ENV_DB_PATH, str(tmp_path / "wb.sqlite3"))
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    owner.reset_rate_limits()
    owner_assist.reset_assist_state()

    async def fail(method, path, json_body=None, token=""):
        raise AssertionError("github.api_request must not be reached here")

    monkeypatch.setattr(github, "api_request", fail)
    with TestClient(app) as c:
        yield c
    owner.reset_rate_limits()


def _basic() -> dict:
    tok = base64.b64encode(b"owner:test-owner-pw").decode()
    return {"Authorization": f"Basic {tok}"}


def test_writeback_posts_reject_cross_and_missing_origin(client):
    for action, data in [
        ("assist", {"target": "", "text": "help"}),
        ("note", {"target": "", "text": "note"}),
        ("complete", {"target": "x", "text": ""}),
    ]:
        cross = client.post(f"/owner/queue/actions/{action}", data=data,
                            headers={**_basic(), "Origin": CROSS_ORIGIN})
        assert cross.status_code == 403, action
        missing = client.post(f"/owner/queue/actions/{action}", data=data,
                              headers=_basic())
        assert missing.status_code == 403, action  # no Origin/Referer → rejected


def test_writeback_post_rate_limited(client):
    hdr = {**_basic(), "Origin": SAME_ORIGIN}
    for i in range(owner.RATE_LIMIT_MAX_REQUESTS):
        assert client.post("/owner/queue/actions/note",
                           data={"target": "", "text": f"n{i}"},
                           headers=hdr).status_code == 200
    tripped = client.post("/owner/queue/actions/note",
                          data={"target": "", "text": "over"}, headers=hdr)
    assert tripped.status_code == 429


# --------------------------------------------------------------------------
# (f) contract pins — state_summary + the audit-row branch/pr columns
# --------------------------------------------------------------------------
def test_state_summary_contract(monkeypatch):
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    s = writeback.state_summary()
    assert s["base"] == "main"
    assert s["branch"] == "main"  # back-compat alias = the PR base
    assert s["branch_prefix"] == "claude/owner-writeback-"
    assert s["repo"] == "menno420/websites"
    assert s["inbox_path"] == "control/inbox.md"
    assert s["notes_path"] == "control/owner-notes.md"
    assert s["token_env"] == "GITHUB_TOKEN"
    assert s["token_set"] is False


def test_audit_row_carries_branch_and_pr_columns(monkeypatch):
    _install_fake(monkeypatch, read_text="# Owner notes\n")
    entry = _submit("note", "", "n")
    for col in ("branch", "pr_number", "pr_url"):
        assert col in entry, col
    assert entry["branch"] == writeback.writeback_branch_name(entry)
    assert entry["pr_number"] == PR_NUMBER
    assert entry["pr_url"] == PR_URL
