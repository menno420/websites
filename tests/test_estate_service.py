"""Aggregation tests: raw readers can change without changing the UI model."""

import asyncio
from dataclasses import replace
from datetime import datetime, timezone

from app import estate, estate_reader, estate_service

UTC = timezone.utc


def _result(data=None, *, ok=True, status=200, cached=False, error=""):
    return {
        "ok": ok,
        "status": status,
        "data": data,
        "error": error,
        "fetched_at": "10:00:00 UTC",
        "fetched_at_iso": "2026-08-27T10:00:00Z",
        "cached": cached,
        "url": "https://example.test/source",
    }


def _sources(*, listing_ok=True):
    verified = datetime.now(UTC).date().isoformat()
    rows = (
        estate_reader.EstateRow(
            name="alpha",
            purpose="Alpha product",
            raw_state="active",
            read_first="README.md",
            layer2="[entry](repos/alpha/README.md)",
            layer2_path="docs/repos/alpha/README.md",
            section="Active — current work",
            verified_date=verified,
            source_line=10,
        ),
        estate_reader.EstateRow(
            name="private-tool",
            purpose="PRIVATE internal tool",
            raw_state="infrastructure, dormant",
            read_first="README.md",
            layer2="on demand",
            layer2_path=None,
            section="Active — current work",
            verified_date=verified,
            source_line=11,
        ),
    )
    public = (
        estate_reader.PublicRepository(
            name="alpha",
            description="",
            html_url="https://github.com/menno420/alpha",
            archived=True,
            disabled=False,
            pushed_at="2026-08-27T09:00:00Z",
            updated_at="2026-08-27T09:00:00Z",
            default_branch="main",
            open_issues_count=1,
        ),
        estate_reader.PublicRepository(
            name="new-public",
            description="Newly created public repository",
            html_url="https://github.com/menno420/new-public",
            archived=False,
            disabled=False,
            pushed_at="2026-08-27T08:00:00Z",
            updated_at="2026-08-27T08:00:00Z",
            default_branch="main",
            open_issues_count=0,
        ),
    )
    activity = estate_reader.ActivityParseResult(
        generated_at="2026-08-27 09:30Z",
        in_flight=(),
        sessions=(
            estate_reader.ActivityRecord(
                kind="session",
                repo="alpha",
                date="2026-08-27",
                status="complete",
                venue="chatgpt-work",
                model="GPT-5",
                title="Alpha session",
                detail="",
                source_url="https://github.com/menno420/alpha/blob/main/.sessions/x.md",
                related_url="",
                source_line=20,
            ),
        ),
        invisible_work=(),
    )
    listing_result = (
        _result([{"name": item.name} for item in public])
        if listing_ok
        else _result(None, ok=False, status=503, error="offline")
    )
    return estate_reader.OverviewSources(
        estate_result=_result("estate"),
        activity_result=_result("activity"),
        public_repos_result=listing_result,
        estate=estate_reader.EstateParseResult(rows),
        activity=activity,
        public_repositories=public if listing_ok else (),
        unindexed_public_repositories=(public[1],) if listing_ok else (),
        warnings=(),
    )


def test_aggregation_honours_live_archive_and_surfaces_unindexed_public():
    model, rows, public = estate_service._aggregate(_sources())
    alpha = model.repository("alpha")
    assert alpha is not None
    assert alpha.status is estate.RepositoryStatus.ARCHIVED
    assert alpha.status_freshness.state is estate.FreshnessState.LIVE
    assert alpha.status_source.label == "Public GitHub repository metadata"
    assert any("GitHub state is archived" in warning for warning in alpha.warnings)
    assert alpha.last_activity_at == datetime(2026, 8, 27, 9, tzinfo=UTC)
    assert alpha.freshness.state in {
        estate.FreshnessState.LAST_VERIFIED,
        estate.FreshnessState.STALE,
    }
    unindexed = model.repository("new-public")
    assert unindexed is not None and not unindexed.indexed_by_fleet_manager
    assert unindexed.status is estate.RepositoryStatus.UNKNOWN
    assert unindexed.status_freshness.state is estate.FreshnessState.UNKNOWN
    assert unindexed.purpose_text == "Purpose not confidently established."
    assert "not yet indexed" in unindexed.attention_reasons[0]
    assert set(rows) == {"alpha", "private-tool"}
    assert set(public) == {"alpha", "new-public"}


def test_private_row_never_gains_a_public_member_link():
    model, _rows, _public = estate_service._aggregate(_sources())
    private = model.repository("private-tool")
    assert private is not None
    assert private.visibility == "private"
    assert private.github_present is None
    assert all(source.repository != "private-tool" for source in private.sources)


