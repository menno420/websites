"""Pure tests for the stable estate domain and /repos list contract."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app import listfilter
from app.estate import (
    NEXT_THREAD_UNKNOWN,
    REPOS_LIST_SPEC,
    Activity,
    EstateOverview,
    Freshness,
    FreshnessState,
    OwnerCommentSummary,
    RepositoryDetail,
    RepositoryStatus,
    RepositorySummary,
    SourceReference,
    normalize_repository_status,
)

UTC = timezone.utc
NOW = datetime(2026, 8, 27, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("raw", "section", "expected"),
    [
        ("active — shipping", "Active — current work", RepositoryStatus.ACTIVE),
        ("paused by owner", "Paused / owner-gated", RepositoryStatus.PAUSED),
        ("complete-parked", "Paused / owner-gated", RepositoryStatus.PAUSED),
        ("frozen behavior oracle", "Frozen experiments", RepositoryStatus.FROZEN),
        (
            "infrastructure, dormant between asks",
            "Active — current work",
            RepositoryStatus.INFRASTRUCTURE,
        ),
        ("📦 ARCHIVED 2026-08-23", "Paused", RepositoryStatus.ARCHIVED),
        ("opaque wording", "", RepositoryStatus.UNKNOWN),
    ],
)
def test_status_normalizes_current_ledger_shapes(raw, section, expected):
    result = normalize_repository_status(raw, section=section)
    assert result.status is expected
    assert result.raw_status == raw


def test_explicit_frozen_state_beats_active_section_and_warns():
    result = normalize_repository_status(
        "frozen behavior/UX oracle — maintenance only",
        section="Active — where work actually goes now",
    )
    assert result.status is RepositoryStatus.FROZEN
    assert any("section suggests active" in warning for warning in result.warnings)


def test_live_archived_true_overrides_older_active_wording():
    result = normalize_repository_status(
        "active — work continues", section="Active", live_archived=True
    )
    assert result.status is RepositoryStatus.ARCHIVED
    assert result.raw_status == "active — work continues"
    assert any("Live GitHub state is archived" in warning for warning in result.warnings)


def test_live_not_archived_overrides_stale_archive_wording():
    result = normalize_repository_status(
        "📦 ARCHIVED 2026-08-23",
        section="Paused / owner-gated",
        live_archived=False,
    )
    assert result.status is RepositoryStatus.PAUSED
    assert any("live GitHub state is not archived" in w for w in result.warnings)


def test_status_surfaces_cross_source_contradiction():
    result = normalize_repository_status(
        "active",
        section="Active",
        additional_raw_statuses=("paused by owner", "active and healthy"),
    )
    assert result.status is RepositoryStatus.ACTIVE
    assert result.warnings == ("Another source says paused: paused by owner",)


def test_live_freshness_has_separate_retrieval_and_fact_fields():
    fresh = Freshness.live(NOW)
    assert fresh.state is FreshnessState.LIVE
    assert fresh.is_live and not fresh.is_stale
    assert fresh.retrieved_at == NOW
    assert fresh.fact_as_of == NOW
    assert fresh.label == "Live"
    assert fresh.retrieval_label == "Retrieved 2026-08-27 12:00 UTC"


def test_fresh_download_of_old_fact_stays_measured_not_live():
    fact_time = NOW - timedelta(hours=6)
    fresh = Freshness.measured(fact_time, retrieved_at=NOW, now=NOW)
    assert fresh.state is FreshnessState.MEASURED
    assert fresh.retrieved_at == NOW
    assert fresh.fact_as_of == fact_time
    assert fresh.age_hours == 6
    assert fresh.label == "Measured 6 hours ago"


def test_measured_stale_threshold_is_strictly_after_fourteen_days():
    boundary = Freshness.measured(NOW - timedelta(days=14), now=NOW)
    stale = Freshness.measured(
        NOW - timedelta(days=14, seconds=1), now=NOW
    )
    assert boundary.state is FreshnessState.MEASURED
    assert stale.state is FreshnessState.STALE
    assert stale.label == "Stale"
    assert stale.detail == "Measured 14 days ago"


def test_last_verified_keeps_date_semantics_when_fresh_or_stale():
    recent = Freshness.last_verified(date(2026, 8, 20), now=NOW)
    old = Freshness.last_verified(date(2026, 8, 1), now=NOW)
    assert recent.state is FreshnessState.LAST_VERIFIED
    assert recent.label == "Last verified 2026-08-20"
    assert old.state is FreshnessState.STALE
    assert old.detail == "Last verified 2026-08-01"


def test_unknown_and_unavailable_are_explicit_and_explainable():
    unknown = Freshness.unknown(reason="No dated source", now=NOW)
    unavailable = Freshness.unavailable(reason="Private source", now=NOW)
    assert unknown.state is FreshnessState.UNKNOWN
    assert unknown.detail == "No dated source"
    assert unknown.age is None
    assert unavailable.state is FreshnessState.UNAVAILABLE
    assert unavailable.label == "Unavailable"
    assert unavailable.detail == "Private source"
    assert not unavailable.is_available


def test_naive_timestamps_are_normalized_to_utc():
    fresh = Freshness.measured(
        datetime(2026, 8, 27, 10),
        retrieved_at=datetime(2026, 8, 27, 12),
        now=NOW,
    )
    assert fresh.fact_as_of.tzinfo == UTC
    assert fresh.retrieved_at.tzinfo == UTC
    assert fresh.age_hours == 2


def test_comment_unknown_is_not_zero():
    unknown = OwnerCommentSummary()
    zero = OwnerCommentSummary(
        unconsumed_count=0,
        consumed_count=0,
        freshness=Freshness.live(NOW),
    )
    assert unknown.is_known is False
    assert unknown.total_count is None
    assert unknown.has_comments is None
    assert unknown.label == "Comments unknown"
    assert zero.is_known is True
    assert zero.total_count == 0
    assert zero.has_comments is False
    assert zero.label == "No owner comments"


def test_comment_summary_distinguishes_open_consumed_and_partial_history():
    open_comments = OwnerCommentSummary(2, 3, Freshness.live(NOW))
    consumed = OwnerCommentSummary(0, 1, Freshness.live(NOW))
    partial = OwnerCommentSummary(0, None, Freshness.live(NOW))
    assert open_comments.has_unconsumed is True
    assert open_comments.has_comments is True
    assert open_comments.label == "2 owner comments awaiting action"
    assert consumed.label == "1 owner comment consumed"
    assert partial.has_comments is None
    assert partial.label == "No unconsumed comments · history unknown"


def test_negative_comment_counts_are_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        OwnerCommentSummary(unconsumed_count=-1)


def _comments(open_count: int = 0, consumed_count: int = 0):
    return OwnerCommentSummary(
        open_count,
        consumed_count,
        Freshness.live(NOW),
    )


def _repo(
    name: str,
    status: RepositoryStatus,
    *,
    purpose: str = "",
    warnings=(),
    activity_at=None,
    comments=None,
    indexed=True,
):
    activities = ()
    if activity_at is not None:
        activities = (
            Activity(
                f"{name} moved",
                activity_at,
                freshness=Freshness.measured(activity_at, now=NOW),
            ),
        )
    return RepositorySummary(
        name=name,
        purpose=purpose,
        status=status,
        raw_status=status.value,
        freshness=Freshness.live(NOW),
        activities=activities,
        owner_comments=comments if comments is not None else _comments(),
        warnings=warnings,
        indexed_by_fleet_manager=indexed,
        github_present=True,
    )


def test_repository_activity_attention_and_template_properties():
    recent = _repo(
        "spider-bot",
        RepositoryStatus.ACTIVE,
        purpose="community bot",
        activity_at=NOW - timedelta(days=2),
    )
    old = _repo(
        "venture-lab",
        RepositoryStatus.PAUSED,
        activity_at=NOW - timedelta(days=30),
        warnings=("Member state contradicts ledger.",),
    )
    assert recent.recently_active
    assert not recent.needs_attention
    assert recent.url == "/repos/spider-bot"
    assert recent.status_label == "Active"
    assert "recently-active" in recent.signal_values
    assert not old.recently_active
    assert old.needs_attention
    assert "needs-attention" in old.signal_values


def test_unindexed_repository_and_open_comment_are_attention_signals():
    repo = _repo(
        "new-repo",
        RepositoryStatus.UNKNOWN,
        indexed=False,
        comments=_comments(1, 0),
    )
    assert repo.needs_attention
    assert repo.owner_comments.label in repo.attention_reasons
    assert any("not yet indexed" in reason for reason in repo.attention_reasons)
    assert set(repo.signal_values) == {"needs-attention", "has-owner-comments"}


def test_source_reference_preserves_provenance_and_availability():
    source = SourceReference(
        "Fleet Manager Layer 2",
        "https://github.com/menno420/fleet-manager/blob/main/docs/repos/websites/README.md",
        repository="fleet-manager",
        path="docs/repos/websites/README.md",
        authority="authoritative",
        freshness=Freshness.last_verified(date(2026, 8, 26), now=NOW),
    )
    assert source.repo == "fleet-manager"
    assert source.location == "fleet-manager/docs/repos/websites/README.md"
    assert source.is_authoritative
    assert source.availability_label == "Available"


def test_repository_detail_uses_exact_honest_next_thread_fallback():
    summary = _repo("websites", RepositoryStatus.ACTIVE)
    missing = RepositoryDetail(summary)
    established = RepositoryDetail(summary, current_next_thread="Ship /repos")
    assert missing.current_next_thread_text == NEXT_THREAD_UNKNOWN
    assert established.current_next_thread_text == "Ship /repos"


def test_estate_overview_counts_and_case_insensitive_lookup():
    overview = EstateOverview(
        repositories=(
            _repo("Alpha", RepositoryStatus.ACTIVE),
            _repo("infra", RepositoryStatus.INFRASTRUCTURE),
            _repo(
                "beta",
                RepositoryStatus.PAUSED,
                warnings=("attention",),
            ),
        ),
        freshness=Freshness.live(NOW),
    )
    assert overview.counts_by_status["active"] == 1
    assert overview.counts_by_status["infrastructure"] == 1
    assert overview.counts_by_status["archived"] == 0
    assert overview.attention_count == 1
    assert overview.repository("ALPHA").name == "Alpha"
    assert overview.repository("missing") is None


def _filter_items():
    return [
        _repo(
            "alpha",
            RepositoryStatus.ACTIVE,
            purpose="physics game",
            activity_at=NOW - timedelta(days=1),
        ),
        _repo(
            "beta",
            RepositoryStatus.PAUSED,
            purpose="commerce lane",
            warnings=("Needs reconciliation",),
            comments=_comments(1, 2),
            activity_at=NOW - timedelta(days=20),
        ),
        _repo(
            "kit",
            RepositoryStatus.INFRASTRUCTURE,
            purpose="shared method kit",
        ),
        _repo("old-tool", RepositoryStatus.ARCHIVED, purpose="finished CLI"),
    ]


@pytest.mark.parametrize(
    ("params", "names"),
    [
        ({"state": "active"}, ["alpha"]),
        ({"state": "paused"}, ["beta"]),
        ({"state": "infrastructure"}, ["kit"]),
        ({"state": "archived"}, ["old-tool"]),
        ({"signal": "recently-active"}, ["alpha"]),
        ({"signal": "needs-attention"}, ["beta"]),
        ({"signal": "has-owner-comments"}, ["beta"]),
        ({"state": "paused", "signal": "has-owner-comments"}, ["beta"]),
        ({"q": "PHYSICS"}, ["alpha"]),
        ({"q": "shared method"}, ["kit"]),
    ],
)
def test_repos_list_spec_supports_requested_filters_and_search(params, names):
    state = listfilter.parse(REPOS_LIST_SPEC, params)
    view = listfilter.apply(REPOS_LIST_SPEC, _filter_items(), state)
    assert [repository.name for repository in view["items"]] == names


def test_signal_filter_is_or_within_signal_dimension():
    state = listfilter.parse(
        REPOS_LIST_SPEC,
        {"signal": ["recently-active", "has-owner-comments"]},
    )
    view = listfilter.apply(REPOS_LIST_SPEC, _filter_items(), state)
    assert {repository.name for repository in view["items"]} == {"alpha", "beta"}


def test_repos_list_sorts_attention_recent_az_and_state():
    items = _filter_items()
    expected = {
        "attention": ["beta", "alpha", "kit", "old-tool"],
        "recent": ["alpha", "beta", "kit", "old-tool"],
        "az": ["alpha", "beta", "kit", "old-tool"],
        "state": ["alpha", "kit", "beta", "old-tool"],
    }
    for sort, names in expected.items():
        state = listfilter.parse(REPOS_LIST_SPEC, {"sort": sort})
        view = listfilter.apply(REPOS_LIST_SPEC, items, state)
        assert [repository.name for repository in view["items"]] == names
