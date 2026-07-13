"""Owner-queue per-step question digest: WHAT testers asked behind a cell.

Backlog promotion ("Per-step question digest — surface WHAT testers asked
at a hotspot, not just how many", 2026-07-13, the finisher-hotspots
session 💡): the heatmap and the finisher hotspots (PRs #294/#298/#303)
rank WHERE guide chats cluster, but the owner still opens each drop-off's
per-claim transcript one by one to learn what confused people — and
finishers' transcripts on hotspot tasks render nowhere at all (PR #292
attaches them to submissions, not to the strip). Covers the
``guided_step_questions()`` store accessor (message text only — never the
guide's replies — grouped by (task, step) across ALL claims regardless of
outcome, newest-first with a per-cell cap + total) and the collapsed
<details> digest rendered behind both strips' cells on GET /testing/owner
(presence on heatmap and hotspot rows, cap annotation, truncation via
``_digest_question_text``, and autoescape on hostile tester input).
Network-free, same fixture as the heatmap suite. The no-auth 401 pin for
/testing/owner already lives in
``test_testing.py::test_owner_401_on_missing_or_wrong_password``.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from botsite import app as app_module
from botsite import data_source as ds
from botsite import testing, testing_ai, testing_store

PW = "owner-pass"
GUIDED_TASK = "walkthrough-botsite-first-visit"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("TESTING_DB_PATH", str(tmp_path / "testing.sqlite3"))
    for var in (
        "SITE_PASSWORD",
        "TESTING_AUTOPAY_ENABLED",
        "PAYPAL_CLIENT_ID",
        "PAYPAL_CLIENT_SECRET",
        "TESTING_BOUNTY_CAP_USD",
        "ANTHROPIC_API_KEY",  # no key in tests → degraded mode, zero network
        "TESTING_AI_MODEL",
        "TESTING_AI_DAILY_CAP",
        "TESTING_AI_GUIDE_CAP",
        "TESTING_AUTOPAY_MIN_SCORE",
    ):
        monkeypatch.delenv(var, raising=False)
    testing.reset_rate_limits()
    testing_ai.reset_ai_state()
    ds.clear_cache()
    ds.prime_cache({})
    ds.set_client(ds.make_client())  # never actually hit (cache is warm)
    with TestClient(app_module.app) as c:
        yield c
    ds.clear_cache()


def make_claim(email, name="Wanda", task_id=GUIDED_TASK):
    """Store-level claim (status 'claimed'); token just has to be unique."""
    return testing_store.create_claim(
        task_id, name, email, "", f"token-{email}"
    )


def make_finisher(email, exchanges, task_id=GUIDED_TASK):
    """A claim that chatted `(step, message)` pairs and then pushed through
    to a submission — the finisher side of both strips."""
    claim = make_claim(email, task_id=task_id)
    for step, message in exchanges:
        testing_store.add_guide_exchange(claim["id"], step, message, "like so")
    testing_store.create_submission(claim["id"], {"q": "a"}, "made it")
    testing_store.set_claim_status(claim["id"], "submitted")
    return claim


def owner_page(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    return r.text


# --- store accessor -----------------------------------------------------------

def test_questions_group_by_task_and_step_across_outcomes(client):
    # a drop-off asks at steps 0 and 1, a finisher asks at step 1 — the cell
    # pools BOTH (all claims, whatever became of the asker), newest first,
    # message text only: the guide's replies never enter the digest
    stuck = make_claim("stuck@example.com")
    testing_store.add_guide_exchange(stuck["id"], 0, "where is it?", "header")
    testing_store.add_guide_exchange(stuck["id"], 1, "toggle broken?", "flip")
    make_finisher("f1@example.com", [(1, "same toggle?")])
    digest = testing_store.guided_step_questions()
    assert set(digest) == {GUIDED_TASK}
    cells = digest[GUIDED_TASK]
    assert cells[0] == {"total": 1, "questions": ["where is it?"]}
    assert cells[1] == {
        "total": 2, "questions": ["same toggle?", "toggle broken?"]
    }
    replies = str(digest)
    assert "header" not in replies and "flip" not in replies


def test_questions_cap_keeps_newest_and_counts_total(client):
    # seven exchanges at one step from one chatty claim: the cell keeps the
    # newest QUESTION_DIGEST_CAP texts (newest first) but the total stays 7
    c = make_claim("chatty@example.com")
    for n in range(1, 8):
        testing_store.add_guide_exchange(c["id"], 2, f"digestq-{n}", "ok")
    cell = testing_store.guided_step_questions()[GUIDED_TASK][2]
    assert testing_store.QUESTION_DIGEST_CAP == 5
    assert cell["total"] == 7
    assert cell["questions"] == [
        "digestq-7", "digestq-6", "digestq-5", "digestq-4", "digestq-3"
    ]


def test_questions_empty_without_exchanges(client):
    # nothing at all → {}; a chatless claim contributes nothing either
    assert testing_store.guided_step_questions() == {}
    make_claim("silent@example.com")
    assert testing_store.guided_step_questions() == {}


def test_questions_group_tasks_separately(client):
    a = make_claim("a@example.com", task_id="walkthrough-alpha")
    z = make_claim("z@example.com", task_id="walkthrough-zeta")
    testing_store.add_guide_exchange(a["id"], 0, "alpha q", "r")
    testing_store.add_guide_exchange(z["id"], 3, "zeta q", "r")
    digest = testing_store.guided_step_questions()
    assert digest["walkthrough-alpha"] == {
        0: {"total": 1, "questions": ["alpha q"]}
    }
    assert digest["walkthrough-zeta"] == {
        3: {"total": 1, "questions": ["zeta q"]}
    }


# --- owner page rendering -------------------------------------------------------

def test_digest_renders_behind_heatmap_cell(client, monkeypatch):
    # the heatmap cell says "2 touched" — the digest under the strip lists
    # the actual questions, collapsed, pooling the finisher who also asked
    stuck = make_claim("stuck@example.com")
    testing_store.add_guide_exchange(
        stuck["id"], 1, "where does the toggle live?", "footer"
    )
    make_finisher("f1@example.com", [(1, "dark mode toggle?")])
    html = owner_page(client, monkeypatch)
    assert "Step heatmap" in html
    assert "step 2 · 2 tester question(s) (untrusted tester input)" in html
    assert "· where does the toggle live?" in html
    assert "· dark mode toggle?" in html
    # collapsed by default — a plain <details>, no open attribute anywhere
    assert "<details open" not in html


def test_digest_renders_behind_finisher_hotspot_cell(client, monkeypatch):
    # the whole point of the slice: finishers' questions on a zero-drop-off
    # task were rendered NOWHERE (PR #292 hangs transcripts on submissions,
    # not the strip) — the hotspot cell now carries them
    make_finisher("f1@example.com", [(0, "what counts as done here?")])
    html = owner_page(client, monkeypatch)
    assert "Finisher question hotspots" in html
    assert "step 1 · 1 tester question(s) (untrusted tester input)" in html
    assert "· what counts as done here?" in html


def test_digest_escapes_hostile_message(client, monkeypatch):
    # untrusted tester input: a script-tag message renders escaped (Jinja
    # autoescape), never as markup — anywhere on the page
    stuck = make_claim("evil@example.com")
    testing_store.add_guide_exchange(
        stuck["id"], 0, "<script>alert(1)</script>", "nice try"
    )
    html = owner_page(client, monkeypatch)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_digest_caps_rendered_questions_at_newest_five(client, monkeypatch):
    # seven questions at one step: the digest shows the newest five with the
    # "newest N shown" annotation; the two oldest appear only once on the
    # page (the claim's own transcript block), never in the digest
    stuck = make_claim("chatty@example.com")
    for n in range(1, 8):
        testing_store.add_guide_exchange(stuck["id"], 0, f"digestq-{n}", "ok")
    html = owner_page(client, monkeypatch)
    assert (
        "step 1 · 7 tester question(s) · newest 5 shown"
        " (untrusted tester input)" in html
    )
    for n in (3, 4, 5, 6, 7):
        assert html.count(f"digestq-{n}") == 2  # transcript + digest
    for n in (1, 2):
        assert html.count(f"digestq-{n}") == 1  # transcript only


def test_digest_truncates_long_messages(client, monkeypatch):
    # a very long question truncates to the display cap with an ellipsis in
    # the digest; the per-claim transcript keeps the full text
    long_q = "L" * 200
    stuck = make_claim("longwinded@example.com")
    testing_store.add_guide_exchange(stuck["id"], 0, long_q, "ok")
    html = owner_page(client, monkeypatch)
    assert "L" * 159 + "…" in html
    assert long_q in html  # the transcript block stays untruncated


def test_digest_absent_for_question_free_cells(client, monkeypatch):
    # padded never-reached cells and steps nobody asked about render no
    # digest row — only the one asked-at step grows a <details>
    stuck = make_claim("early@example.com")
    testing_store.add_guide_exchange(stuck["id"], 0, "start?", "header")
    html = owner_page(client, monkeypatch)
    assert html.count("tester question(s)") == 1
    assert "step 1 · 1 tester question(s)" in html


def test_digest_question_text_truncates_and_bounds():
    # pure helper: long messages truncate to the cap with an ellipsis;
    # short ones pass through stripped; empties stay empty
    text = testing._digest_question_text("x" * 500)
    assert len(text) == testing.QUESTION_DIGEST_TEXT_MAX
    assert text.endswith("…")
    assert testing._digest_question_text("  short?  ") == "short?"
    assert testing._digest_question_text("") == ""
    assert testing._digest_question_text(None) == ""