def test_listing_failure_keeps_fleet_rows_and_makes_presence_unknown():
    model, _rows, _public = estate_service._aggregate(_sources(listing_ok=False))
    assert {repo.name for repo in model.repositories} == {"alpha", "private-tool"}
    assert model.repository("alpha").github_present is None


def test_listing_failure_does_not_treat_future_archive_prose_as_archived():
    sources = _sources(listing_ok=False)
    row = replace(
        sources.estate.rows[0],
        raw_state=(
            "complete-parked architecture donor — archive remains queued; "
            "not archived"
        ),
        section="Paused / owner-gated",
    )
    sources = replace(
        sources,
        estate=estate_reader.EstateParseResult(
            (row, *sources.estate.rows[1:])
        ),
    )
    model, _rows, _public = estate_service._aggregate(sources)
    assert model.repository("alpha").status is estate.RepositoryStatus.PAUSED


def test_live_not_archived_does_not_make_dated_active_state_live():
    sources = _sources()
    public = (
        replace(sources.public_repositories[0], archived=False),
        sources.public_repositories[1],
    )
    model, _rows, _public = estate_service._aggregate(
        replace(sources, public_repositories=public)
    )
    alpha = model.repository("alpha")
    assert alpha.status is estate.RepositoryStatus.ACTIVE
    assert alpha.status_source.label == "Fleet Manager estate index"
    assert alpha.status_freshness.state is not estate.FreshnessState.LIVE


def test_catalogue_freshness_uses_oldest_row_verification_floor():
    sources = _sources()
    rows = (
        replace(sources.estate.rows[0], verified_date="2026-08-21"),
        replace(sources.estate.rows[1], verified_date="2026-08-24"),
    )
    model, _rows, _public = estate_service._aggregate(
        replace(sources, estate=estate_reader.EstateParseResult(rows))
    )
    assert model.freshness.fact_as_of.date().isoformat() == "2026-08-21"


def test_exactly_full_public_listing_is_not_treated_as_exhaustive():
    sources = _sources()
    full_page = [{"name": f"repo-{index}"} for index in range(100)]
    model, _rows, _public = estate_service._aggregate(
        replace(
            sources,
            public_repos_result=_result(full_page),
            public_repositories=(),
            unindexed_public_repositories=(),
        )
    )
    assert model.repository("alpha").github_present is None


def test_successful_but_unparseable_sources_are_not_labelled_live():
    sources = _sources()
    malformed = replace(
        sources,
        estate=estate_reader.EstateParseResult(
            (), ("no estate repository tables found",)
        ),
        activity=estate_reader.ActivityParseResult(
            None, (), (), (), ("activity log generated timestamp missing",)
        ),
    )
    model, _rows, _public = estate_service._aggregate(malformed)
    by_label = {source.label: source for source in model.sources}
    assert by_label["Fleet Manager estate index"].freshness.state is estate.FreshnessState.UNAVAILABLE
    assert by_label["Fleet Manager activity log"].freshness.state is estate.FreshnessState.UNAVAILABLE
    assert "activity log generated timestamp missing" in model.warnings


def test_overview_delegates_to_reader(monkeypatch):
    calls = []

    async def fake_read(refresh=False, *, coalesce_public_listing=True):
        calls.append((refresh, coalesce_public_listing))
        return _sources()

    monkeypatch.setattr(estate_reader, "read_overview_sources", fake_read)
    model = asyncio.run(
        estate_service.overview(
            refresh=True,
            coalesce_public_listing=False,
        )
    )
    assert model.repository("alpha")
    assert calls == [(True, False)]


def test_detail_uses_member_truth_and_exact_next_heading(monkeypatch):
    async def fake_overview(refresh=False):
        return _sources()

    async def fake_detail(
        name,
        is_public,
        layer2_path,
        member_paths=None,
        member_ref="main",
        refresh=False,
    ):
        assert name == "alpha" and is_public is True
        assert member_paths[0] == "README.md"
        assert member_ref == "main"
        members = {
            path: _result(None, ok=False, status=404, error="Not Found")
            for path in estate_reader.MEMBER_PROBE_PATHS
        }
        members["docs/current-state.md"] = _result(
            "# Current state\n\nAuthoritative situation.\n\n"
            "## Next step\n\nShip the verified slice."
        )
        return estate_reader.DetailSources(
            name=name,
            is_public=True,
            layer2_path=layer2_path,
            layer2_result=_result(
                "# alpha\n\n## The one-paragraph answer\n\nRouting context."
            ),
            member_results=members,
        )

    monkeypatch.setattr(estate_reader, "read_overview_sources", fake_overview)
    monkeypatch.setattr(estate_reader, "read_detail_sources", fake_detail)
    detail = asyncio.run(estate_service.detail("alpha"))
    assert detail.current_situation == "Authoritative situation."
    assert detail.current_next_thread == "Ship the verified slice."
    assert detail.current_situation_source.path == "docs/current-state.md"
    assert detail.current_next_thread_source.path == "docs/current-state.md"
    assert any(source.path == "docs/current-state.md" for source in detail.all_sources)


