"""gen_releases.py — the release-drift bake. Every test drives a PURE
transform (``parse_arcade`` / ``parse_ls_remote_tags`` / ``pick_latest_tag`` /
``compute_drift`` / ``bake``) or the fail-soft ``main`` paths with the one
network seam (the injected ``tag_fetcher`` / the module ``fetch_tags``) stubbed
— no live git transport. Time is frozen by monkeypatching the module clock so
the generated stamp is deterministic (the repo's 08:45Z clock-freeze lesson)."""

from __future__ import annotations

import datetime as dt
import json

from review import gen_releases


# A frozen clock so bake()'s generated_at is deterministic under test.
class _FrozenDT(dt.datetime):
    @classmethod
    def now(cls, tz=None):  # noqa: A003 — matches datetime.now signature
        return dt.datetime(2026, 7, 18, 12, 0, 0, tzinfo=tz or dt.timezone.utc)


def _freeze(monkeypatch):
    monkeypatch.setattr(gen_releases, "datetime", _FrozenDT)


# A minimal arcade.json text: one game whose registry free text encodes an
# expected release tag (lumen-drift-v1.3), one whose text encodes none, and one
# with NO source_repo (must be dropped — nothing to drift against).
_ARCADE_TEXT = json.dumps([
    {
        "slug": "lumen-drift",
        "name": "Lumen Drift",
        "maturity": "playable",
        "availability": "unavailable",
        "url": None,
        "source_repo": "menno420/gba-homebrew",
        "status_note": "Download release pending: the GitHub Release (lumen-drift-v1.3) needs one owner click.",
        "blocker": {
            "owner_action": "Publish the GitHub Release lumen-drift-v1.3 in menno420/gba-homebrew.",
            "unblocks": "gives the ROM a public download URL",
            "ask_id": "ASK-0010",
        },
    },
    {
        "slug": "mineverse",
        "name": "mineverse",
        "maturity": "beta",
        "availability": "live",
        "url": "https://example.invalid",
        "source_repo": "menno420/superbot-mineverse",
        "status_note": "Read-only demo — player sign-in launching.",
    },
    {
        "slug": "no-repo-game",
        "name": "No Repo Game",
        "maturity": "beta",
        "availability": "unavailable",
        "url": None,
        # no source_repo key at all → excluded by parse_arcade
    },
])


# ---------------------------------------------------------------------------
# parse_arcade — per-game {slug, name, source_repo, expected_tag}
# ---------------------------------------------------------------------------

def test_parse_arcade_extracts_repo_backed_games_and_expected_tags():
    games = gen_releases.parse_arcade(_ARCADE_TEXT)
    # the no-source_repo entry is dropped
    assert [g["slug"] for g in games] == ["lumen-drift", "mineverse"]
    lumen = games[0]
    assert lumen["name"] == "Lumen Drift"
    assert lumen["source_repo"] == "menno420/gba-homebrew"
    # the tag is read from the blocker/status free text (no structured field)
    assert lumen["expected_tag"] == "lumen-drift-v1.3"
    # a game whose text encodes no release tag records None (never guessed)
    assert games[1]["expected_tag"] is None


def test_parse_arcade_prefers_owner_action_then_status_note():
    text = json.dumps([
        {"slug": "g", "name": "G", "source_repo": "o/r",
         "status_note": "note mentions g-v2.0",
         "blocker": {"owner_action": "Publish g-v9.9", "unblocks": "x"}},
    ])
    # owner_action wins over status_note
    assert gen_releases.parse_arcade(text)[0]["expected_tag"] == "g-v9.9"


def test_parse_arcade_ignores_bare_version_in_prose():
    # a bare "(v1.3)" with no <name>-v boundary is NOT a tag
    text = json.dumps([
        {"slug": "g", "name": "G", "source_repo": "o/r",
         "description": "a finished ROM (v1.3)", "status_note": "no tag here"},
    ])
    assert gen_releases.parse_arcade(text)[0]["expected_tag"] is None


def test_parse_arcade_malformed_input_is_empty_list():
    assert gen_releases.parse_arcade("not json") == []
    assert gen_releases.parse_arcade("") == []
    assert gen_releases.parse_arcade(json.dumps({"not": "a list"})) == []
    # a list of non-dicts / dicts without source_repo yields nothing
    assert gen_releases.parse_arcade(json.dumps(["x", {"slug": "no-repo"}])) == []


