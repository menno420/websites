"""Owner-visible repository catalogue and detail route contracts."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app import estate, estate_service
from app.main import app

UTC = timezone.utc


def _source(available=True):
    return estate.SourceReference(
        label="Fleet Manager estate index",
        url=(
            "https://github.com/menno420/fleet-manager/blob/main/docs/ESTATE.md"
            if available
            else ""
        ),
        repository="fleet-manager",
        path="docs/ESTATE.md",
        authority="routing",
        freshness=estate.Freshness.last_verified(
            datetime(2026, 8, 26, tzinfo=UTC),
            now=datetime(2026, 8, 27, tzinfo=UTC),
        ),
        available=available,
    )


def _summary(name="alpha", status=estate.RepositoryStatus.ACTIVE, **kwargs):
    activity = estate.Activity(
        "Completed a useful session",
        datetime(2026, 8, 27, 9, tzinfo=UTC),
        source=_source(),
        freshness=estate.Freshness.live(
            datetime(2026, 8, 27, 10, tzinfo=UTC)
        ),
    )
    values = {
        "name": name,
        "purpose": f"{name} product purpose",
        "status": status,
        "raw_status": status.value,
        "status_freshness": estate.Freshness.live(
            datetime(2026, 8, 27, 10, tzinfo=UTC)
        ),
        "status_source": _source(),
        "freshness": estate.Freshness.last_verified(
            datetime(2026, 8, 26, tzinfo=UTC),
            now=datetime(2026, 8, 27, tzinfo=UTC),
        ),
        "sources": (_source(),),
        "activities": (activity,),
        "owner_comments": estate.OwnerCommentSummary(
            0,
            0,
            freshness=estate.Freshness.live(
                datetime(2026, 8, 27, 10, tzinfo=UTC)
            ),
        ),
        "visibility": "public",
    }
    values.update(kwargs)
    return estate.RepositorySummary(**values)


def _overview():
    return estate.EstateOverview(
        repositories=(
            _summary("alpha", estate.RepositoryStatus.ACTIVE),
            _summary(
                "beta",
                estate.RepositoryStatus.PAUSED,
                warnings=("Source disagreement needs review.",),
            ),
            _summary(
                "private-tool",
                estate.RepositoryStatus.INFRASTRUCTURE,
                visibility="private",
                github_present=None,
            ),
        ),
        sources=(_source(),),
        freshness=_source().freshness,
    )


def _detail():
    summary = _summary()
    return estate.RepositoryDetail(
        summary=summary,
        current_situation="Alpha is useful and currently verified.",
        current_situation_source=_source(),
        why_it_exists=summary.purpose,
        recent_activity=summary.activities,
        important_sources=(_source(),),
    )


def test_repos_renders_visual_cards_filters_and_provenance(monkeypatch):
    async def fake_overview(refresh=False):
        return _overview()

    monkeypatch.setattr(estate_service, "overview", fake_overview)
    with TestClient(app) as client:
        response = client.get("/repos")
    assert response.status_code == 200
    assert "repositories — the software estate" in response.text
    assert response.text.count('class="card repo-card') == 3
    assert 'href="/repos/alpha"' in response.text
    assert "last meaningful activity" in response.text
    assert "Last verified" in response.text
    assert "Fleet Manager estate index" in response.text
    assert 'class="repo-grid"' in response.text
    assert "<table" not in response.text


def test_repos_filters_by_state_and_attention(monkeypatch):
    async def fake_overview(refresh=False):
        return _overview()

    monkeypatch.setattr(estate_service, "overview", fake_overview)
    with TestClient(app) as client:
        paused = client.get("/repos?state=paused")
        attention = client.get("/repos?signal=needs-attention")
    assert 'data-row-id="repo-beta"' in paused.text
    assert 'data-row-id="repo-alpha"' not in paused.text
    assert 'data-row-id="repo-beta"' in attention.text
    assert 'data-row-id="repo-alpha"' not in attention.text


def test_known_detail_renders_sections_and_honest_next_thread(monkeypatch):
    async def fake_detail(name, refresh=False):
        return _detail() if name == "alpha" else None

    monkeypatch.setattr(estate_service, "detail", fake_detail)
    with TestClient(app) as client:
        response = client.get("/repos/alpha")
    assert response.status_code == 200
    for heading in (
        "at a glance",
        "current situation",
        "recent activity",
        "current next thread",
        "owner feedback",
        "important sources",
        "provenance & freshness",
    ):
        assert heading in response.text
    assert estate.NEXT_THREAD_UNKNOWN in response.text
    assert "Source:" in response.text
    assert "Fleet Manager estate index" in response.text
    assert "Nothing queued only in this website" in response.text


def test_unknown_or_traversal_repository_is_not_a_detail_page(monkeypatch):
    calls = []

    async def fake_detail(name, refresh=False):
        calls.append(name)
        return None

    monkeypatch.setattr(estate_service, "detail", fake_detail)
    with TestClient(app) as client:
        unknown = client.get("/repos/not-indexed")
        traversal = client.get("/repos/%2E%2E%2Fsecret")
    assert unknown.status_code == 404
    assert traversal.status_code in (404, 422)
    assert "not-indexed" in calls


def test_private_unavailable_source_has_no_private_link(monkeypatch):
    summary = _summary(
        "private-tool",
        estate.RepositoryStatus.INFRASTRUCTURE,
        visibility="private",
        sources=(_source(),),
    )
    private_source = estate.SourceReference(
        label="Repository-native sources",
        url="",
        repository="private-tool",
        authority="authoritative",
        freshness=estate.Freshness.unavailable(reason="not fetched"),
        available=False,
    )
    detail = estate.RepositoryDetail(
        summary=summary,
        current_situation="Only intentionally public routing context.",
        important_sources=(private_source,),
    )

    async def fake_detail(name, refresh=False):
        return detail

    monkeypatch.setattr(estate_service, "detail", fake_detail)
    with TestClient(app) as client:
        response = client.get("/repos/private-tool")
    assert response.status_code == 200
    assert "Private or" in response.text and "unavailable records are labelled" in response.text
    assert "private-tool/blob" not in response.text
    assert "Unavailable" in response.text


def test_untrusted_text_is_escaped(monkeypatch):
    malicious = _summary(
        name="alpha",
        purpose="<script>alert(1)</script>",
        raw_status="<img src=x onerror=alert(1)>",
    )
    model = estate.EstateOverview(
        repositories=(malicious,),
        sources=(_source(),),
        freshness=_source().freshness,
    )

    async def fake_overview(refresh=False):
        return model

    monkeypatch.setattr(estate_service, "overview", fake_overview)
    with TestClient(app) as client:
        response = client.get("/repos")
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
    assert "onerror=alert(1)&gt;" in response.text
