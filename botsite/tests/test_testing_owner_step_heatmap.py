"""Owner-queue drop-off step heatmap: per-task aggregate over guide_exchanges.

Backlog promotion ("Drop-off step heatmap on the owner queue", 2026-07-13,
#293's session 💡): the Drop-offs section shows each abandoned claim's
transcript individually; the rankable signal — the walkthrough step where
chats cluster before a claim dies — needs a per-step aggregate. Covers the
``guided_step_dropoff()`` store accessor (touched/died-here counts, dense
steps, per-task grouping, same scope as ``abandoned_guided_claims()``) and
the heatmap strip rendered inside the Drop-offs section on GET
/testing/owner, the step-text join (step_index → the walkthrough
step's title in the cell tooltip, bare-number fallback for unknown
tasks), and the full-length tail (the strip pads never-reached steps
out to the script's real length with hollow cells + an "of N steps"
label; unknown tasks stay observed-only), and the survival contrast
(per-step ``finished`` finisher counts + ``died_share`` lethality over
ALL touchers — finishers' persisted chats fold into the same cells so
"hard but passable" and "wall" stop rendering identically).
Network-free, same fixture as the drop-offs suite. The
no-auth 401 pin for /testing/owner already lives in
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


def make_finisher(email, steps, task_id=GUIDED_TASK):
    """A claim that chatted at `steps` and then pushed through to a
    submission — the survival-contrast side of the heatmap."""
    claim = make_claim(email, task_id=task_id)
    for step in steps:
        testing_store.add_guide_exchange(claim["id"], step, "hm?", "like so")
    testing_store.create_submission(claim["id"], {"q": "a"}, "made it")
    testing_store.set_claim_status(claim["id"], "submitted")
    return claim


def owner_page(client, monkeypatch):
    monkeypatch.setenv("SITE_PASSWORD", PW)
    r = client.get("/testing/owner", auth=("owner", PW))
    assert r.status_code == 200
    return r.text


# --- store accessor -----------------------------------------------------------

def test_heatmap_counts_touched_and_died_across_claims(client):
    # three drop-offs on one task with differing max steps:
    #   c1 touches 0,1,3 (dies at 3) · c2 touches 0,1 (dies at 1, two
    #   exchanges at step 1 — still ONE claim) · c3 touches only 2 (dies at 2)
    c1 = make_claim("one@example.com")
    c2 = make_claim("two@example.com")
    c3 = make_claim("three@example.com")
    for step in (0, 1, 3):
        testing_store.add_guide_exchange(c1["id"], step, "stuck", "try this")
    testing_store.add_guide_exchange(c2["id"], 0, "hello?", "hi")
    testing_store.add_guide_exchange(c2["id"], 1, "still stuck", "ok")
    testing_store.add_guide_exchange(c2["id"], 1, "really stuck", "hm")
    testing_store.add_guide_exchange(c3["id"], 2, "toggle?", "flip it")
    rows = testing_store.guided_step_dropoff()
    assert len(rows) == 1
    task = rows[0]
    assert task["task_id"] == GUIDED_TASK
    assert task["claim_count"] == 3
    # dense 0..3 — step 2 appears even though only one claim touched it
    assert [s["step_index"] for s in task["steps"]] == [0, 1, 2, 3]
    assert [s["touched"] for s in task["steps"]] == [2, 2, 1, 1]
    assert [s["died_here"] for s in task["steps"]] == [0, 1, 1, 1]


def test_heatmap_groups_by_task_ordered_by_task_id(client):
    b = make_claim("b@example.com", task_id="walkthrough-zeta")
    a = make_claim("a@example.com", task_id="walkthrough-alpha")
    testing_store.add_guide_exchange(b["id"], 1, "where?", "there")
    testing_store.add_guide_exchange(a["id"], 0, "how?", "so")
    rows = testing_store.guided_step_dropoff()
    assert [t["task_id"] for t in rows] == [
        "walkthrough-alpha", "walkthrough-zeta"
    ]
    assert rows[0]["claim_count"] == 1
    # zeta's claim only chatted at step 1 — step 0 renders as a zero cell
    # (zero touchers → died_share stays 0.0, no division blow-up)
    assert rows[1]["steps"] == [
        {"step_index": 0, "touched": 0, "died_here": 0,
         "finished": 0, "died_share": 0.0},
        {"step_index": 1, "touched": 1, "died_here": 1,
         "finished": 0, "died_share": 1.0},
    ]


def test_heatmap_empty_without_any_guided_dropoff(client):
    make_claim("silent@example.com")  # claimed, but never chatted
    assert testing_store.guided_step_dropoff() == []


def test_heatmap_excludes_submitted_claims(client):
    # same scope as abandoned_guided_claims(): a submission row (and status
    # flip) takes the claim out of the drop-off aggregate entirely — its
    # chat re-enters only as the per-step `finished` contrast count
    done = make_claim("finisher@example.com")
    testing_store.add_guide_exchange(done["id"], 0, "How?", "Like this.")
    testing_store.create_submission(done["id"], {"q": "a"}, "found nothing")
    testing_store.set_claim_status(done["id"], "submitted")
    stuck = make_claim("walker@example.com")
    testing_store.add_guide_exchange(stuck["id"], 2, "lost", "step by step")
    rows = testing_store.guided_step_dropoff()
    assert len(rows) == 1
    assert rows[0]["claim_count"] == 1
    assert rows[0]["finisher_count"] == 1
    assert rows[0]["steps"][2] == {
        "step_index": 2, "touched": 1, "died_here": 1,
        "finished": 0, "died_share": 1.0,
    }
    # the finisher's step-0 chat shows up as survival contrast, not touched
    assert rows[0]["steps"][0] == {
        "step_index": 0, "touched": 0, "died_here": 0,
        "finished": 1, "died_share": 0.0,
    }


# --- owner page rendering -------------------------------------------------------

def test_heatmap_strip_renders_with_expected_counts(client, monkeypatch):
    c1 = make_claim("one@example.com")
    c2 = make_claim("two@example.com")
    testing_store.add_guide_exchange(c1["id"], 0, "start?", "header")
    testing_store.add_guide_exchange(c1["id"], 1, "then?", "footer")
    testing_store.add_guide_exchange(c2["id"], 0, "hm", "ok")
    html = owner_page(client, monkeypatch)
    assert "Step heatmap" in html
    assert "2 drop-off(s)" in html
    # steps display 1-based, matching the transcript block's "[step N]"
    assert "step 1 · 2 touched · 1 died" in html
    assert "step 2 · 1 touched · 1 died" in html
    # cell shading scales with the died-here share (1/2 → 0.7 * 0.5)
    assert "background:rgba(214,69,49,0.35)" in html


def test_heatmap_absent_when_no_dropoffs(client, monkeypatch):
    make_claim("silent@example.com", name="Sil")  # no chat → no heatmap
    html = owner_page(client, monkeypatch)
    assert "No drop-offs" in html
    assert "Step heatmap" not in html


# --- step text labels (step_index → walkthrough step title join) ----------------

def test_heatmap_tooltip_carries_step_text(client, monkeypatch):
    # GUIDED_TASK is a real catalog task — its walkthrough step titles join
    # into the cell tooltip so the owner reads WHAT the step asks, not just
    # its number ("step 1 — Homepage first impression" instead of "step 1")
    c = make_claim("texty@example.com")
    testing_store.add_guide_exchange(c["id"], 0, "start?", "header")
    testing_store.add_guide_exchange(c["id"], 1, "then?", "footer")
    html = owner_page(client, monkeypatch)
    assert "step 1 — Homepage first impression: 1 chat(s) touched it" in html
    assert "step 2 — Features: 1 chat(s) touched it, 1 died here" in html
    # the visible cell stays compact — numbers + counts, no title text
    assert "step 1 · 1 touched · 0 died" in html


def test_heatmap_tooltip_falls_back_to_bare_number(client, monkeypatch):
    # a task with no catalog entry has no step script — step_text stays
    # empty and the tooltip keeps the pre-join bare-number form
    c = make_claim("ghost@example.com", task_id="walkthrough-unknown-task")
    testing_store.add_guide_exchange(c["id"], 1, "where?", "there")
    html = owner_page(client, monkeypatch)
    assert 'title="step 2: 1 chat(s) touched it, 1 died here"' in html
    assert "step 2 —" not in html


# --- full-length tail (pad the strip out to the walkthrough's real length) ------

def test_heatmap_pads_tail_to_full_script_length(client, monkeypatch):
    # GUIDED_TASK's walkthrough is 6 steps; two drop-offs whose chats touch
    # only steps 0–2 must still render a 6-cell strip: 3 observed cells plus
    # 3 hollow never-reached tail cells and an "of 6 steps" label —
    # distance-to-finish is the severity signal the strip used to hide
    c1 = make_claim("early@example.com")
    c2 = make_claim("earlier@example.com")
    for step in (0, 1, 2):
        testing_store.add_guide_exchange(c1["id"], step, "stuck", "try this")
    testing_store.add_guide_exchange(c2["id"], 1, "lost", "go on")
    html = owner_page(client, monkeypatch)
    assert "of 6 steps" in html
    # observed cells keep the counts form ...
    assert "step 3 · 1 touched · 1 died" in html
    # ... the unreached tail renders as never-reached cells (steps 4–6)
    for n in (4, 5, 6):
        assert f"step {n} · never reached" in html
    assert "step 3 · never reached" not in html
    # tail tooltips still carry the step's own text from the script join
    assert (
        "step 6 — Theme and phone width: never reached by any drop-off's chat"
        in html
    )


def test_heatmap_no_tail_when_dropoff_dies_at_last_step(client, monkeypatch):
    # a chat that reaches the final step (index 5 of 6) already densifies the
    # strip to full length — nothing to pad, no never-reached cell
    c = make_claim("finisher@example.com")
    testing_store.add_guide_exchange(c["id"], 5, "last one", "almost there")
    html = owner_page(client, monkeypatch)
    assert "of 6 steps" in html
    assert "step 6 · 1 touched · 1 died" in html
    assert "never reached" not in html


def test_heatmap_unknown_task_keeps_observed_only_strip(client, monkeypatch):
    # no catalog entry → empty step script: no padding, no "of N steps"
    # label — the strip stays exactly the observed-only pre-tail rendering
    c = make_claim("ghost@example.com", task_id="walkthrough-unknown-task")
    testing_store.add_guide_exchange(c["id"], 1, "where?", "there")
    html = owner_page(client, monkeypatch)
    assert "step 2 · 1 touched · 1 died" in html
    assert "never reached" not in html
    assert "· of " not in html


# --- survival contrast (finishers' chats fold into the strip) -------------------

def test_heatmap_survival_contrast_counts_finishers_and_died_share(client):
    # one drop-off dies at step 1; two finishers also asked there but
    # pushed through — the cell's lethality is 1 death over 3 touchers,
    # not the raw all-drop-offs-died-here it would read without contrast
    stuck = make_claim("wall@example.com")
    testing_store.add_guide_exchange(stuck["id"], 1, "stuck", "try this")
    make_finisher("f1@example.com", [0, 1])
    make_finisher("f2@example.com", [1])
    rows = testing_store.guided_step_dropoff()
    assert len(rows) == 1
    assert rows[0]["claim_count"] == 1
    assert rows[0]["finisher_count"] == 2
    step0, step1 = rows[0]["steps"]
    assert step0 == {"step_index": 0, "touched": 0, "died_here": 0,
                     "finished": 1, "died_share": 0.0}
    assert step1["touched"] == 1
    assert step1["died_here"] == 1
    assert step1["finished"] == 2
    assert step1["died_share"] == pytest.approx(1 / 3)


def test_heatmap_finisher_only_step_extends_dense_range(client):
    # the drop-off died at step 0; a finisher asked further along at step 2
    # — the strip grows to cover it, and the untouched gap step in between
    # stays an all-zero cell (zero touchers → died_share 0.0, no division)
    stuck = make_claim("early@example.com")
    testing_store.add_guide_exchange(stuck["id"], 0, "lost", "step one")
    make_finisher("deep@example.com", [2])
    rows = testing_store.guided_step_dropoff()
    task = rows[0]
    assert [s["step_index"] for s in task["steps"]] == [0, 1, 2]
    assert task["steps"][0]["died_share"] == 1.0
    assert task["steps"][1] == {"step_index": 1, "touched": 0, "died_here": 0,
                                "finished": 0, "died_share": 0.0}
    assert task["steps"][2] == {"step_index": 2, "touched": 0, "died_here": 0,
                                "finished": 1, "died_share": 0.0}


def test_heatmap_finishers_alone_create_no_task_row(client):
    # the strip stays a drop-off view: a task where everyone finished has
    # nothing to rank — finishers are contrast, not subject
    make_finisher("solo@example.com", [0, 1])
    assert testing_store.guided_step_dropoff() == []


def test_heatmap_cell_renders_finisher_annotation_and_lethality_shading(
    client, monkeypatch
):
    # one drop-off touches steps 0–1 and dies at 1; a finisher also asked
    # at step 0. Step 0 (2 touchers, 0 deaths) renders pale with the
    # finisher annotation; step 1 (1 toucher, 1 death) renders as the wall
    stuck = make_claim("walker@example.com")
    testing_store.add_guide_exchange(stuck["id"], 0, "start?", "header")
    testing_store.add_guide_exchange(stuck["id"], 1, "then?", "footer")
    make_finisher("f1@example.com", [0])
    html = owner_page(client, monkeypatch)
    assert "1 drop-off(s) · 1 finisher(s) chatted" in html
    assert "step 1 · 1 touched · 0 died · 1 finisher(s) asked" in html
    assert "1 finisher(s) also asked here" in html
    # shading is died-share over ALL touchers: 0/2 pale, 1/1 full-dark
    assert "background:rgba(214,69,49,0.00)" in html
    assert "background:rgba(214,69,49,0.70)" in html
    # the wall cell carries no finisher annotation — nobody asked there
    assert "step 2 · 1 touched · 1 died · " not in html


def test_heatmap_absent_when_only_finishers_chatted(client, monkeypatch):
    # rendering twin of the store guard: finisher chats without any
    # drop-off leave the Drop-offs section empty, heatmap and all
    make_finisher("solo@example.com", [0, 1])
    html = owner_page(client, monkeypatch)
    assert "No drop-offs" in html
    assert "Step heatmap" not in html


def test_heatmap_step_text_truncates_and_bounds():
    # pure helper: long titles truncate to the cap with an ellipsis; an
    # out-of-range index or a text-less step falls back to empty
    steps = [{"title": "x" * 200}, {"instruction": "no title key"}]
    text = testing._heatmap_step_text(steps, 0)
    assert len(text) == testing.HEATMAP_STEP_TEXT_MAX
    assert text.endswith("…")
    assert testing._heatmap_step_text(steps, 1) == ""
    assert testing._heatmap_step_text(steps, 5) == ""
    assert testing._heatmap_step_text(steps, -1) == ""