# ---------------------------------------------------------------------------
# parse_ls_remote_tags — git ls-remote --tags stdout → tag names
# ---------------------------------------------------------------------------

def test_parse_ls_remote_tags_strips_peel_suffix_and_dedupes():
    out = (
        "1111111111111111111111111111111111111111\trefs/tags/lumen-drift-v1.0\n"
        "2222222222222222222222222222222222222222\trefs/tags/lumen-drift-v1.3\n"
        "3333333333333333333333333333333333333333\trefs/tags/lumen-drift-v1.3^{}\n"  # peeled annotated tag
        "not-a-tag-line\n"
    )
    tags = gen_releases.parse_ls_remote_tags(out)
    assert tags == ["lumen-drift-v1.0", "lumen-drift-v1.3"]


def test_parse_ls_remote_tags_empty_is_empty():
    assert gen_releases.parse_ls_remote_tags("") == []
    assert gen_releases.parse_ls_remote_tags("garbage\nlines\n") == []


# ---------------------------------------------------------------------------
# pick_latest_tag — family filter + natural, version-aware sort
# ---------------------------------------------------------------------------

def test_pick_latest_tag_prefers_family_and_sorts_naturally():
    tags = ["lumen-drift-v1.9", "lumen-drift-v1.10", "other-game-v5.0"]
    # v1.10 > v1.9 (numeric, not lexicographic), and the other game's tag is
    # excluded by the slug-family filter
    assert gen_releases.pick_latest_tag(tags, "lumen-drift") == "lumen-drift-v1.10"


def test_pick_latest_tag_falls_back_to_all_tags_when_family_empty():
    tags = ["v1.0", "v2.0"]
    assert gen_releases.pick_latest_tag(tags, "lumen-drift") == "v2.0"


def test_pick_latest_tag_none_when_no_tags():
    assert gen_releases.pick_latest_tag([], "lumen-drift") is None


# ---------------------------------------------------------------------------
# compute_drift — the pure expected-vs-live core
# ---------------------------------------------------------------------------

def test_compute_drift_true_when_expected_missing_live():
    drift, reason = gen_releases.compute_drift("lumen-drift-v1.3", None)
    assert drift is True
    assert "not published" in reason and "lumen-drift-v1.3" in reason


def test_compute_drift_true_when_tags_differ():
    drift, reason = gen_releases.compute_drift("g-v2.0", "g-v1.0")
    assert drift is True
    assert "g-v2.0" in reason and "g-v1.0" in reason


def test_compute_drift_false_when_tags_match():
    drift, reason = gen_releases.compute_drift("g-v2.0", "g-v2.0")
    assert drift is False and "matches" in reason


def test_compute_drift_false_when_expected_unknown():
    drift, reason = gen_releases.compute_drift(None, "g-v2.0")
    assert drift is False and "no release tag" in reason


# ---------------------------------------------------------------------------
# bake — pure, with an injected tag fetcher (drift / no-drift / unknown / fail)
# ---------------------------------------------------------------------------

def test_bake_flags_the_canonical_unpublished_release_drift(monkeypatch):
    _freeze(monkeypatch)
    # gba-homebrew reachable, but no lumen-drift release tag published (the real
    # canonical case: ls-remote --tags succeeds with no matching tag) → drift
    fetch = lambda repo: ([], "")
    doc = gen_releases.bake(_ARCADE_TEXT, fetch)
    assert doc["generated_at"] == "2026-07-18T12:00:00Z"
    assert doc["drift_count"] == 1
    lumen = next(e for e in doc["entries"] if e["slug"] == "lumen-drift")
    assert lumen["drift"] is True
    assert lumen["expected_tag"] == "lumen-drift-v1.3"
    assert lumen["live_tag"] is None
    # the tagless game never drifts
    mineverse = next(e for e in doc["entries"] if e["slug"] == "mineverse")
    assert mineverse["drift"] is False


