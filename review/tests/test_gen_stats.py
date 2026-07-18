"""gen_stats.py — the per-repo REST stats bake. Every test stubs the single
network seam (``_api``) with canned ``(body, headers, reason)`` tuples, or
stubs ``repo_stats`` wholesale for the ``main`` fail-soft paths — no live
GitHub call, no token read that could vary by runner. Expectations are derived
from the generator's own code (the Link-header last-page grammar, the fail-soft
write discipline)."""

from __future__ import annotations

import json

from review import gen_stats


# ---------------------------------------------------------------------------
# total_prs — the Link header's last page IS the total PR count
# ---------------------------------------------------------------------------

def _api_const(result):
    return lambda path: result


def test_total_prs_reads_the_last_page_from_the_link_header(monkeypatch):
    link = (
        '<https://api.github.com/repositories/1/pulls?state=all&per_page=1&page=2>; rel="next", '
        '<https://api.github.com/repositories/1/pulls?state=all&per_page=1&page=42>; rel="last"'
    )
    monkeypatch.setattr(gen_stats, "_api", _api_const(([{}], {"Link": link}, "")))
    count, err = gen_stats.total_prs("websites")
    assert count == 42 and err == ""


def test_total_prs_no_link_header_falls_back_to_body_length(monkeypatch):
    # no Link header ⇒ zero or one PR total; the returned body length is it
    monkeypatch.setattr(gen_stats, "_api", _api_const(([{"n": 1}], {}, "")))
    assert gen_stats.total_prs("websites") == (1, "")
    monkeypatch.setattr(gen_stats, "_api", _api_const(([], {}, "")))
    assert gen_stats.total_prs("websites") == (0, "")


def test_total_prs_propagates_the_api_error(monkeypatch):
    monkeypatch.setattr(gen_stats, "_api", _api_const((None, {}, "HTTP 403")))
    assert gen_stats.total_prs("websites") == (None, "HTTP 403")


# ---------------------------------------------------------------------------
# repo_stats — the two-call per-repo record, honest on failure
# ---------------------------------------------------------------------------

def _two_call_api(meta, pulls):
    """Dispatch on path: the /pulls call vs the repo-metadata call."""
    def _api(path):
        return pulls if "/pulls" in path else meta
    return _api


def test_repo_stats_normal_record_shape(monkeypatch):
    meta = (
        {
            "pushed_at": "2026-07-14T10:00:00Z",
            "created_at": "2026-01-01T00:00:00Z",
            "description": "the control plane",
            "open_issues_count": 5,
            "default_branch": "main",
        },
        {},
        "",
    )
    link = '<https://api.github.com/x?page=7>; rel="last"'
    pulls = ([{}], {"Link": link}, "")
    monkeypatch.setattr(gen_stats, "_api", _two_call_api(meta, pulls))
    out = gen_stats.repo_stats("websites")
    assert out == {
        "ok": True,
        "pushed_at": "2026-07-14T10:00:00Z",
        "created_at": "2026-01-01T00:00:00Z",
        "description": "the control plane",
        "open_issues_and_prs": 5,
        "default_branch": "main",
        "total_prs": 7,
    }


def test_repo_stats_metadata_failure_is_honest(monkeypatch):
    monkeypatch.setattr(gen_stats, "_api", _api_const((None, {}, "HTTP 404")))
    out = gen_stats.repo_stats("gone-repo")
    assert out == {"ok": False, "reason": "HTTP 404"}


def test_repo_stats_records_pr_count_failure_without_dropping_the_repo(monkeypatch):
    meta = ({"pushed_at": "2026-07-14T10:00:00Z", "open_issues_count": 2}, {}, "")
    pulls = (None, {}, "HTTP 403")  # the PR-count call alone fails
    monkeypatch.setattr(gen_stats, "_api", _two_call_api(meta, pulls))
    out = gen_stats.repo_stats("websites")
    assert out["ok"] is True
    assert "total_prs" not in out
    assert out["total_prs_reason"] == "HTTP 403"


# ---------------------------------------------------------------------------
# main — fail-soft loader + write discipline against fleet.json
# ---------------------------------------------------------------------------

def test_main_unreadable_fleet_skips_and_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(gen_stats, "FLEET_PATH", tmp_path / "nope.json")
    out = tmp_path / "stats.json"
    monkeypatch.setattr(gen_stats, "OUT_PATH", out)
    assert gen_stats.main() == 0
    assert not out.exists()  # fail-soft: no stats file conjured


def test_main_no_repo_backed_lanes_skips(monkeypatch, tmp_path):
    fleet = tmp_path / "fleet.json"
    fleet.write_text(json.dumps({"lanes": []}), encoding="utf-8")
    monkeypatch.setattr(gen_stats, "FLEET_PATH", fleet)
    out = tmp_path / "stats.json"
    monkeypatch.setattr(gen_stats, "OUT_PATH", out)
    assert gen_stats.main() == 0
    assert not out.exists()


def test_main_all_failed_does_not_write_a_stats_file(monkeypatch, tmp_path):
    fleet = tmp_path / "fleet.json"
    fleet.write_text(json.dumps({"lanes": [{"repo": "a"}, {"repo": "b"}]}),
                     encoding="utf-8")
    monkeypatch.setattr(gen_stats, "FLEET_PATH", fleet)
    out = tmp_path / "stats.json"
    monkeypatch.setattr(gen_stats, "OUT_PATH", out)
    monkeypatch.setattr(gen_stats, "repo_stats",
                        lambda repo: {"ok": False, "reason": "HTTP 403"})
    assert gen_stats.main() == 0
    # an all-failed run writes nothing — honest absence beats faking GitHub's voice
    assert not out.exists()


def test_main_writes_stats_for_the_repos_that_succeeded(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)  # deterministic auth label
    fleet = tmp_path / "fleet.json"
    fleet.write_text(json.dumps({"lanes": [{"repo": "a"}, {"repo": "b"}]}),
                     encoding="utf-8")
    monkeypatch.setattr(gen_stats, "FLEET_PATH", fleet)
    out = tmp_path / "stats.json"
    monkeypatch.setattr(gen_stats, "OUT_PATH", out)
    monkeypatch.setattr(
        gen_stats, "repo_stats",
        lambda repo: {"ok": True, "pushed_at": "2026-07-14T10:00:00Z", "total_prs": 3},
    )
    assert gen_stats.main() == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert set(doc["repos"]) == {"a", "b"}
    assert doc["repos"]["a"]["total_prs"] == 3
    assert doc["auth"] == "anonymous (60 req/h ceiling)"
    assert doc["generated_at"].endswith("Z")
