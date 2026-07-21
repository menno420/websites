"""gen_edition.py — the edition auto-drafter. Network-free and clock-free here:
every test drives the pure ``render_edition`` transform (or ``main`` against a
tmp mirror dir) with canned mirror dicts, so nothing shells out and no wall
clock enters the assertions. Determinism is a first-class property under test —
the drafter must be idempotent (same date+number+mirrors → identical bytes) so
a re-bake never churns an edition, and its output must round-trip through
``review.editions`` unchanged (front-matter contract + list/parse)."""

from __future__ import annotations

import json

from review import editions, gen_edition

# --------------------------------------------------------------------------- #
# Canned mirrors — small honest stand-ins for the committed review/data/*.json,
# shaped exactly like the real bakes so the derived facts are real transforms.
# --------------------------------------------------------------------------- #
STATS = {
    "generated_at": "2026-07-20T08:19:50Z",
    "repos": {
        "alpha": {"ok": True, "total_prs": 100, "open_issues_and_prs": 2},
        "beta": {"ok": True, "total_prs": 50, "open_issues_and_prs": 1},
        "gamma": {"ok": False, "reason": "404 for agent token"},
    },
}
FLEET = {
    "registry": {"total_seats": 24, "repo_seats": 17},
    "seats": [
        {"seat": "S1", "repos": [{"repo": "alpha", "heartbeat_available": True}]},
        {"seat": "S2", "repos": [{"repo": "beta", "heartbeat_available": False}]},
    ],
}
RELEASES = {"entries": [{"slug": "g1", "drift": False}], "drift_count": 0}
SNAPSHOT = {
    "generated_at": "2026-07-20T08:19:34Z",
    "git_head": "79d57e0c0cd4efe5a2c4b6cef6e144da5f2c46b6",
    "days": [
        {"date": "2026-07-13", "test_functions_eod": 106},
        {"date": "2026-07-14", "test_functions_eod": 300},
    ],
    "totals": {"prs_merged": 430, "commits": 468, "test_functions": 300, "services": 4},
}
QUESTIONS = {"questions": []}


def _mirrors(**overrides):
    m = {
        "stats": STATS,
        "fleet": FLEET,
        "releases": RELEASES,
        "snapshot": SNAPSHOT,
        "questions": QUESTIONS,
    }
    m.update(overrides)
    return m


# --------------------------------------------------------------------------- #
# (a) Front-matter carries every key editions.parse_edition requires
# --------------------------------------------------------------------------- #
def test_render_front_matter_has_all_required_keys():
    text = gen_edition.render_edition(2, "2026-07-21", _mirrors())
    assert text.startswith("---\n")
    header = text.split("---\n", 2)[1]
    keys = {line.split(":", 1)[0].strip() for line in header.splitlines() if ":" in line}
    # parse_edition needs a non-empty title and a YYYY-MM-DD date; the site's
    # index + Atom feed also render summary.
    assert {"title", "date", "summary"} <= keys


def test_render_derives_facts_from_mirrors_only():
    text = gen_edition.render_edition(2, "2026-07-21", _mirrors())
    # numbers are real transforms of the canned mirrors, not invented:
    assert "150" in text  # 100 + 50 total_prs across ok repos
    assert "2 of 3 repositories" in text  # gamma failed the bake
    assert "24 seats" in text and "2 standing seats" in text  # 2 seats in fixture
    assert "growing from 106 to 300 functions" in text
    assert "430 merged PRs" in text
    # honest empty-questions branch
    assert "No external reviewer questions are on the ledger yet" in text


