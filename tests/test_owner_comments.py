"""Public Fleet Manager owner-comment contract and bounded-read tests."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app import estate, estate_reader, estate_service, github, listfilter, owner_comments

UTC = timezone.utc
NOW = datetime(2026, 8, 27, 12, tzinfo=UTC)


def _json(data) -> str:
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _result(data=None, *, ok=True, status=200, cached=False, error="") -> dict:
    return {
        "ok": ok,
        "status": status,
        "data": data,
        "error": error,
        "fetched_at": "12:00:00 UTC",
        "fetched_at_iso": "2026-08-27T12:00:00Z",
        "cached": cached,
        "url": "https://raw.example/source",
    }


def _root_row(
    repository="alpha",
    *,
    active=0,
    consumed=0,
    latest_active=None,
    latest_consumed=None,
) -> dict:
    return {
        "repository": repository,
        "index": f"docs/owner-comments/{repository}/README.md",
        "unconsumed_count": active,
        "consumed_count": consumed,
        "latest_unconsumed_at": latest_active,
        "latest_consumed_at": latest_consumed,
    }


def _root(*rows) -> str:
    return _json(
        {
            "schema_version": 1,
            "derived_from": list(owner_comments.DERIVED_FROM),
            "repositories": list(rows),
        }
    )


@pytest.mark.parametrize(
    "payload",
    (
        _root(_root_row()).replace(
            '"unconsumed_count": 0',
            '"unconsumed_count": 0,\n      "unconsumed_count": 1',
            1,
        ),
        '{"schema_version": ' + ("9" * 5_000) + "}\n",
        '{"x":' + ("[" * 2_000) + "0" + ("]" * 2_000) + "}\n",
    ),
)
def test_hostile_json_degrades_index_instead_of_escaping(monkeypatch, payload):
    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _result(payload)

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    result = asyncio.run(owner_comments.read_index())

    assert result.valid is False
    assert result.rows == ()
    assert result.warnings


def _repo_index(repository="alpha", *, active=(), consumed=()) -> str:
    lines = [
        f"# Owner comments — `{repository}`",
        "",
        "> **Status:** `living-ledger`",
        ">",
        "> **Generated index.** Run `python3 tools/owner_comments.py reindex`;",
        "> do not hand-edit this file. **Every record and all of its metadata",
        "> are public.** Read the [storage and privacy contract](../README.md)",
        "> before adding feedback. JSON preserves the owner's wording verbatim.",
        "",
        f"## Unconsumed ({len(active)})",
        "",
    ]
    if active:
        lines.extend(
            [
                "| id | created at | source | record |",
                "|---|---|---|---|",
            ]
        )
        for comment_id, created_at, surface in active:
            lines.append(
                f"| `{comment_id}` | `{created_at}` | {surface} | "
                f"[`{comment_id}.json`]({comment_id}.json) |"
            )
    else:
        lines.append("No unconsumed owner comments.")
    lines.extend(["", f"## Consumed history ({len(consumed)})", ""])
    if consumed:
        lines.extend(
            [
                "| id | created at | consumed at | preserved record |",
                "|---|---|---|---|",
            ]
        )
        for comment_id, created_at, consumed_at in consumed:
            lines.append(
                f"| `{comment_id}` | `{created_at}` | `{consumed_at}` | "
                f"[`{comment_id}.json`](consumed/{comment_id}.json) |"
            )
    else:
        lines.append("No consumed owner comments.")
    lines.extend(
        [
            "",
            "## Consume mechanically",
            "",
            "After acting or explicitly reconciling a comment, run:",
            "",
            "```text",
            f"python3 tools/owner_comments.py consume {repository} <comment-id> \\",
            "  --actor <session-card-or-actor> --evidence <record-or-PR-link>",
            "```",
            "",
            "Commit the moved record and both changed indexes together. Never delete it.",
            "",
        ]
    )
    return "\n".join(lines)


def _record(
    comment_id,
    created_at,
    *,
    repository="alpha",
    state="unconsumed",
    comment="Owner wording",
    surface="control-plane",
    context="/repos/alpha",
    consumed_at=None,
) -> dict:
    data = {
        "schema_version": 1,
        "id": comment_id,
        "repository": repository,
        "created_at": created_at,
        "state": state,
        "source": {"surface": surface, "context": context},
        "comment": comment,
    }
    if state == "consumed":
        data["consumption"] = {
            "at": consumed_at,
            "actor": "session-card",
            "evidence": "PR #1",
        }
    return data


def test_read_index_is_one_anonymous_public_fetch_and_zero_is_known(monkeypatch):
    calls = []

    async def fake_fetch(repo, path, ref="main", refresh=False):
        calls.append((repo, path, ref, refresh))
        return _result(_root(_root_row()))

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    read = asyncio.run(owner_comments.read_index(refresh=True))
    summary = owner_comments.summary_for(read, "alpha")
    assert calls == [
        (
            "fleet-manager",
            "docs/owner-comments/index.json",
            "main",
            True,
        )
    ]
    assert read.valid
    assert summary.is_known and summary.total_count == 0
    assert summary.freshness.state is estate.FreshnessState.LIVE
    assert summary.source.path == "docs/owner-comments/index.json"


def test_cached_root_index_is_measured_not_live(monkeypatch):
    async def fake_fetch(*args, **kwargs):
        return _result(_root(_root_row()), cached=True)

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    summary = owner_comments.summary_for(
        asyncio.run(owner_comments.read_index()), "alpha"
    )
    assert summary.freshness.state is estate.FreshnessState.MEASURED
    assert summary.freshness.retrieved_at == NOW


def test_missing_root_is_unavailable_never_zero(monkeypatch):
    async def fake_fetch(*args, **kwargs):
        return _result(None, ok=False, status=404, error="Not Found")

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    read = asyncio.run(owner_comments.read_index())
    summary = owner_comments.summary_for(read, "alpha")
    assert not read.valid
    assert summary.unconsumed_count is None
    assert summary.consumed_count is None
    assert summary.has_comments is None
    assert summary.freshness.state is estate.FreshnessState.UNAVAILABLE


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: "{not json",
        lambda data: _json({**data, "schema_version": 2}),
        lambda data: _json({**data, "unexpected": True}),
        lambda data: _json({**data, "derived_from": ["wrong"]}),
        lambda data: _json(
            {
                **data,
                "repositories": [
                    {
                        **data["repositories"][0],
                        "index": "docs/owner-comments/other/README.md",
                    }
                ],
            }
        ),
        lambda data: _json(
            {
                **data,
                "repositories": [
                    {
                        **data["repositories"][0],
                        "unconsumed_count": 1,
                        "latest_unconsumed_at": None,
                    }
                ],
            }
        ),
    ],
    ids=(
        "malformed",
        "version",
        "unknown-key",
        "derived-from",
        "root-path-mismatch",
        "count-timestamp-mismatch",
    ),
)
def test_bad_root_shapes_are_rejected(mutate):
    data = json.loads(_root(_root_row()))
    with pytest.raises(owner_comments.OwnerCommentContractError):
        owner_comments.parse_root_index(mutate(data))


def test_missing_or_case_mismatched_repository_is_unknown_not_zero():
    source = estate.SourceReference(
        "Fleet owner comments",
        "https://example.test/index.json",
        freshness=estate.Freshness.live(NOW),
    )
    index = owner_comments.OwnerCommentIndexRead(
        owner_comments.parse_root_index(_root(_root_row("Alpha"))),
        source,
        valid=True,
    )
    for name in ("alpha", "missing"):
        summary = owner_comments.summary_for(index, name)
        assert not summary.is_known
        assert summary.has_comments is None
        assert summary.freshness.state is estate.FreshnessState.UNKNOWN


def test_detail_reads_active_and_consumed_and_keeps_untrusted_text_raw(monkeypatch):
    active = ("oc-active", "2026-08-27T10:00:00Z", "control-plane")
    consumed = (
        "oc-consumed",
        "2026-08-26T09:00:00Z",
        "2026-08-27T11:00:00Z",
    )
    index = _repo_index(active=(active,), consumed=(consumed,))
    raw_comment = "<script>alert('x')</script> **not markdown**"
    raw_context = "<b>/repos/alpha</b>"
    payloads = {
        "docs/owner-comments/alpha/README.md": _result(index),
        "docs/owner-comments/alpha/oc-active.json": _result(
            _json(
                _record(
                    active[0],
                    active[1],
                    comment=raw_comment,
                    context=raw_context,
                )
            )
        ),
        "docs/owner-comments/alpha/consumed/oc-consumed.json": _result(
            _json(
                _record(
                    consumed[0],
                    consumed[1],
                    state="consumed",
                    consumed_at=consumed[2],
                )
            )
        ),
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        assert repo == "fleet-manager"
        return payloads[path]

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    expected = estate.OwnerCommentSummary(1, 1, estate.Freshness.live(NOW))
    collection = asyncio.run(
        owner_comments.read_repository_comments(
            "alpha", expected_summary=expected, refresh=True
        )
    )
    assert [record.id for record in collection.unconsumed] == ["oc-active"]
    assert [record.id for record in collection.consumed] == ["oc-consumed"]
    assert collection.unconsumed[0].comment == raw_comment
    assert collection.unconsumed[0].source_context == raw_context
    assert collection.consumed[0].consumption_actor == "session-card"
    assert collection.consumed[0].consumption_evidence == "PR #1"
    assert "/blob/main/docs/owner-comments/alpha/oc-active.json" in (
        collection.unconsumed[0].source.url
    )
    assert collection.freshness.state is estate.FreshnessState.LIVE
    assert not collection.warnings and not collection.truncated


@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        (lambda data: {**data, "schema_version": 2}, "schema"),
        (lambda data: {**data, "id": "different-id"}, "id/path"),
        (lambda data: {**data, "repository": "other"}, "repository/path"),
        (lambda data: {**data, "state": "consumed"}, "state/path"),
        (lambda data: {**data, "unexpected": True}, "unknown field"),
        (
            lambda data: {**data, "source": {**data["source"], "extra": "x"}},
            "source fields",
        ),
        (
            lambda data: {**data, "created_at": "2026-02-30T10:00:00Z"},
            "real RFC3339",
        ),
    ],
    ids=(
        "schema",
        "id-path",
        "repository-path",
        "state-path",
        "unknown-top-key",
        "unknown-source-key",
        "invalid-timestamp",
    ),
)
def test_malformed_record_is_skipped_without_sinking_detail(monkeypatch, mutation, needle):
    active = ("oc-active", "2026-08-27T10:00:00Z", "control-plane")
    payload = mutation(_record(active[0], active[1]))
    payloads = {
        "docs/owner-comments/alpha/README.md": _result(
            _repo_index(active=(active,))
        ),
        "docs/owner-comments/alpha/oc-active.json": _result(_json(payload)),
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return payloads[path]

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    collection = asyncio.run(owner_comments.read_repository_comments("alpha"))
    assert collection.unconsumed == ()
    assert any(needle in warning for warning in collection.warnings)
    assert collection.freshness.state is estate.FreshnessState.UNKNOWN


def test_noncanonical_readme_record_path_is_rejected():
    text = _repo_index(
        active=(("oc-active", "2026-08-27T10:00:00Z", "control-plane"),)
    ).replace("(oc-active.json)", "(other.json)")
    with pytest.raises(owner_comments.OwnerCommentContractError, match="active path"):
        owner_comments.parse_repository_index(text, "alpha")


def test_one_record_fetch_failure_degrades_only_that_record(monkeypatch):
    active = (
        ("oc-one", "2026-08-27T10:00:00Z", "control-plane"),
        ("oc-two", "2026-08-27T11:00:00Z", "control-plane"),
    )

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.endswith("README.md"):
            return _result(_repo_index(active=active))
        if path.endswith("oc-two.json"):
            return _result(None, ok=False, status=503, error="offline")
        return _result(_json(_record(active[0][0], active[0][1])))

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    collection = asyncio.run(owner_comments.read_repository_comments("alpha"))
    assert [record.id for record in collection.unconsumed] == ["oc-one"]
    assert any("oc-two: record unavailable" in item for item in collection.warnings)
    assert collection.freshness.state is estate.FreshnessState.UNKNOWN


@pytest.mark.parametrize(
    ("hostile", "needle"),
    (
        (
            _repo_index().replace(
                "## Unconsumed (0)",
                f"## Unconsumed ({'9' * 5_000})",
            ),
            "bounded count",
        ),
        (
            _repo_index().replace(
                "## Unconsumed (0)", "## Unconsumed (00000)"
            ),
            "not canonical",
        ),
        (_repo_index().replace("\n", "\r\n"), "canonical LF"),
    ),
)
def test_hostile_repository_index_degrades_detail_instead_of_escaping(
    monkeypatch, hostile, needle
):

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return _result(hostile)

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    collection = asyncio.run(
        owner_comments.read_repository_comments("alpha")
    )

    assert collection.unconsumed == ()
    assert collection.freshness.state is estate.FreshnessState.UNAVAILABLE
    assert any(needle in warning for warning in collection.warnings)


@pytest.mark.parametrize("separator", ("\u2028", "\x0b"))
def test_repository_index_rejects_non_lf_line_separators(separator):
    text = _repo_index().replace("\n", separator, 1)
    with pytest.raises(
        owner_comments.OwnerCommentContractError,
        match="generated Fleet Manager v1 shape",
    ):
        owner_comments.parse_repository_index(text, "alpha")


def test_detail_caps_fanout_and_bounds_concurrency(monkeypatch):
    active = tuple(
        (
            f"oc-a-{index:03d}",
            f"2026-08-27T10:{index:02d}:00Z",
            "control-plane",
        )
        for index in range(52)
    )
    consumed = tuple(
        (
            f"oc-c-{index:03d}",
            f"2026-08-26T10:{index:02d}:00Z",
            f"2026-08-27T11:{index:02d}:00Z",
        )
        for index in range(12)
    )
    in_flight = 0
    high_water = 0
    record_calls = []

    async def fake_fetch(repo, path, ref="main", refresh=False):
        nonlocal in_flight, high_water
        if path.endswith("README.md"):
            return _result(_repo_index(active=active, consumed=consumed))
        in_flight += 1
        high_water = max(high_water, in_flight)
        await asyncio.sleep(0)
        record_calls.append(path)
        in_flight -= 1
        comment_id = path.rsplit("/", 1)[-1][:-5]
        if "/consumed/" in path:
            entry = next(item for item in consumed if item[0] == comment_id)
            data = _record(
                entry[0],
                entry[1],
                state="consumed",
                consumed_at=entry[2],
            )
        else:
            entry = next(item for item in active if item[0] == comment_id)
            data = _record(entry[0], entry[1])
        return _result(_json(data))

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    collection = asyncio.run(owner_comments.read_repository_comments("alpha"))
    assert collection.truncated
    assert len(collection.unconsumed) == owner_comments.MAX_ACTIVE_RECORDS
    assert len(collection.consumed) == owner_comments.MAX_CONSUMED_RECORDS
    assert collection.unconsumed[0].id == "oc-a-002"
    assert collection.consumed[0].id == "oc-c-002"
    assert len(record_calls) == 60
    assert high_water <= owner_comments.DETAIL_CONCURRENCY


def test_detail_total_budget_cancels_slow_record_fanout(monkeypatch):
    active = tuple(
        (
            f"oc-slow-{index:03d}",
            f"2026-08-27T10:00:{index:02d}Z",
            "control-plane",
        )
        for index in range(8)
    )
    cancelled = 0

    async def fake_fetch(repo, path, ref="main", refresh=False):
        nonlocal cancelled
        if path.endswith("README.md"):
            return _result(_repo_index(active=active))
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled += 1
            raise

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    monkeypatch.setattr(owner_comments, "DETAIL_TIMEOUT_SECONDS", 0.01)
    collection = asyncio.run(
        owner_comments.read_repository_comments("alpha", refresh=True)
    )

    assert collection.unconsumed == ()
    assert any("detail budget" in warning for warning in collection.warnings)
    assert cancelled <= owner_comments.DETAIL_CONCURRENCY
    assert collection.freshness.state is estate.FreshnessState.UNKNOWN


def test_root_repository_count_mismatch_is_visible_but_records_survive(monkeypatch):
    active = ("oc-active", "2026-08-27T10:00:00Z", "control-plane")

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if path.endswith("README.md"):
            return _result(_repo_index(active=(active,)))
        return _result(_json(_record(active[0], active[1])))

    monkeypatch.setattr(github, "fetch_public_file", fake_fetch)
    expected = estate.OwnerCommentSummary(2, 0, estate.Freshness.live(NOW))
    collection = asyncio.run(
        owner_comments.read_repository_comments("alpha", expected_summary=expected)
    )
    assert len(collection.unconsumed) == 1
    assert any("indexes disagree" in warning for warning in collection.warnings)
    assert collection.freshness.state is estate.FreshnessState.UNKNOWN


def _overview_sources() -> estate_reader.OverviewSources:
    row = estate_reader.EstateRow(
        name="alpha",
        purpose="Alpha product",
        raw_state="active",
        read_first="`README.md`",
        layer2="[entry](repos/alpha/README.md)",
        layer2_path="docs/repos/alpha/README.md",
        section="Active",
        verified_date="2026-08-27",
        source_line=1,
    )
    public = estate_reader.PublicRepository(
        name="new-public",
        description="",
        html_url="https://github.com/menno420/new-public",
        archived=False,
        disabled=False,
        pushed_at="2026-08-27T09:00:00Z",
        updated_at="2026-08-27T09:00:00Z",
        default_branch="main",
        open_issues_count=0,
    )
    activity = estate_reader.ActivityParseResult(
        generated_at="2026-08-27 11:00Z",
        in_flight=(),
        sessions=(),
        invisible_work=(),
        recognized_sections=("sessions",),
    )
    return estate_reader.OverviewSources(
        estate_result=_result("estate"),
        activity_result=_result("activity"),
        public_repos_result=_result([{"name": "new-public"}]),
        estate=estate_reader.EstateParseResult((row,)),
        activity=activity,
        public_repositories=(public,),
        unindexed_public_repositories=(public,),
    )


def test_estate_aggregation_joins_counts_filter_and_unindexed_unavailable():
    source = estate.SourceReference(
        "Fleet owner comments",
        "https://example.test/index.json",
        repository="fleet-manager",
        path=owner_comments.ROOT_INDEX_PATH,
        freshness=estate.Freshness.live(NOW),
    )
    index = owner_comments.OwnerCommentIndexRead(
        owner_comments.parse_root_index(
            _root(
                _root_row(
                    active=1,
                    latest_active="2026-08-27T10:00:00Z",
                )
            )
        ),
        source,
        valid=True,
    )
    model, _rows, _public = estate_service._aggregate(_overview_sources(), index)
    alpha = model.repository("alpha")
    unindexed = model.repository("new-public")
    assert alpha.owner_comments.unconsumed_count == 1
    assert "has-owner-comments" in alpha.signal_values
    state = listfilter.parse(estate.REPOS_LIST_SPEC, {"signal": "has-owner-comments"})
    view = listfilter.apply(estate.REPOS_LIST_SPEC, model.repositories, state)
    assert [item.name for item in view["items"]] == ["alpha"]
    assert unindexed.owner_comments.unconsumed_count is None
    assert unindexed.owner_comments.freshness.state is estate.FreshnessState.UNAVAILABLE
    assert model.sources[-1] is source


def test_owner_comment_models_are_immutable_tuple_data_and_sources_join_detail():
    source = estate.SourceReference(
        "record",
        "https://example.test/record.json",
        freshness=estate.Freshness.live(NOW),
    )
    record = estate.OwnerCommentRecord(
        id="oc-active",
        repository="alpha",
        comment="<em>plain data</em>",
        created_at=datetime(2026, 8, 27, 10),
        state="unconsumed",
        source_surface="control-plane",
        source=source,
    )
    collection = estate.OwnerCommentCollection(unconsumed=[record], warnings=["x"])
    detail = estate.RepositoryDetail(
        summary=estate.RepositorySummary("alpha"), owner_feedback=collection
    )
    assert collection.unconsumed == (record,)
    assert collection.warnings == ("x",)
    assert record.created_at.tzinfo == UTC
    assert record.comment == "<em>plain data</em>"
    assert source in detail.all_sources
    with pytest.raises(ValueError, match="state"):
        replace(record, state="future")
