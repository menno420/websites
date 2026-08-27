"""Normalize public Fleet Manager/GitHub reads into the stable estate model.

Routes and templates call this module, never the Markdown reader directly.
The service intentionally keeps the overview cheap (two Fleet Manager files
and one anonymous GitHub listing) and gives a detail request the only bounded
member-repository fan-out.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import replace
from datetime import date, datetime, timezone
from typing import Any, Mapping, Optional
from urllib.parse import quote

from . import config, estate, estate_reader, owner_comments

UTC = timezone.utc


def _datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value or "").strip()
    if not text:
        return None
    date_match = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    if date_match and not re.search(r"\d{2}:\d{2}", text):
        return datetime.fromisoformat(date_match.group(0)).replace(tzinfo=UTC)
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return datetime.fromisoformat(text).replace(tzinfo=UTC)
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, TypeError):
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%MZ").replace(tzinfo=UTC)
        except ValueError:
            return None


def _envelope_freshness(
    result: Mapping[str, Any],
    *,
    fact_as_of: Any = None,
    verified: bool = False,
) -> estate.Freshness:
    retrieved = _datetime(result.get("fetched_at_iso"))
    if not result.get("ok"):
        return estate.Freshness.unavailable(
            retrieved_at=retrieved,
            reason=str(result.get("error") or f"HTTP {result.get('status')}"),
        )
    fact = _datetime(fact_as_of)
    if fact is not None:
        value: datetime | date = (
            fact.date()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(fact_as_of or ""))
            else fact
        )
        if verified:
            return estate.Freshness.last_verified(value, retrieved_at=retrieved)
        return estate.Freshness.measured(value, retrieved_at=retrieved)
    if result.get("cached"):
        if retrieved is None:
            return estate.Freshness.unknown(
                reason="Cached source has no retrieval timestamp."
            )
        return estate.Freshness.measured(retrieved, retrieved_at=retrieved)
    return estate.Freshness.live(retrieved_at=retrieved)


def _source(
    label: str,
    repository: str,
    path: str,
    freshness: estate.Freshness,
    *,
    authority: str,
    available: Optional[bool] = True,
    url: str = "",
    ref: str = "main",
) -> estate.SourceReference:
    if not url and available is True:
        url = (
            f"https://github.com/{config.OWNER}/{repository}/blob/"
            f"{quote(ref, safe='')}/{path}"
            if path
            else f"https://github.com/{config.OWNER}/{repository}"
        )
    return estate.SourceReference(
        label=label,
        url=url,
        repository=repository,
        path=path,
        authority=authority,
        freshness=freshness,
        available=available,
    )


def _concise(text: str, limit: int = 300) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    head = value[: limit + 1]
    stop = max(head.rfind(". "), head.rfind("; "), head.rfind(" — "))
    if stop >= limit // 2:
        return head[: stop + 1].rstrip(" ;—")
    word = head.rfind(" ", 0, limit)
    return head[: max(word, 1)].rstrip(" ,;:") + "…"


def _activity_freshness(
    sources: estate_reader.OverviewSources,
) -> estate.Freshness:
    parse_ok = bool(
        sources.activity.generated_at
        and (
            sources.activity.recognized_sections
            or sources.activity.records
        )
        and not any(
            "malformed" in warning.casefold()
            for warning in sources.activity.warnings
        )
    )
    if sources.activity_result.get("ok") and not parse_ok:
        return estate.Freshness.unavailable(
            retrieved_at=_datetime(
                sources.activity_result.get("fetched_at_iso")
            ),
            reason="Fleet Manager activity log could not be parsed.",
        )
    return _envelope_freshness(
        sources.activity_result,
        fact_as_of=_datetime(sources.activity.generated_at),
    )


def _activity(
    record: estate_reader.ActivityRecord,
    freshness: estate.Freshness,
) -> estate.Activity:
    occurred = _datetime(record.date)
    if record.kind == "in_flight":
        summary = f"In-flight session: {record.title or record.detail or 'untitled'}"
    elif record.kind == "invisible_work":
        summary = "Repository moved without a current session card"
        if record.detail:
            summary += f": {record.detail}"
    else:
        summary = record.title or "Repository session"
        if record.status:
            summary += f" · {record.status}"
    source = estate.SourceReference(
        label="Fleet Manager activity record",
        url=record.source_url,
        repository="fleet-manager",
        path=estate_reader.ACTIVITY_PATH,
        authority="routing",
        freshness=freshness,
        available=True,
    )
    return estate.Activity(
        summary=_concise(summary, 360),
        occurred_at=occurred,
        kind=record.kind,
        source=source,
        freshness=freshness,
    )


def _github_activity(
    public: estate_reader.PublicRepository,
    freshness: estate.Freshness,
) -> Optional[estate.Activity]:
    occurred = _datetime(public.pushed_at)
    if occurred is None:
        return None
    source = estate.SourceReference(
        label="Public GitHub repository metadata",
        url=public.html_url,
        repository=public.name,
        authority="authoritative",
        freshness=freshness,
        available=True,
    )
    return estate.Activity(
        summary="Repository pushed on GitHub",
        occurred_at=occurred,
        kind="github-push",
        source=source,
        freshness=freshness,
    )


def _comments_not_ready() -> estate.OwnerCommentSummary:
    return estate.OwnerCommentSummary(
        freshness=estate.Freshness.unavailable(
            reason="Fleet Manager owner-comment records are not available."
        )
    )


def _aggregate(
    sources: estate_reader.OverviewSources,
    comment_index: Optional[owner_comments.OwnerCommentIndexRead] = None,
) -> tuple[
    estate.EstateOverview,
    dict[str, estate_reader.EstateRow],
    dict[str, estate_reader.PublicRepository],
]:
    public = {item.name.casefold(): item for item in sources.public_repositories}
    grouped: dict[str, list[estate_reader.EstateRow]] = {}
    for row in sources.estate.rows:
        grouped.setdefault(row.name.casefold(), []).append(row)

    activity_freshness = _activity_freshness(sources)
    activities: dict[str, list[estate.Activity]] = {}
    for record in sources.activity.records:
        activities.setdefault(record.repo.casefold(), []).append(
            _activity(record, activity_freshness)
        )

    rows_by_name: dict[str, estate_reader.EstateRow] = {}
    repositories: list[estate.RepositorySummary] = []
    estate_parse_ok = bool(sources.estate.rows)
    estate_source_freshness = (
        _envelope_freshness(sources.estate_result)
        if estate_parse_ok
        else estate.Freshness.unavailable(
            retrieved_at=_datetime(
                sources.estate_result.get("fetched_at_iso")
            ),
            reason="Fleet Manager estate index could not be parsed.",
        )
    )
    listing_freshness = _envelope_freshness(sources.public_repos_result)
    listing_data = sources.public_repos_result.get("data")
    listing_complete = bool(
        sources.public_repos_result.get("ok")
        and isinstance(listing_data, list)
        and len(listing_data) < 100
        and len(sources.public_repositories) == len(listing_data)
    )

    for key, duplicate_rows in grouped.items():
        row = duplicate_rows[0]
        rows_by_name[key] = row
        public_repo = public.get(key)
        explicit_private = bool(
            re.search(
                r"\bPRIVATE\b",
                f"{row.purpose} {row.raw_state}",
                re.IGNORECASE,
            )
        )
        resolution = estate.normalize_repository_status(
            row.state_text,
            section=row.section,
            live_archived=public_repo.archived if public_repo else None,
            additional_raw_statuses=tuple(
                other.state_text for other in duplicate_rows[1:]
            ),
        )
        verified = _datetime(row.verified_date)
        row_freshness = (
            _envelope_freshness(
                sources.estate_result,
                fact_as_of=verified,
                verified=True,
            )
            if verified
            else estate.Freshness.unknown(
                retrieved_at=_datetime(
                    sources.estate_result.get("fetched_at_iso")
                ),
                reason="Fleet Manager row has no verified date.",
            )
        )
        row_activities = list(activities.get(key, ()))
        if public_repo:
            push = _github_activity(public_repo, listing_freshness)
            if push:
                row_activities.append(push)
        row_activities.sort(
            key=lambda item: (
                item.kind == "in_flight",
                item.occurred_at or datetime.min.replace(tzinfo=UTC),
            ),
            reverse=True,
        )

        references: list[estate.SourceReference] = [
            _source(
                "Fleet Manager estate index",
                "fleet-manager",
                estate_reader.ESTATE_PATH,
                row_freshness,
                authority="routing",
                available=estate_parse_ok,
            )
        ]
        if row.layer2_path:
            references.append(
                _source(
                    "Fleet Manager Layer-2 entry",
                    "fleet-manager",
                    row.layer2_path,
                    row_freshness,
                    authority="routing",
                )
            )
        if public_repo:
            references.append(
                estate.SourceReference(
                    label="Public GitHub repository metadata",
                    url=public_repo.html_url,
                    repository=public_repo.name,
                    authority="authoritative",
                    freshness=listing_freshness,
                    available=True,
                )
            )

        live_archive_override = bool(
            public_repo and public_repo.archived is True
        )
        status_source = (
            references[-1] if live_archive_override else references[0]
        )
        status_freshness = (
            listing_freshness if live_archive_override else row_freshness
        )

        warnings = [*row.warnings, *resolution.warnings]
        if len(duplicate_rows) > 1:
            warnings.append(
                "Fleet Manager contains duplicate repository rows; the first "
                "row is shown and the contradiction is preserved."
            )
        if public_repo and public_repo.disabled:
            warnings.append("GitHub reports this repository disabled.")
        if explicit_private:
            visibility = "private"
            github_present: Optional[bool] = None
        elif public_repo:
            visibility = "public"
            github_present = True
        elif listing_complete:
            visibility = "unknown"
            github_present = False
        else:
            visibility = "unknown"
            github_present = None

        repositories.append(
            estate.RepositorySummary(
                name=row.name,
                purpose=_concise(row.purpose_text),
                status=resolution.status,
                raw_status=row.state_text,
                status_freshness=status_freshness,
                status_source=status_source,
                freshness=row_freshness,
                sources=tuple(references),
                activities=tuple(row_activities),
                owner_comments=(
                    owner_comments.summary_for(comment_index, row.name)
                    if comment_index is not None
                    else _comments_not_ready()
                ),
                warnings=tuple(dict.fromkeys(warnings)),
                indexed_by_fleet_manager=True,
                github_present=github_present,
                visibility=visibility,
            )
        )

    for public_repo in sources.unindexed_public_repositories:
        key = public_repo.name.casefold()
        if key in grouped:
            continue
        push = _github_activity(public_repo, listing_freshness)
        github_source = estate.SourceReference(
            label="Public GitHub repository metadata",
            url=public_repo.html_url,
            repository=public_repo.name,
            authority="authoritative",
            freshness=listing_freshness,
            available=True,
        )
        unindexed_archived = public_repo.archived is True
        unindexed_status_freshness = (
            listing_freshness
            if unindexed_archived
            else estate.Freshness.unknown(
                retrieved_at=listing_freshness.retrieved_at,
                reason="Fleet Manager has not established a repository state.",
            )
        )
        repositories.append(
            estate.RepositorySummary(
                name=public_repo.name,
                purpose="",
                status=(
                    estate.RepositoryStatus.ARCHIVED
                    if unindexed_archived
                    else estate.RepositoryStatus.UNKNOWN
                ),
                raw_status="",
                status_freshness=unindexed_status_freshness,
                status_source=github_source,
                freshness=listing_freshness,
                sources=(github_source,),
                activities=(push,) if push else (),
                owner_comments=owner_comments.unavailable_summary(
                    "Repository is not indexed by Fleet Manager; owner comments "
                    "are unavailable."
                ),
                warnings=(
                    "Present in GitHub; not yet indexed by Fleet Manager.",
                ),
                indexed_by_fleet_manager=False,
                github_present=True,
                visibility="public",
            )
        )

    repositories.sort(key=lambda item: item.name.casefold())
    source_refs = (
        _source(
            "Fleet Manager estate index",
            "fleet-manager",
            estate_reader.ESTATE_PATH,
            estate_source_freshness,
            authority="routing",
            available=estate_parse_ok,
        ),
        _source(
            "Fleet Manager activity log",
            "fleet-manager",
            estate_reader.ACTIVITY_PATH,
            activity_freshness,
            authority="routing",
            available=activity_freshness.is_available,
        ),
        estate.SourceReference(
            label="Public GitHub repository listing",
            url=f"https://github.com/{config.OWNER}?tab=repositories",
            repository="",
            authority="authoritative",
            freshness=listing_freshness,
            available=bool(sources.public_repos_result.get("ok")),
        ),
        *((comment_index.source,) if comment_index is not None else ()),
    )
    comment_alignment_warnings: list[str] = []
    if comment_index is not None and comment_index.valid:
        estate_names = {row.name for row in sources.estate.rows}
        comment_names = {row.repository for row in comment_index.rows}
        missing_comments = sorted(estate_names - comment_names, key=str.casefold)
        extra_comments = sorted(comment_names - estate_names, key=str.casefold)
        if missing_comments:
            comment_alignment_warnings.append(
                "Fleet Manager owner-comment index is missing estate "
                "repositories: " + ", ".join(missing_comments)
            )
        if extra_comments:
            comment_alignment_warnings.append(
                "Fleet Manager owner-comment index contains repositories not "
                "present in the estate index: " + ", ".join(extra_comments)
            )
    warnings = tuple(
        dict.fromkeys(
            (
                *sources.warnings,
                *sources.estate.warnings,
                *sources.activity.warnings,
                *(comment_index.warnings if comment_index is not None else ()),
                *comment_alignment_warnings,
            )
        )
    )
    verified_dates = [
        value
        for row in sources.estate.rows
        if (value := _datetime(row.verified_date)) is not None
    ]
    overview_freshness = (
        estate.Freshness.last_verified(
            min(verified_dates).date(),
            retrieved_at=_datetime(sources.estate_result.get("fetched_at_iso")),
        )
        if verified_dates
        else estate_source_freshness
    )
    return (
        estate.EstateOverview(
            repositories=tuple(repositories),
            sources=source_refs,
            freshness=overview_freshness,
            warnings=warnings,
        ),
        rows_by_name,
        public,
    )


async def overview(
    refresh: bool = False,
    *,
    coalesce_public_listing: bool = True,
) -> estate.EstateOverview:
    """Return the cheap, stable catalogue model."""

    reader_kwargs = {"refresh": refresh}
    if not coalesce_public_listing:
        reader_kwargs["coalesce_public_listing"] = False
    sources, comment_index = await asyncio.gather(
        estate_reader.read_overview_sources(**reader_kwargs),
        owner_comments.read_index(refresh=refresh),
    )
    model, _rows, _public = _aggregate(sources, comment_index)
    return model


async def revalidate_owner_comment_repository(
    repository: estate.RepositorySummary,
    *,
    mutation: bool = False,
) -> estate.RepositorySummary:
    """Apply an exact-public observation to one known estate member.

    Fleet Manager's estate index establishes which names are valid review
    targets.  This independent repository-specific read establishes whether
    the selected target may receive a public owner-comment record right now;
    it never depends on the overview listing's pagination. Mutation checks
    are fresh and uncoalesced; form-display checks may use the public cache.
    """

    # Fleet Manager's explicit PRIVATE wording is an estate-owned disclosure
    # boundary, not an old listing observation that GitHub may override.
    if repository.visibility == "private":
        return repository

    lookup = await estate_reader.read_public_repository(
        repository.name,
        refresh=mutation,
        coalesce=not mutation,
    )
    warnings = repository.warnings
    if not lookup.is_public:
        warnings = tuple(
            dict.fromkeys(
                (
                    *warnings,
                    "Anonymous repository-specific visibility check did not "
                    f"prove this target public: {lookup.reason}",
                )
            )
        )
    return replace(
        repository,
        visibility=lookup.visibility,
        github_present=True if lookup.is_public else None,
        warnings=warnings,
    )


_AS_OF_PATTERNS = (
    re.compile(r"\btrue as of\s+\*{0,2}(20\d{2}-\d{2}-\d{2})", re.I),
    re.compile(
        r"\blast (?:verified|updated)\s+\*{0,2}(20\d{2}-\d{2}-\d{2})",
        re.I,
    ),
    re.compile(r"\bupdated:\s*\*{0,2}(20\d{2}-\d{2}-\d{2})", re.I),
)


def _document_date(text: str) -> Optional[str]:
    for pattern in _AS_OF_PATTERNS:
        match = pattern.search(text or "")
        if match:
            return match.group(1)
    return None


def _member_source(
    name: str,
    path: str,
    result: Mapping[str, Any],
    *,
    ref: str,
) -> estate.SourceReference:
    text = result.get("data") if isinstance(result.get("data"), str) else ""
    fact_date = _document_date(text)
    freshness = (
        _envelope_freshness(result, fact_as_of=fact_date, verified=True)
        if fact_date
        else (
            estate.Freshness.unknown(
                retrieved_at=_datetime(result.get("fetched_at_iso")),
                reason="Source provides no fact-as-of date.",
            )
            if result.get("ok")
            else _envelope_freshness(result)
        )
    )
    return _source(
        {
            "README.md": "Repository README",
            "docs/current-state.md": "Repository current state",
            "docs/intent.md": "Repository intent",
            "docs/DESIGN.md": "Repository design",
            "docs/PROJECT-CLOSEOUT.md": "Project closeout",
            "HANDOFF.md": "Repository handoff",
        }.get(path, path),
        name,
        path,
        freshness,
        authority="authoritative",
        available=bool(result.get("ok")),
        ref=ref,
    )


async def detail(
    name: str,
    refresh: bool = False,
) -> Optional[estate.RepositoryDetail]:
    """Return one validated repository review, or None when unknown."""

    if not estate_reader.safe_repo_name(name):
        return None
    raw, comment_index = await asyncio.gather(
        estate_reader.read_overview_sources(refresh=refresh),
        owner_comments.read_index(refresh=refresh),
    )
    overview_model, rows, public = _aggregate(raw, comment_index)
    summary = overview_model.repository(name)
    if summary is None:
        return None
    key = summary.name.casefold()
    row = rows.get(key)
    public_repo = public.get(key)
    member_ref = estate_reader.safe_member_ref(
        public_repo.default_branch if public_repo else "main"
    )
    routed_member_paths = (
        estate_reader.read_first_paths(row.read_first) if row else ()
    )
    detail_task = estate_reader.read_detail_sources(
        summary.name,
        is_public=public_repo is not None,
        layer2_path=row.layer2_path if row else None,
        member_paths=(
            estate_reader.member_probe_paths(row.read_first)
            if row
            else estate_reader.MEMBER_PROBE_PATHS
        ),
        member_ref=member_ref,
        refresh=refresh,
    )
    if summary.indexed_by_fleet_manager:
        detail_sources, owner_feedback = await asyncio.gather(
            detail_task,
            owner_comments.read_repository_comments(
                summary.name,
                expected_summary=summary.owner_comments,
                refresh=refresh,
            ),
        )
    else:
        detail_sources = await detail_task
        owner_feedback = estate.OwnerCommentCollection(
            warnings=(
                "Repository is not indexed by Fleet Manager; owner comments "
                "are unavailable.",
            ),
            freshness=estate.Freshness.unavailable(
                reason="No Fleet Manager owner-comment route exists."
            ),
        )

    warnings: list[str] = []
    important: list[estate.SourceReference] = []
    member_sources: dict[str, estate.SourceReference] = {}
    member_texts: list[tuple[str, str]] = []
    if detail_sources.is_public:
        for path, result in detail_sources.member_results.items():
            if result.get("ok") and isinstance(result.get("data"), str):
                source = _member_source(
                    summary.name, path, result, ref=member_ref
                )
                important.append(source)
                member_sources[path] = source
                member_texts.append((path, result["data"]))
                if estate_reader.is_placeholder_text(result["data"]):
                    warnings.append(f"{path} is an unrendered placeholder.")
            elif result.get("status") not in (404,):
                source = _member_source(
                    summary.name, path, result, ref=member_ref
                )
                important.append(source)
                member_sources[path] = source
    else:
        important.append(
            estate.SourceReference(
                label="Repository-native sources",
                url="",
                repository=summary.name,
                authority="authoritative",
                freshness=estate.Freshness.unavailable(
                    reason="Private or unavailable source was not fetched."
                ),
                available=False,
            )
        )

    layer_text = (
        detail_sources.layer2_result.get("data")
        if detail_sources.layer2_result.get("ok")
        and isinstance(detail_sources.layer2_result.get("data"), str)
        else ""
    )
    layer_source: Optional[estate.SourceReference] = None
    if detail_sources.layer2_path:
        fact_date = _document_date(layer_text)
        layer_source = _source(
            "Fleet Manager Layer-2 entry",
            "fleet-manager",
            detail_sources.layer2_path,
            _envelope_freshness(
                detail_sources.layer2_result,
                fact_as_of=fact_date,
                verified=bool(fact_date),
            ),
            authority="routing",
            available=bool(detail_sources.layer2_result.get("ok")),
        )
        important.append(layer_source)

    situation = ""
    situation_source: Optional[estate.SourceReference] = None
    situation_paths = tuple(
        dict.fromkeys(
            (
                *routed_member_paths,
                "docs/current-state.md",
                "README.md",
                "docs/PROJECT-CLOSEOUT.md",
                "docs/DESIGN.md",
            )
        )
    )
    for preferred in situation_paths:
        text_value = next(
            (body for path, body in member_texts if path == preferred),
            "",
        )
        if text_value and not estate_reader.is_placeholder_text(text_value):
            situation = estate_reader.extract_concise_situation(text_value)
        if situation:
            situation_source = member_sources.get(preferred)
            break
    if not situation and layer_text:
        situation = estate_reader.extract_concise_situation(layer_text)
        if situation:
            situation_source = layer_source
    if not situation:
        situation = summary.purpose_text
        situation_source = summary.sources[0] if summary.sources else None

    # Layer-2 is routing context and may lag the repository. A roadmap is
    # shown only when a repository-native source uses an exact next heading.
    next_thread: Optional[str] = None
    next_thread_source: Optional[estate.SourceReference] = None
    next_paths = tuple(
        dict.fromkeys(
            (
                *routed_member_paths,
                "docs/current-state.md",
                "docs/PROJECT-CLOSEOUT.md",
                "HANDOFF.md",
                "README.md",
            )
        )
    )
    for preferred in next_paths:
        text_value = next(
            (body for path, body in member_texts if path == preferred),
            "",
        )
        next_thread = estate_reader.extract_explicit_next_thread(text_value)
        if next_thread:
            next_thread_source = member_sources.get(preferred)
            break

    in_flight = [
        item for item in summary.activities if item.kind == "in_flight"
    ]
    other_activity = [
        item for item in summary.activities if item.kind != "in_flight"
    ]
    recent_activity = tuple((in_flight + other_activity)[: max(8, len(in_flight))])

    return estate.RepositoryDetail(
        summary=summary,
        current_situation=situation,
        current_situation_source=situation_source,
        why_it_exists=summary.purpose_text,
        recent_activity=recent_activity,
        important_sources=tuple(important),
        current_next_thread=next_thread,
        current_next_thread_source=next_thread_source,
        owner_feedback=owner_feedback,
        warnings=tuple(dict.fromkeys(warnings)),
    )