def test_bake_no_drift_when_live_matches_expected(monkeypatch):
    _freeze(monkeypatch)
    fetch = lambda repo: (["lumen-drift-v1.3"], "") if "gba" in repo else ([], "")
    doc = gen_releases.bake(_ARCADE_TEXT, fetch)
    assert doc["drift_count"] == 0
    lumen = next(e for e in doc["entries"] if e["slug"] == "lumen-drift")
    assert lumen["drift"] is False and lumen["live_tag"] == "lumen-drift-v1.3"


def test_bake_flags_drift_when_live_family_tag_is_older(monkeypatch):
    _freeze(monkeypatch)
    # gba-homebrew published lumen-drift-v1.2, but the registry expects v1.3 →
    # the slug-family filter picks v1.2 as this game's live tag, and it differs
    fetch = lambda repo: (["lumen-drift-v1.2"], "") if "gba" in repo else ([], "")
    doc = gen_releases.bake(_ARCADE_TEXT, fetch)
    assert doc["drift_count"] == 1
    lumen = next(e for e in doc["entries"] if e["slug"] == "lumen-drift")
    assert lumen["drift"] is True and lumen["live_tag"] == "lumen-drift-v1.2"


def test_bake_fetch_failure_leaves_drift_undetermined(monkeypatch):
    _freeze(monkeypatch)
    # every fetch fails → no game drifts (a review site never asserts drift on
    # data it could not read), and the reason says so honestly
    fetch = lambda repo: ([], "ls-remote --tags timed out")
    doc = gen_releases.bake(_ARCADE_TEXT, fetch)
    assert doc["drift_count"] == 0
    lumen = next(e for e in doc["entries"] if e["slug"] == "lumen-drift")
    assert lumen["drift"] is False
    assert "drift undetermined" in lumen["reason"]
    assert lumen["live_tag"] is None


# ---------------------------------------------------------------------------
# main — fail-soft (arcade unreadable / total fetch failure keep the file)
# ---------------------------------------------------------------------------

def test_main_writes_an_honest_mirror_on_first_bake(monkeypatch, tmp_path):
    _freeze(monkeypatch)
    out = tmp_path / "releases.json"  # does NOT exist yet
    monkeypatch.setattr(gen_releases, "OUT_PATH", out)
    monkeypatch.setattr(gen_releases, "ARCADE_PATH", tmp_path / "arcade.json")
    (tmp_path / "arcade.json").write_text(_ARCADE_TEXT, encoding="utf-8")
    # gba-homebrew has no published lumen-drift tag → the canonical drift demo
    monkeypatch.setattr(gen_releases, "fetch_tags", lambda repo: ([], ""))
    assert gen_releases.main() == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["generated_at"] == "2026-07-18T12:00:00Z"
    assert doc["drift_count"] == 1
    assert any(e["drift"] for e in doc["entries"])


def test_main_keeps_committed_file_when_arcade_unreadable(monkeypatch, tmp_path):
    out = tmp_path / "releases.json"
    before = '{"generated_at": "2026-07-10T00:00:00Z", "entries": [], "drift_count": 0}\n'
    out.write_text(before, encoding="utf-8")
    monkeypatch.setattr(gen_releases, "OUT_PATH", out)
    monkeypatch.setattr(gen_releases, "ARCADE_PATH", tmp_path / "missing-arcade.json")
    assert gen_releases.main() == 0
    # existing committed file left byte-identical (fail-soft)
    assert out.read_text(encoding="utf-8") == before


def test_main_keeps_committed_file_when_every_fetch_fails(monkeypatch, tmp_path):
    out = tmp_path / "releases.json"
    before = '{"generated_at": "2026-07-10T00:00:00Z", "entries": [], "drift_count": 0}\n'
    out.write_text(before, encoding="utf-8")
    monkeypatch.setattr(gen_releases, "OUT_PATH", out)
    monkeypatch.setattr(gen_releases, "ARCADE_PATH", tmp_path / "arcade.json")
    (tmp_path / "arcade.json").write_text(_ARCADE_TEXT, encoding="utf-8")
    # a total network wall: every game's tags unreadable → don't clobber the
    # last good bake with an all-undetermined mirror
    monkeypatch.setattr(gen_releases, "fetch_tags", lambda repo: ([], "timed out"))
    assert gen_releases.main() == 0
    assert out.read_text(encoding="utf-8") == before
