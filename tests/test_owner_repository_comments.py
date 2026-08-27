"""Owner-comment UI security, validation, and honest-state contracts."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import (
    config,
    estate,
    estate_reader,
    estate_service,
    owner,
    owner_comment_writeback,
)
from app.main import app

UTC = timezone.utc
OWNER_PASSWORD = "owner-comment-test-password"
SAME_ORIGIN = "http://testserver"
CROSS_ORIGIN = "https://attacker.example"
SUBMISSION_KEY = "0123456789abcdef0123456789abcdef"


def _basic(password: str = OWNER_PASSWORD) -> dict[str, str]:
    token = base64.b64encode(f"owner:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _summary(
    name: str = "websites",
    *,
    visibility: str = "public",
    indexed: bool = True,
) -> estate.RepositorySummary:
    return estate.RepositorySummary(
        name=name,
        purpose="Control-plane websites",
        status=estate.RepositoryStatus.ACTIVE,
        raw_status="active",
        freshness=estate.Freshness.live(
            datetime(2026, 8, 27, 12, tzinfo=UTC)
        ),
        status_freshness=estate.Freshness.live(
            datetime(2026, 8, 27, 12, tzinfo=UTC)
        ),
        indexed_by_fleet_manager=indexed,
        visibility=visibility,
    )


def _overview(*repositories: estate.RepositorySummary) -> estate.EstateOverview:
    return estate.EstateOverview(repositories=repositories)


def _public_lookup(
    name: str = "websites",
    *,
    visibility: str = "public",
    status: int = 200,
) -> estate_reader.PublicRepositoryLookup:
    repository = (
        estate_reader.PublicRepository(
            name=name,
            description="Control-plane websites",
            html_url=f"https://github.com/menno420/{name}",
            archived=False,
            disabled=False,
            pushed_at="2026-08-27T12:00:00Z",
            updated_at="2026-08-27T12:00:00Z",
            default_branch="main",
            open_issues_count=0,
        )
        if visibility == "public"
        else None
    )
    return estate_reader.PublicRepositoryLookup(
        name=name,
        result={
            "ok": 200 <= status < 300,
            "status": status,
            "data": {} if status == 200 else None,
            "error": "Not Found" if status == 404 else "",
        },
        repository=repository,
        visibility=visibility,
        reason="" if visibility == "public" else "not publicly visible",
    )


@pytest.fixture(autouse=True)
def _reset_owner_limits():
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


@pytest.fixture(autouse=True)
def _default_exact_public_lookup(monkeypatch):
    async def fake_lookup(name, *, refresh=False, coalesce=True):
        return _public_lookup(name)

    monkeypatch.setattr(estate_reader, "read_public_repository", fake_lookup)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PASSWORD)
    monkeypatch.setenv(owner_comment_writeback.ENV_TOKEN, "fleet-write-token")
    with TestClient(app) as value:
        yield value


def _install_overview(monkeypatch, *repositories):
    async def fake_overview(refresh=False, *, coalesce_public_listing=True):
        return _overview(*repositories)

    monkeypatch.setattr(estate_service, "overview", fake_overview)


def test_comment_form_is_owner_only_and_names_public_destination(
    client, monkeypatch
):
    _install_overview(monkeypatch, _summary())
    assert client.get("/owner/repository-comments/websites").status_code == 401

    response = client.get(
        "/owner/repository-comments/websites", headers=_basic()
    )
    assert response.status_code == 200
    assert "Public record" in response.text
    assert "menno420/fleet-manager" in response.text
    assert "FLEET_MANAGER_WRITEBACK_TOKEN" not in response.text
    assert 'name="public_acknowledgement"' in response.text
    assert 'name="submission_key" value="' in response.text
    assert "credential configured" in response.text
    assert "verified against Fleet Manager when" in response.text


def test_fleet_indexed_repo_beyond_listing_limit_gets_exact_form_and_post(
    client, monkeypatch
):
    _install_overview(monkeypatch, _summary(visibility="unknown"))
    lookups = []
    submitted = []

    async def exact_public(name, *, refresh=False, coalesce=True):
        lookups.append((name, refresh, coalesce))
        return _public_lookup(name)

    async def fake_submit(repository, comment, **kwargs):
        submitted.append((repository, comment, kwargs))
        return owner_comment_writeback.OwnerCommentWritebackResult(
            state="pending_pr",
            repository=repository,
            comment_id="oc-0123456789abcdef0123456789abcdef",
            branch="claude/owner-comments-oc-0123456789abcdef0123456789abcdef",
            pr_number=953,
            pr_url="https://github.com/menno420/fleet-manager/pull/953",
        )

    monkeypatch.setattr(estate_reader, "read_public_repository", exact_public)
    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )

    form = client.get(
        "/owner/repository-comments/websites",
        headers=_basic(),
    )
    assert form.status_code == 200
    assert 'name="public_acknowledgement"' in form.text

    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "This repo is beyond the overview page.",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )

    assert response.status_code == 202
    assert lookups == [
        ("websites", False, True),
        ("websites", True, False),
    ]
    assert submitted and submitted[0][0] == "websites"


def test_comment_post_rejects_cross_origin_before_write(client, monkeypatch):
    _install_overview(monkeypatch, _summary())
    called = False

    async def fake_submit(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("writeback must not run")

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "hello",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    )
    assert response.status_code == 403
    assert not called


def test_submission_revalidates_public_visibility_without_cache(
    client, monkeypatch
):
    refreshes = []
    lookups = []

    async def changing_overview(
        refresh=False, *, coalesce_public_listing=True
    ):
        refreshes.append((refresh, coalesce_public_listing))
        return _overview(_summary())

    async def changing_lookup(name, *, refresh=False, coalesce=True):
        lookups.append((name, refresh, coalesce))
        return (
            _public_lookup(name, visibility="unavailable", status=404)
            if refresh
            else _public_lookup(name)
        )

    async def forbidden(*args, **kwargs):
        raise AssertionError("private target must not reach writeback")

    monkeypatch.setattr(estate_service, "overview", changing_overview)
    monkeypatch.setattr(estate_reader, "read_public_repository", changing_lookup)
    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", forbidden
    )

    form = client.get(
        "/owner/repository-comments/websites", headers=_basic()
    )
    assert form.status_code == 200
    assert refreshes == [(False, True)]
    assert lookups == [("websites", False, True)]

    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "This must stay behind the public boundary.",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )

    assert response.status_code == 503
    assert refreshes == [(False, True), (True, True)]
    assert lookups == [
        ("websites", False, True),
        ("websites", True, False),
    ]
    assert "not confidently established as public" in response.text


def test_submission_preserves_owner_text_and_reports_pending_not_durable(
    client, monkeypatch
):
    _install_overview(monkeypatch, _summary())
    captured = {}
    wording = "  Keep <script>alert(1)</script> & this line\nexactly.  "

    async def fake_submit(
        repository, comment, *, context=None, submission_key=None
    ):
        captured.update(
            repository=repository,
            comment=comment,
            context=context,
            submission_key=submission_key,
        )
        return owner_comment_writeback.OwnerCommentWritebackResult(
            state="pending_pr",
            repository=repository,
            comment_id="oc-20260827t120000z-a1b2c3d4",
            branch="claude/owner-comments-oc-20260827t120000z-a1b2c3d4",
            pr_number=953,
            pr_url="https://github.com/menno420/fleet-manager/pull/953",
        )

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": wording,
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 202
    assert captured == {
        "repository": "websites",
        "comment": wording,
        "context": "/repos/websites",
        "submission_key": SUBMISSION_KEY,
    }
    assert "Pending Fleet Manager PR — not durable yet" in response.text
    assert "Fleet Manager PR #953" in response.text
    assert (
        'href="https://github.com/menno420/fleet-manager/pull/953"'
        in response.text
    )
    assert "durable only after" in response.text


@pytest.mark.parametrize(
    ("comment", "ack", "needle"),
    (
        ("hello", "", "Confirm that the comment"),
        (" \n\t ", "yes", "non-whitespace"),
        ("x\x00y", "yes", "NUL byte"),
        ("x" * 20_001, "yes", "20000 characters"),
    ),
)
def test_invalid_comment_never_reaches_writeback(
    client, monkeypatch, comment, ack, needle
):
    _install_overview(monkeypatch, _summary())

    async def fake_submit(*args, **kwargs):
        raise AssertionError("invalid comment must not reach writeback")

    async def forbidden_lookup(*args, **kwargs):
        raise AssertionError("invalid form must not spend a visibility lookup")

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    monkeypatch.setattr(
        estate_reader, "read_public_repository", forbidden_lookup
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": comment,
            "public_acknowledgement": ack,
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 422
    assert needle in response.text


def test_missing_submission_key_never_reaches_writeback(client, monkeypatch):
    _install_overview(monkeypatch, _summary())

    async def fake_submit(*args, **kwargs):
        raise AssertionError("missing idempotency key must not reach writeback")

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "hello",
            "public_acknowledgement": "yes",
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )

    assert response.status_code == 422
    assert "submission key is missing" in response.text


def test_unknown_private_and_missing_token_never_write(client, monkeypatch):
    private = _summary("estate-backups", visibility="private")
    _install_overview(monkeypatch, private)

    async def fake_submit(*args, **kwargs):
        raise AssertionError("unavailable target must not reach writeback")

    async def forbidden_lookup(*args, **kwargs):
        raise AssertionError(
            "explicit Fleet private/unavailable capability must not be overridden"
        )

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    monkeypatch.setattr(
        estate_reader, "read_public_repository", forbidden_lookup
    )
    headers = {**_basic(), "Origin": SAME_ORIGIN}
    private_response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "estate-backups",
            "comment": "public-looking text",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers=headers,
    )
    assert private_response.status_code == 503
    assert "not confidently established as public" in private_response.text
    assert "Required external action" not in private_response.text
    assert owner_comment_writeback.ENV_TOKEN not in private_response.text

    monkeypatch.delenv(owner_comment_writeback.ENV_TOKEN, raising=False)
    private_without_token = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "estate-backups",
            "comment": "public-looking text",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers=headers,
    )
    assert private_without_token.status_code == 503
    assert "Required external action" not in private_without_token.text
    assert owner_comment_writeback.ENV_TOKEN not in private_without_token.text

    _install_overview(
        monkeypatch, _summary("github-only", indexed=False)
    )
    unindexed_without_token = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "github-only",
            "comment": "estate routing first",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers=headers,
    )
    assert unindexed_without_token.status_code == 503
    assert "not established this repository" in unindexed_without_token.text
    assert "Required external action" not in unindexed_without_token.text
    assert owner_comment_writeback.ENV_TOKEN not in unindexed_without_token.text

    unknown = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "not-in-estate",
            "comment": "hello",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers=headers,
    )
    assert unknown.status_code == 404

    async def exact_public(name, *, refresh=False, coalesce=True):
        assert (refresh, coalesce) == (True, False)
        return _public_lookup(name)

    monkeypatch.setattr(estate_reader, "read_public_repository", exact_public)
    _install_overview(monkeypatch, _summary())
    missing = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "hello",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers=headers,
    )
    assert missing.status_code == 503
    assert owner_comment_writeback.ENV_TOKEN in missing.text
    assert "Submission is unavailable" in missing.text


def test_malformed_write_token_never_reaches_owner_html(client, monkeypatch):
    _install_overview(monkeypatch, _summary())
    sentinel = "fleet-super\nsecret"
    monkeypatch.setenv(owner_comment_writeback.ENV_TOKEN, sentinel)

    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "hello",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )

    assert response.status_code == 503
    assert sentinel not in response.text
    assert "invalid header characters" in response.text


def test_failed_writeback_is_escaped_and_never_called_durable(client, monkeypatch):
    _install_overview(monkeypatch, _summary())

    async def fake_submit(
        repository, comment, *, context=None, submission_key=None
    ):
        return owner_comment_writeback.OwnerCommentWritebackResult(
            state="failed_retryable",
            repository=repository,
            error="upstream <script>alert(1)</script> failed",
        )

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "Please retry this exactly.",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 503
    assert "Nothing is being called durable" in response.text
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "Please retry this exactly." in response.text


def test_surrogate_writeback_error_cannot_break_owner_response(client, monkeypatch):
    _install_overview(monkeypatch, _summary())

    async def fake_submit(
        repository, comment, *, context=None, submission_key=None
    ):
        return owner_comment_writeback.OwnerCommentWritebackResult(
            state="failed",
            repository=repository,
            error="\ud800",
        )

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "Preserve this retry text.",
            "public_acknowledgement": "yes",
            "submission_key": SUBMISSION_KEY,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )

    assert response.status_code == 409
    assert "invalid Unicode error body" in response.text
    assert "Preserve this retry text." in response.text


def test_public_detail_escapes_comment_context_and_consumption_metadata(
    client, monkeypatch
):
    summary = _summary()
    record_source = estate.SourceReference(
        label="Fleet Manager owner-comment record",
        url=(
            "https://github.com/menno420/fleet-manager/blob/main/"
            "docs/owner-comments/websites/abc.json"
        ),
        repository="fleet-manager",
        path="docs/owner-comments/websites/abc.json",
        freshness=estate.Freshness.live(
            datetime(2026, 8, 27, 12, tzinfo=UTC)
        ),
    )
    record = estate.OwnerCommentRecord(
        id="abc",
        repository="websites",
        comment="<script>alert('comment')</script>",
        created_at=datetime(2026, 8, 27, 12, tzinfo=UTC),
        state="unconsumed",
        source_surface="control-plane",
        source_context="javascript:alert('context')",
        source=record_source,
    )
    feedback = estate.OwnerCommentCollection(
        unconsumed=(record,),
        freshness=record_source.freshness,
        source=record_source,
    )
    detail = estate.RepositoryDetail(
        summary=summary,
        why_it_exists=summary.purpose,
        owner_feedback=feedback,
    )

    async def fake_detail(name, refresh=False):
        return detail

    monkeypatch.setattr(estate_service, "detail", fake_detail)
    response = client.get("/repos/websites")
    assert response.status_code == 200
    assert "<script>alert('comment')</script>" not in response.text
    assert "&lt;script&gt;alert" in response.text
    assert 'href="javascript:' not in response.text
    assert "Context: javascript:alert" in response.text
