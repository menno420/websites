"""gen_snapshot.py — the repo-numbers bake. Network-free and git-free here:
every test drives the pure transform directly or stubs the ``_git`` seam (and
the higher-level git/IO helpers) with canned output, so nothing shells out.
Expectations are derived from the generator's own code, never invented; dates
are fixed in the PAST relative to any wall clock, so the ``partial``/today
branch never time-bombs."""

from __future__ import annotations

import json
import re
import subprocess

from review import gen_snapshot


# ---------------------------------------------------------------------------
# _utc_date — any-offset commit timestamp → its UTC calendar date
# ---------------------------------------------------------------------------

def test_utc_date_normalizes_offset_to_utc_calendar_day():
    # 23:30 at -05:00 is 04:30 the NEXT day in UTC — the date must roll over
    assert gen_snapshot._utc_date("2026-07-13T23:30:00-05:00") == "2026-07-14"
    # a UTC stamp keeps its own day
    assert gen_snapshot._utc_date("2026-07-13T02:00:00+00:00") == "2026-07-13"
    # an eastern offset can roll the date BACK
    assert gen_snapshot._utc_date("2026-07-14T01:00:00+05:00") == "2026-07-13"


# ---------------------------------------------------------------------------
# commit_and_pr_days — per-day commit + unique-merged-PR rollups
# ---------------------------------------------------------------------------

def _fake_log(monkeypatch, text: str) -> None:
    monkeypatch.setattr(gen_snapshot, "_git", lambda *a: text)


def test_commit_and_pr_days_counts_commits_and_dedupes_prs_newest_first(monkeypatch):
    # history is newest-first; PR #42 is sighted on 07-14 (merge) and again on
    # 07-13 (the original commit) — it must count ONCE, on the merge date.
    log = "\n".join([
        "2026-07-14T10:00:00+00:00\x1fFix the thing (#42)",
        "2026-07-14T09:00:00+00:00\x1fMerge pull request #40 from feature/x",
        "2026-07-13T12:00:00+00:00\x1fAdd the thing (#42)",
        "2026-07-13T08:00:00+00:00\x1fplain commit, no PR ref",
        "a malformed line with no separator",  # skipped
    ])
    _fake_log(monkeypatch, log)
    commits, prs, total_commits, total_prs = gen_snapshot.commit_and_pr_days()
    assert commits == {"2026-07-14": 2, "2026-07-13": 2}
    # #42 deduped onto its merge day (07-14); #40 merge-ref also on 07-14
    assert prs == {"2026-07-14": 2}
    assert total_commits == 4  # the separator-less line is not a commit
    assert total_prs == 2  # two unique PR numbers seen


def test_commit_and_pr_days_empty_history_is_all_zero(monkeypatch):
    _fake_log(monkeypatch, "")
    commits, prs, total_commits, total_prs = gen_snapshot.commit_and_pr_days()
    assert commits == {} and prs == {}
    assert total_commits == 0 and total_prs == 0


# ---------------------------------------------------------------------------
# session_cards_per_day — .sessions/*.md filenames → per-day counts
# ---------------------------------------------------------------------------

def test_session_cards_per_day_counts_dated_cards_and_skips_readme(monkeypatch, tmp_path):
    sess = tmp_path / ".sessions"
    sess.mkdir()
    for name in (
        "2026-07-14-alpha.md",
        "2026-07-14-beta.md",
        "2026-07-13-gamma.md",
        "README.md",            # explicitly skipped
        "no-date-prefix.md",    # no YYYY-MM-DD- prefix → not counted
    ):
        (sess / name).write_text("x", encoding="utf-8")
    monkeypatch.setattr(gen_snapshot, "REPO_ROOT", tmp_path)
    cards, total = gen_snapshot.session_cards_per_day()
    assert cards == {"2026-07-14": 2, "2026-07-13": 1}
    assert total == 3


def test_session_cards_per_day_empty_dir_is_zero(monkeypatch, tmp_path):
    (tmp_path / ".sessions").mkdir()
    monkeypatch.setattr(gen_snapshot, "REPO_ROOT", tmp_path)
    assert gen_snapshot.session_cards_per_day() == ({}, 0)


# ---------------------------------------------------------------------------
# test_functions_at — git grep -c tally, honest-fail path
# ---------------------------------------------------------------------------

def test_test_functions_at_sums_per_file_counts(monkeypatch):
    monkeypatch.setattr(
        gen_snapshot, "_git",
        lambda *a: "tests/test_a.py:3\nreview/tests/test_b.py:5\nbotsite/tests/test_c.py:2\n",
    )
    assert gen_snapshot.test_functions_at("HEAD") == 10


def test_test_functions_at_returns_zero_when_grep_finds_nothing(monkeypatch):
    def _raise(*a):
        raise subprocess.CalledProcessError(1, "git grep")
    monkeypatch.setattr(gen_snapshot, "_git", _raise)
    # git grep exits non-zero on no match — that is 0 tests, never a crash
    assert gen_snapshot.test_functions_at("HEAD") == 0


# ---------------------------------------------------------------------------
# main — bakes snapshot.json with the right shape and totals
# ---------------------------------------------------------------------------

def test_main_bakes_snapshot_with_days_and_totals(monkeypatch, tmp_path):
    # 07-13 is fixed in the past relative to any wall clock, so no row ever
    # picks up the today-only "partial" marker — deterministic forever.
    monkeypatch.setattr(
        gen_snapshot, "commit_and_pr_days",
        lambda: ({"2026-07-13": 2}, {"2026-07-13": 1}, 2, 1),
    )
    monkeypatch.setattr(
        gen_snapshot, "session_cards_per_day", lambda: ({"2026-07-13": 1}, 1)
    )
    monkeypatch.setattr(gen_snapshot, "_git", lambda *a: "deadbeef\n")
    monkeypatch.setattr(gen_snapshot, "eod_commit", lambda day: f"sha-{day}")
    monkeypatch.setattr(gen_snapshot, "test_functions_at", lambda ref: 100)
    # OUT_PATH must sit under REPO_ROOT — main() prints its relative path
    monkeypatch.setattr(gen_snapshot, "REPO_ROOT", tmp_path)
    out = tmp_path / "data" / "snapshot.json"
    monkeypatch.setattr(gen_snapshot, "OUT_PATH", out)

    gen_snapshot.main()

    snap = json.loads(out.read_text(encoding="utf-8"))
    assert snap["git_head"] == "deadbeef"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", snap["generated_at"])
    assert snap["days"] == [{
        "date": "2026-07-13",
        "prs_merged": 1,
        "commits": 2,
        "session_cards": 1,
        "test_functions_eod": 100,
    }]
    assert snap["totals"] == {
        "prs_merged": 1,
        "commits": 2,
        "session_cards": 1,
        "test_functions": 100,
        "services": 4,
    }