def test_detail_rejects_unsafe_name_before_any_io(monkeypatch):
    async def should_not_run(*args, **kwargs):
        raise AssertionError("unsafe name triggered I/O")

    monkeypatch.setattr(estate_reader, "read_overview_sources", should_not_run)
    assert asyncio.run(estate_service.detail("../private")) is None


def test_detail_does_not_promote_layer2_roadmap(monkeypatch):
    async def fake_overview(refresh=False):
        return _sources()

    async def fake_detail(
        name,
        is_public,
        layer2_path,
        member_paths=None,
        member_ref="main",
        refresh=False,
    ):
        members = {
            path: _result(None, ok=False, status=404, error="Not Found")
            for path in estate_reader.MEMBER_PROBE_PATHS
        }
        return estate_reader.DetailSources(
            name=name,
            is_public=True,
            layer2_path=layer2_path,
            layer2_result=_result(
                "## The one-paragraph answer\n\nUseful orientation.\n\n"
                "## Next step\n\nThis dated Layer-2 plan must not become roadmap."
            ),
            member_results=members,
        )

    monkeypatch.setattr(estate_reader, "read_overview_sources", fake_overview)
    monkeypatch.setattr(estate_reader, "read_detail_sources", fake_detail)
    detail = asyncio.run(estate_service.detail("alpha"))
    assert detail.current_situation == "Useful orientation."
    assert detail.current_next_thread_text == estate.NEXT_THREAD_UNKNOWN


def test_detail_uses_public_default_branch_for_reads_and_source_links(monkeypatch):
    sources = _sources()
    public = (
        replace(sources.public_repositories[0], default_branch="master"),
        sources.public_repositories[1],
    )

    async def fake_overview(refresh=False):
        return replace(sources, public_repositories=public)

    async def fake_detail(
        name,
        is_public,
        layer2_path,
        member_paths=None,
        member_ref="main",
        refresh=False,
    ):
        assert member_ref == "master"
        members = {
            path: _result(None, ok=False, status=404, error="Not Found")
            for path in member_paths
        }
        members["README.md"] = _result(
            "## Overview\n\nAuthoritative master-branch situation."
        )
        return estate_reader.DetailSources(
            name=name,
            is_public=True,
            layer2_path=layer2_path,
            layer2_result=_result(None, ok=False, status=404),
            member_results=members,
        )

    monkeypatch.setattr(estate_reader, "read_overview_sources", fake_overview)
    monkeypatch.setattr(estate_reader, "read_detail_sources", fake_detail)
    detail = asyncio.run(estate_service.detail("alpha"))
    readme = next(source for source in detail.all_sources if source.path == "README.md")
    assert "/blob/master/README.md" in readme.url


def test_current_inflight_activity_survives_the_detail_cutoff(monkeypatch):
    sources = _sources()
    in_flight = estate_reader.ActivityRecord(
        kind="in_flight",
        repo="alpha",
        date="",
        status="in-progress",
        venue="chatgpt-work",
        model="",
        title="Current review",
        detail="#521",
        source_url="https://github.com/menno420/websites/pull/521",
        related_url="",
        source_line=1,
    )
    sessions = tuple(
        replace(
            sources.activity.sessions[0],
            date=f"2026-08-{26 - index:02d}",
            title=f"older {index}",
        )
        for index in range(10)
    )
    sources = replace(
        sources,
        activity=estate_reader.ActivityParseResult(
            generated_at="2026-08-27 09:30Z",
            in_flight=(in_flight,),
            sessions=sessions,
            invisible_work=(),
            recognized_sections=("in_flight", "sessions"),
        ),
    )

    async def fake_overview(refresh=False):
        return sources

    async def fake_detail(
        name,
        is_public,
        layer2_path,
        member_paths=None,
        member_ref="main",
        refresh=False,
    ):
        return estate_reader.DetailSources(
            name=name,
            is_public=True,
            layer2_path=layer2_path,
            layer2_result=_result(None, ok=False, status=404),
            member_results={
                path: _result(None, ok=False, status=404)
                for path in member_paths
            },
        )

    monkeypatch.setattr(estate_reader, "read_overview_sources", fake_overview)
    monkeypatch.setattr(estate_reader, "read_detail_sources", fake_detail)
    detail = asyncio.run(estate_service.detail("alpha"))
    assert detail.recent_activity[0].kind == "in_flight"
    assert any(item.kind == "in_flight" for item in detail.recent_activity)
