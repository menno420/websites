"""Owner-comment UI security, validation, and honest-state contracts."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import (
    config,
    estate,
    estate_service,
    owner,
    owner_comment_writeback,
)
from app.main import app

UTC = timezone.utc
OWNER_PASSWORD = "owner-comment-test-password"
SAME_ORIGIN = "http://testserver"
CROSS_ORIGIN = "https://attacker.example"


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


@pytest.fixture(autouse=True)
def _reset_owner_limits():
    owner.reset_rate_limits()
    yield
    owner.reset_rate_limits()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(config, "SITE_PASSWORD", OWNER_PASSWORD)
    monkeypatch.setenv(owner_comment_writeback.ENV_TOKEN, "fleet-write-token")
    with TestClient(app) as value:
        yield value


def _install_overview(monkeypatch, *repositories):
    async def fake_overview(refresh=False):
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
        },
        headers={**_basic(), "Origin": CROSS_ORIGIN},
    )
    assert response.status_code == 403
    assert not called


def test_submission_preserves_owner_text_and_reports_pending_not_durable(
    client, monkeypatch
):
    _install_overview(monkeypatch, _summary())
    captured = {}
    wording = "  Keep <script>alert(1)</script> & this line\nexactly.  "

    async def fake_submit(repository, comment, *, context=None):
        captured.update(
            repository=repository,
            comment=comment,
            context=context,
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
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 202
    assert captured == {
        "repository": "websites",
        "comment": wording,
        "context": "/repos/websites",
    }
    assert "Pending Fleet Manager PR — not durable yet" in response.text
    assert "Fleet Manager PR #953" in response.text
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

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": comment,
            "public_acknowledgement": ack,
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 422
    assert needle in response.text


def test_unknown_private_and_missing_token_never_write(client, monkeypatch):
    private = _summary("estate-backups", visibility="private")
    _install_overview(monkeypatch, private)

    async def fake_submit(*args, **kwargs):
        raise AssertionError("unavailable target must not reach writeback")

    monkeypatch.setattr(
        owner_comment_writeback, "submit_owner_comment", fake_submit
    )
    headers = {**_basic(), "Origin": SAME_ORIGIN}
    private_response = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "estate-backups",
            "comment": "public-looking text",
            "public_acknowledgement": "yes",
        },
        headers=headers,
    )
    assert private_response.status_code == 503
    assert "not confidently established as public" in private_response.text

    unknown = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "not-in-estate",
            "comment": "hello",
            "public_acknowledgement": "yes",
        },
        headers=headers,
    )
    assert unknown.status_code == 404

    _install_overview(monkeypatch, _summary())
    monkeypatch.delenv(owner_comment_writeback.ENV_TOKEN, raising=False)
    missing = client.post(
        "/owner/repository-comments/submit",
        data={
            "repository": "websites",
            "comment": "hello",
            "public_acknowledgement": "yes",
        },
        headers=headers,
    )
    assert missing.status_code == 503
    assert owner_comment_writeback.ENV_TOKEN in missing.text
    assert "Submission is unavailable" in missing.text


def test_failed_writeback_is_escaped_and_never_called_durable(client, monkeypatch):
    _install_overview(monkeypatch, _summary())

    async def fake_submit(repository, comment, *, context=None):
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
        },
        headers={**_basic(), "Origin": SAME_ORIGIN},
    )
    assert response.status_code == 503
    assert "Nothing is being called durable" in response.text
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "Please retry this exactly." in response.text


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