# --------------------------------------------------------------------------- #
# (b) editions.py parses + lists the generated file (round-trip contract)
# --------------------------------------------------------------------------- #
def test_generated_edition_round_trips_through_editions(tmp_path):
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    slug = gen_edition.slug_for("2026-07-21", 2)
    (reviews / f"{slug}.md").write_text(
        gen_edition.render_edition(2, "2026-07-21", _mirrors()), encoding="utf-8"
    )
    got = editions.list_editions(reviews)
    assert [e["slug"] for e in got] == [slug]
    e = editions.get_edition(slug, reviews)
    assert e is not None
    assert e["title"].startswith("Edition 2")
    assert e["date"] == "2026-07-21"
    assert e["summary"]
    # house rule: every claim cites evidence — the body links committed files
    assert "github.com/menno420/websites" in e["body_md"]


def test_generated_edition_parse_is_not_none():
    slug = gen_edition.slug_for("2026-07-21", 2)
    text = gen_edition.render_edition(2, "2026-07-21", _mirrors())
    assert editions.parse_edition(text, slug) is not None


# --------------------------------------------------------------------------- #
# (c) Idempotent — same (date, number, mirrors) → byte-identical output
# --------------------------------------------------------------------------- #
def test_render_is_idempotent():
    a = gen_edition.render_edition(2, "2026-07-21", _mirrors())
    b = gen_edition.render_edition(2, "2026-07-21", _mirrors())
    assert a == b
    # no wall-clock leakage: the rendered file carries only the mirror's own
    # generated_at stamps and the edition's argument date, never "now".
    assert a.count("2026-07-21") >= 1


def test_slug_and_number_format():
    assert gen_edition.slug_for("2026-07-21", 2) == "2026-07-21-edition-002"
    assert gen_edition.slug_for("2026-01-01", 12) == "2026-01-01-edition-012"


# --------------------------------------------------------------------------- #
# (d) Fail-soft — a missing mirror drops its section, never crashes
# --------------------------------------------------------------------------- #
def test_render_fail_soft_when_mirror_absent():
    # every mirror missing: still a valid, parseable edition (just leaner)
    empty = {name: None for name in gen_edition.MIRRORS}
    text = gen_edition.render_edition(2, "2026-07-21", empty)
    assert editions.parse_edition(text, "2026-07-21-edition-002") is not None
    # sections whose mirror is gone are simply absent
    assert "The window in one line" not in text
    assert "Repositories:" not in text
    # a partial set still renders the sections it can support
    partial = {name: None for name in gen_edition.MIRRORS}
    partial["releases"] = RELEASES
    t2 = gen_edition.render_edition(2, "2026-07-21", partial)
    assert "Release drift:" in t2
    assert editions.parse_edition(t2, "2026-07-21-edition-002") is not None


def test_load_mirror_fail_soft_on_missing_and_malformed(tmp_path):
    # missing file → None
    assert gen_edition.load_mirror(tmp_path, "stats") is None
    # malformed JSON → None (never raises)
    (tmp_path / "stats.json").write_text("{ not json", encoding="utf-8")
    assert gen_edition.load_mirror(tmp_path, "stats") is None
    # well-formed → dict
    (tmp_path / "fleet.json").write_text(json.dumps(FLEET), encoding="utf-8")
    assert gen_edition.load_mirror(tmp_path, "fleet") == FLEET


# --------------------------------------------------------------------------- #
# main — writes the slug'd file from a data dir, honest about mirrors present
# --------------------------------------------------------------------------- #
def test_main_writes_edition_file(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    for name, obj in _mirrors().items():
        (data / f"{name}.json").write_text(json.dumps(obj), encoding="utf-8")
    reviews = tmp_path / "reviews"
    rc = gen_edition.main([
        "--date", "2026-07-21", "--number", "2",
        "--data-dir", str(data), "--reviews-dir", str(reviews),
    ])
    assert rc == 0
    out = reviews / "2026-07-21-edition-002.md"
    assert out.exists()
    assert editions.get_edition("2026-07-21-edition-002", reviews) is not None


def test_main_rejects_bad_date(tmp_path):
    assert gen_edition.main(["--date", "not-a-date", "--reviews-dir", str(tmp_path)]) == 2
