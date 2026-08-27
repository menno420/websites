"""Public, bounded readers for the repository-estate projection.

This module is deliberately below the estate domain/model layer.  It knows
how to read the *current record shapes* owned by ``fleet-manager`` and how to
return honest source envelopes, but it does not decide what a repository's
normalised product state means.  Keeping that distinction here makes the
Markdown-backed reader replaceable by a later digest without teaching routes
or templates about Markdown tables.

Privacy is structural: every remote read in this module goes through
``github.fetch_public_file`` or ``github.public_api``.  Neither a configured
server token nor a private-repository Contents fallback is ever used.
"""

from __future__ import annotations

import asyncio
import posixpath
import re
from dataclasses import dataclass, replace
from typing import Any, Awaitable, Mapping, Optional

from . import clock, config, github

FLEET_REPOSITORY = "fleet-manager"
ESTATE_PATH = "docs/ESTATE.md"
ACTIVITY_PATH = "docs/activity/estate-log.md"

# A detail request may inspect these focused orientation sources in the one
# selected public repository.  This tuple is the fan-out bound as well as the
# presentation order; it is not an estate registry.
MEMBER_PROBE_PATHS: tuple[str, ...] = (
    "README.md",
    "docs/current-state.md",
    "docs/intent.md",
    "docs/DESIGN.md",
    "docs/PROJECT-CLOSEOUT.md",
    "HANDOFF.md",
)
DETAIL_CONCURRENCY = 3
MAX_MEMBER_PROBE_PATHS = 9

_SAFE_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$")
_ISO_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_VERIFIED_DATE_RE = re.compile(
    r"\bverified\b[^\d\n]{0,32}(20\d{2}-\d{2}-\d{2})",
    re.IGNORECASE,
)
_LINK_RE = re.compile(r"\[([^]]+)]\(([^)]+)\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_NEXT_HEADINGS = {"next step", "next action", "current next thread"}
_SITUATION_HEADINGS = {
    "the one-paragraph answer",
    "current situation",
    "current state",
    "at a glance",
    "what this is",
    "overview",
}


@dataclass(frozen=True)
class EstateRow:
    """One literal Fleet Manager estate row.

    The Markdown-bearing cells are retained rather than prematurely cleaned:
    the domain layer may choose concise display text while provenance/debug UI
    can still quote the exact upstream wording.
    """

    name: str
    purpose: str
    raw_state: str
    read_first: str
    layer2: str
    layer2_path: Optional[str]
    section: str
    verified_date: Optional[str]
    source_line: int
    warnings: tuple[str, ...] = ()

    @property
    def purpose_text(self) -> str:
        return markdown_to_text(self.purpose)

    @property
    def state_text(self) -> str:
        return markdown_to_text(self.raw_state)


@dataclass(frozen=True)
class EstateParseResult:
    rows: tuple[EstateRow, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActivityRecord:
    """One routed activity signal from the generated estate activity log."""

    kind: str  # session | in_flight | invisible_work
    repo: str
    date: str
    status: str
    venue: str
    model: str
    title: str
    detail: str
    source_url: str
    related_url: str
    source_line: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActivityParseResult:
    generated_at: Optional[str]
    in_flight: tuple[ActivityRecord, ...]
    sessions: tuple[ActivityRecord, ...]
    invisible_work: tuple[ActivityRecord, ...]
    warnings: tuple[str, ...] = ()
    recognized_sections: tuple[str, ...] = ()

    @property
    def records(self) -> tuple[ActivityRecord, ...]:
        return self.in_flight + self.sessions + self.invisible_work


@dataclass(frozen=True)
class PublicRepository:
    """The cheap public metadata retained from the one GitHub listing."""

    name: str
    description: str
    html_url: str
    archived: Optional[bool]
    disabled: Optional[bool]
    pushed_at: str
    updated_at: str
    default_branch: str
    open_issues_count: Optional[int]


@dataclass(frozen=True)
class OverviewSources:
    estate_result: Mapping[str, Any]
    activity_result: Mapping[str, Any]
    public_repos_result: Mapping[str, Any]
    estate: EstateParseResult
    activity: ActivityParseResult
    public_repositories: tuple[PublicRepository, ...]
    unindexed_public_repositories: tuple[PublicRepository, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class DetailSources:
    name: str
    is_public: bool
    layer2_path: Optional[str]
    layer2_result: Mapping[str, Any]
    member_results: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class _Table:
    section: str
    headers: tuple[str, ...]
    header_line: int
    rows: tuple[tuple[int, tuple[str, ...], tuple[str, ...]], ...]


def safe_repo_name(name: str) -> bool:
    """Whether ``name`` is safe to interpolate into any GitHub read path."""

    return bool(_SAFE_REPOSITORY_RE.fullmatch(name or ""))


def safe_member_ref(ref: str) -> str:
    """Return a safe simple default branch, or the conservative main default."""

    if not _SAFE_REF_RE.fullmatch(ref or ""):
        return "main"
    if ref.endswith("/") or any(
        part in {"", ".", ".."} for part in ref.split("/")
    ):
        return "main"
    return ref


def read_first_paths(value: str, *, limit: int = 3) -> tuple[str, ...]:
    """Extract safe file paths from Fleet Manager's literal read-first route.

    The estate cells use inline-code paths joined by arrows or plus signs.
    Directories and prose are deliberately ignored: detail reads are bounded
    file fetches, never a recursive repository crawl.
    """

    paths: list[str] = []
    for candidate in re.findall(r"`([^`]+)`", value or ""):
        candidate = candidate.split("#", 1)[0].split("?", 1)[0].strip()
        if not candidate or candidate.startswith("/") or candidate.endswith("/"):
            continue
        normal = posixpath.normpath(candidate)
        if normal == ".." or normal.startswith("../"):
            continue
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", normal):
            continue
        basename = posixpath.basename(normal)
        if "." not in basename:
            continue
        if normal not in paths:
            paths.append(normal)
        if len(paths) >= limit:
            break
    return tuple(paths)


def member_probe_paths(read_first: str) -> tuple[str, ...]:
    """Route-prescribed files first, then the stable optional detail probes."""

    return tuple(
        dict.fromkeys((*read_first_paths(read_first), *MEMBER_PROBE_PATHS))
    )[:MAX_MEMBER_PROBE_PATHS]


def markdown_to_text(value: str) -> str:
    """Collapse small inline-Markdown constructs into compact plain text."""

    text = str(value or "")
    text = re.sub(r"!\[([^]]*)]\([^)]+\)", r"\1", text)
    text = _LINK_RE.sub(r"\1", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().strip("|")


def _split_table_row(line: str) -> tuple[str, ...]:
    """Split a Markdown table row while respecting escaped pipe characters."""

    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith(r"\|"):
        body = body[:-1]

    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    cells.append("".join(current).strip())
    return tuple(cells)


def _is_separator(cells: tuple[str, ...]) -> bool:
    return bool(cells) and all(
        re.fullmatch(r":?-{2,}:?", cell.replace(" ", "")) for cell in cells
    )


def _tables(markdown: str) -> tuple[_Table, ...]:
    """Return every well-formed Markdown table plus row-local shape warnings."""

    lines = (markdown or "").splitlines()
    section = ""
    found: list[_Table] = []
    index = 0
    while index < len(lines):
        heading = _HEADING_RE.match(lines[index])
        if heading and len(heading.group(1)) == 2:
            section = markdown_to_text(heading.group(2))

        if not lines[index].lstrip().startswith("|") or index + 1 >= len(lines):
            index += 1
            continue
        headers = _split_table_row(lines[index])
        separator = _split_table_row(lines[index + 1])
        if not _is_separator(separator):
            index += 1
            continue

        expected = len(headers)
        table_rows: list[tuple[int, tuple[str, ...], tuple[str, ...]]] = []
        cursor = index + 2
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            cells = _split_table_row(lines[cursor])
            row_warnings: list[str] = []
            if len(cells) < expected:
                row_warnings.append(
                    f"line {cursor + 1}: expected {expected} cells, found {len(cells)}"
                )
                cells = cells + ("",) * (expected - len(cells))
            elif len(cells) > expected:
                row_warnings.append(
                    f"line {cursor + 1}: expected {expected} cells, found {len(cells)}"
                )
                # Retain every byte even when a producer forgot to escape a
                # pipe: only the last cell is ambiguous, so fold overflow
                # there and flag the row instead of discarding it.
                cells = cells[: expected - 1] + (" | ".join(cells[expected - 1 :]),)
            table_rows.append((cursor + 1, cells, tuple(row_warnings)))
            cursor += 1
        found.append(
            _Table(
                section=section,
                headers=headers,
                header_line=index + 1,
                rows=tuple(table_rows),
            )
        )
        index = cursor
    return tuple(found)


def _header_index(headers: tuple[str, ...], predicate: str) -> Optional[int]:
    for index, header in enumerate(headers):
        normal = markdown_to_text(header).lower()
        if predicate == "repo" and normal == "repo":
            return index
        if predicate == "purpose" and (
            normal.startswith("what it is") or normal.startswith("purpose")
        ):
            return index
        if predicate == "state" and (
            normal.startswith("state") or normal.startswith("status")
        ):
            return index
        if predicate == "read_first" and normal.startswith("read first"):
            return index
        if predicate == "layer2" and "layer 2" in normal:
            return index
    return None


def _markdown_link(value: str) -> tuple[str, str]:
    match = _LINK_RE.search(value or "")
    return (match.group(1), match.group(2)) if match else ("", "")


def _estate_layer2_path(value: str) -> Optional[str]:
    _label, target = _markdown_link(value)
    if not target or "://" in target or target.startswith("/"):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    normal = posixpath.normpath(posixpath.join("docs", target))
    if normal == ".." or normal.startswith("../"):
        return None
    if not normal.startswith("docs/repos/"):
        return None
    if normal.endswith("/"):
        normal += "README.md"
    return normal


def _cell(cells: tuple[str, ...], index: Optional[int]) -> str:
    return cells[index].strip() if index is not None and index < len(cells) else ""


def parse_estate(markdown: str) -> EstateParseResult:
    """Parse Fleet Manager's current estate tables without inventing rows."""

    rows: list[EstateRow] = []
    warnings: list[str] = []
    saw_estate_table = False

    for table in _tables(markdown):
        repo_i = _header_index(table.headers, "repo")
        purpose_i = _header_index(table.headers, "purpose")
        state_i = _header_index(table.headers, "state")
        read_i = _header_index(table.headers, "read_first")
        layer_i = _header_index(table.headers, "layer2")
        if None in (repo_i, purpose_i, state_i, read_i, layer_i):
            continue
        saw_estate_table = True

        header_state = _cell(table.headers, state_i)
        header_verified = _VERIFIED_DATE_RE.search(header_state)
        default_verified = header_verified.group(1) if header_verified else None

        for line_no, cells, row_shape_warnings in table.rows:
            name = markdown_to_text(_cell(cells, repo_i))
            row_warnings = list(row_shape_warnings)
            if not safe_repo_name(name):
                warnings.extend(row_warnings)
                warnings.append(
                    f"line {line_no}: invalid or missing repository identifier"
                )
                continue

            raw_state = _cell(cells, state_i)
            verified_match = _VERIFIED_DATE_RE.search(raw_state)
            verified_date = (
                verified_match.group(1) if verified_match else default_verified
            )
            row = EstateRow(
                name=name,
                purpose=_cell(cells, purpose_i),
                raw_state=raw_state,
                read_first=_cell(cells, read_i),
                layer2=_cell(cells, layer_i),
                layer2_path=_estate_layer2_path(_cell(cells, layer_i)),
                section=table.section,
                verified_date=verified_date,
                source_line=line_no,
                warnings=tuple(row_warnings),
            )
            rows.append(row)
            warnings.extend(row_warnings)

    if not saw_estate_table:
        warnings.append("no estate repository tables found")

    # Preserve every duplicate row; annotate every affected record so a
    # domain/UI consumer cannot accidentally make a silent last-write-wins
    # registry out of contradictory upstream text.
    positions: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        positions.setdefault(row.name.lower(), []).append(index)
    for indexes in positions.values():
        if len(indexes) < 2:
            continue
        name = rows[indexes[0]].name
        lines = ", ".join(str(rows[i].source_line) for i in indexes)
        duplicate_warning = f"duplicate repository {name!r} at lines {lines}"
        warnings.append(duplicate_warning)
        signatures = {
            (
                markdown_to_text(rows[i].purpose).casefold(),
                markdown_to_text(rows[i].raw_state).casefold(),
                markdown_to_text(rows[i].read_first).casefold(),
                rows[i].layer2_path,
            )
            for i in indexes
        }
        contradiction_warning = ""
        if len(signatures) > 1:
            contradiction_warning = (
                f"contradictory repository {name!r} records at lines {lines}"
            )
            warnings.append(contradiction_warning)
        for i in indexes:
            additions = (duplicate_warning,) + (
                (contradiction_warning,) if contradiction_warning else ()
            )
            rows[i] = replace(rows[i], warnings=rows[i].warnings + additions)

    return EstateParseResult(rows=tuple(rows), warnings=tuple(warnings))


def _activity_doc_url() -> str:
    return (
        f"https://github.com/{config.OWNER}/{FLEET_REPOSITORY}/blob/main/"
        f"{ACTIVITY_PATH}"
    )


def _link_url(value: str) -> str:
    _label, target = _markdown_link(value)
    return target


def _link_label(value: str) -> str:
    label, _target = _markdown_link(value)
    return markdown_to_text(label or value)


def parse_activity(markdown: str) -> ActivityParseResult:
    """Parse the generated activity log's three owner-relevant record sets."""

    generated_match = re.search(
        r"\*\*Generated:\*\*\s*(20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}Z)",
        markdown or "",
        re.IGNORECASE,
    )
    generated_at = generated_match.group(1) if generated_match else None
    warnings: list[str] = []
    if not generated_at:
        warnings.append("activity log generated timestamp missing")

    in_flight: list[ActivityRecord] = []
    sessions: list[ActivityRecord] = []
    invisible: list[ActivityRecord] = []
    recognized_sections: list[str] = []
    source_doc = _activity_doc_url()

    for table in _tables(markdown):
        heading = table.section.casefold()
        headers = {markdown_to_text(h).casefold(): i for i, h in enumerate(table.headers)}

        if heading.startswith("in flight right now"):
            recognized_sections.append("in_flight")
            required = ("repo", "pr", "venue", "card")
            if not all(key in headers for key in required):
                warnings.append(
                    f"line {table.header_line}: malformed in-flight table header"
                )
                continue
            for line_no, cells, row_warnings in table.rows:
                repo = markdown_to_text(_cell(cells, headers["repo"]))
                if not safe_repo_name(repo):
                    warnings.append(f"line {line_no}: invalid in-flight repository")
                    continue
                warnings.extend(row_warnings)
                card = _cell(cells, headers["card"])
                pr = _cell(cells, headers["pr"])
                in_flight.append(
                    ActivityRecord(
                        kind="in_flight",
                        repo=repo,
                        date="",
                        status="in-progress",
                        venue=markdown_to_text(_cell(cells, headers["venue"])),
                        model="",
                        title=_link_label(card),
                        detail=markdown_to_text(pr),
                        source_url=_link_url(card) or _link_url(pr) or source_doc,
                        related_url=_link_url(pr),
                        source_line=line_no,
                        warnings=row_warnings,
                    )
                )

        elif heading == "sessions, newest first":
            recognized_sections.append("sessions")
            required = ("date", "repo", "venue", "model", "status", "card")
            if not all(key in headers for key in required):
                warnings.append(
                    f"line {table.header_line}: malformed sessions table header"
                )
                continue
            for line_no, cells, row_warnings in table.rows:
                repo = markdown_to_text(_cell(cells, headers["repo"]))
                if not safe_repo_name(repo):
                    warnings.append(f"line {line_no}: invalid session repository")
                    continue
                warnings.extend(row_warnings)
                card = _cell(cells, headers["card"])
                raw_date = markdown_to_text(_cell(cells, headers["date"]))
                date_match = _ISO_DATE_RE.search(raw_date)
                sessions.append(
                    ActivityRecord(
                        kind="session",
                        repo=repo,
                        date=date_match.group(1) if date_match else raw_date,
                        status=markdown_to_text(_cell(cells, headers["status"])),
                        venue=markdown_to_text(_cell(cells, headers["venue"])),
                        model=markdown_to_text(_cell(cells, headers["model"])),
                        title=_link_label(card),
                        detail="",
                        source_url=_link_url(card) or source_doc,
                        related_url="",
                        source_line=line_no,
                        warnings=row_warnings,
                    )
                )

        elif heading.startswith("invisible work"):
            recognized_sections.append("invisible_work")
            # The prose heading may grow, while the literal columns are stable.
            repo_i = headers.get("repo")
            push_i = headers.get("last push")
            why_i = headers.get("why it is here")
            if None in (repo_i, push_i, why_i):
                warnings.append(
                    f"line {table.header_line}: malformed invisible-work table header"
                )
                continue
            for line_no, cells, row_warnings in table.rows:
                repo = markdown_to_text(_cell(cells, repo_i))
                if not safe_repo_name(repo):
                    warnings.append(f"line {line_no}: invalid invisible-work repository")
                    continue
                warnings.extend(row_warnings)
                invisible.append(
                    ActivityRecord(
                        kind="invisible_work",
                        repo=repo,
                        date=markdown_to_text(_cell(cells, push_i)),
                        status="unexplained",
                        venue="",
                        model="",
                        title="Invisible work",
                        detail=markdown_to_text(_cell(cells, why_i)),
                        source_url=source_doc,
                        related_url=f"https://github.com/{config.OWNER}/{repo}",
                        source_line=line_no,
                        warnings=row_warnings,
                    )
                )

    return ActivityParseResult(
        generated_at=generated_at,
        in_flight=tuple(in_flight),
        sessions=tuple(sessions),
        invisible_work=tuple(invisible),
        warnings=tuple(warnings),
        recognized_sections=tuple(dict.fromkeys(recognized_sections)),
    )


def _failure_envelope(source: str, reason: str) -> dict[str, Any]:
    now = clock.now().replace(microsecond=0)
    return {
        "ok": False,
        "status": 0,
        "data": None,
        "error": github.short_reason(reason),
        "fetched_at": now.strftime("%H:%M:%S UTC"),
        "fetched_at_iso": now.isoformat().replace("+00:00", "Z"),
        "cached": False,
        "url": source,
    }


async def _guarded(awaitable: Awaitable[Mapping[str, Any]], source: str) -> Mapping[str, Any]:
    try:
        return await awaitable
    except Exception as exc:  # a partial upstream must not blank the page
        return _failure_envelope(source, f"{type(exc).__name__}: {exc}")


def _text_result(result: Mapping[str, Any]) -> str:
    data = result.get("data")
    return data if result.get("ok") and isinstance(data, str) else ""


def _public_repository(item: Any) -> Optional[PublicRepository]:
    if not isinstance(item, dict):
        return None
    name = item.get("name")
    if not isinstance(name, str) or not safe_repo_name(name):
        return None
    # Defence in depth: the anonymous endpoint should never return a private
    # row, but a malformed proxy/mock must not expand the public projection.
    if item.get("private") is True or item.get("visibility") == "private":
        return None
    expected_url = f"https://github.com/{config.OWNER}/{name}"
    value_url = item.get("html_url")
    html_url = value_url if value_url == expected_url else expected_url

    archived = item.get("archived")
    disabled = item.get("disabled")
    issues = item.get("open_issues_count")
    return PublicRepository(
        name=name,
        description=item.get("description") if isinstance(item.get("description"), str) else "",
        html_url=html_url,
        archived=archived if isinstance(archived, bool) else None,
        disabled=disabled if isinstance(disabled, bool) else None,
        pushed_at=item.get("pushed_at") if isinstance(item.get("pushed_at"), str) else "",
        updated_at=item.get("updated_at") if isinstance(item.get("updated_at"), str) else "",
        default_branch=(
            item.get("default_branch")
            if isinstance(item.get("default_branch"), str)
            else ""
        ),
        open_issues_count=issues if isinstance(issues, int) and not isinstance(issues, bool) else None,
    )


async def read_overview_sources(
    refresh: bool = False,
    *,
    coalesce_public_listing: bool = True,
) -> OverviewSources:
    """Fetch the overview's three cheap public sources, with no repo fan-out."""

    listing_path = (
        f"/users/{config.OWNER}/repos?type=owner&per_page=100"
        "&sort=pushed&direction=desc"
    )
    estate_result, activity_result, public_repos_result = await asyncio.gather(
        _guarded(
            github.fetch_public_file(
                FLEET_REPOSITORY, ESTATE_PATH, ref="main", refresh=refresh
            ),
            f"{FLEET_REPOSITORY}/{ESTATE_PATH}",
        ),
        _guarded(
            github.fetch_public_file(
                FLEET_REPOSITORY, ACTIVITY_PATH, ref="main", refresh=refresh
            ),
            f"{FLEET_REPOSITORY}/{ACTIVITY_PATH}",
        ),
        _guarded(
            github.public_api(
                listing_path,
                refresh=refresh,
                coalesce=coalesce_public_listing,
            ),
            f"api.github.com{listing_path}",
        ),
    )

    estate = parse_estate(_text_result(estate_result))
    activity = parse_activity(_text_result(activity_result))
    warnings: list[str] = []
    if not estate_result.get("ok"):
        warnings.append(
            "Fleet Manager estate index unavailable: "
            + str(estate_result.get("error") or f"HTTP {estate_result.get('status')}")
        )
    if not activity_result.get("ok"):
        warnings.append(
            "Fleet Manager activity log unavailable: "
            + str(activity_result.get("error") or f"HTTP {activity_result.get('status')}")
        )

    public_rows: list[PublicRepository] = []
    listing_data = public_repos_result.get("data")
    if public_repos_result.get("ok") and isinstance(listing_data, list):
        for index, item in enumerate(listing_data):
            public_repo = _public_repository(item)
            if public_repo is not None:
                public_rows.append(public_repo)
            elif isinstance(item, dict) and (
                item.get("private") is True or item.get("visibility") == "private"
            ):
                warnings.append(
                    f"public repository listing row {index} was private and was suppressed"
                )
            else:
                warnings.append(f"public repository listing row {index} was malformed")
    elif public_repos_result.get("ok"):
        warnings.append("public repository listing returned an unexpected payload")
    else:
        warnings.append(
            "public repository listing unavailable: "
            + str(
                public_repos_result.get("error")
                or f"HTTP {public_repos_result.get('status')}"
            )
        )

    indexed_names = {row.name.casefold() for row in estate.rows}
    unindexed = [
        repo for repo in public_rows if repo.name.casefold() not in indexed_names
    ]
    return OverviewSources(
        estate_result=estate_result,
        activity_result=activity_result,
        public_repos_result=public_repos_result,
        estate=estate,
        activity=activity,
        public_repositories=tuple(public_rows),
        unindexed_public_repositories=tuple(unindexed),
        warnings=tuple(warnings),
    )


def normalize_layer2_path(name: str, layer2_path: Optional[str]) -> Optional[str]:
    """Accept only the selected repo's conventional Fleet Manager entry."""

    if not layer2_path:
        return None
    _label, linked = _markdown_link(layer2_path)
    candidate = linked or layer2_path
    if "://" in candidate or candidate.startswith("/"):
        return None
    candidate = candidate.split("#", 1)[0].split("?", 1)[0].strip()
    if candidate.startswith("repos/"):
        candidate = "docs/" + candidate
    candidate = posixpath.normpath(candidate)
    if candidate == f"docs/repos/{name}":
        candidate += "/README.md"
    expected = f"docs/repos/{name}/README.md"
    return expected if candidate == expected else None


async def read_detail_sources(
    name: str,
    is_public: bool,
    layer2_path: Optional[str],
    member_paths: Optional[tuple[str, ...]] = None,
    member_ref: str = "main",
    refresh: bool = False,
) -> DetailSources:
    """Read Fleet Manager + focused files for one validated repository only."""

    if not safe_repo_name(name):
        raise ValueError("invalid repository identifier")

    normal_layer2 = normalize_layer2_path(name, layer2_path)
    semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

    selected_member_ref = safe_member_ref(member_ref)

    async def fetch(repo: str, path: str, *, ref: str = "main") -> Mapping[str, Any]:
        async with semaphore:
            return await _guarded(
                github.fetch_public_file(repo, path, ref=ref, refresh=refresh),
                f"{repo}/{path}",
            )

    layer_task = (
        asyncio.create_task(fetch(FLEET_REPOSITORY, normal_layer2))
        if normal_layer2
        else None
    )

    selected_member_paths = tuple(
        dict.fromkeys(member_paths or MEMBER_PROBE_PATHS)
    )[:MAX_MEMBER_PROBE_PATHS]

    if is_public:
        member_tasks = {
            path: asyncio.create_task(
                fetch(name, path, ref=selected_member_ref)
            )
            for path in selected_member_paths
        }
        if member_tasks:
            await asyncio.gather(*member_tasks.values())
        member_results: dict[str, Mapping[str, Any]] = {
            path: task.result() for path, task in member_tasks.items()
        }
    else:
        member_results = {
            path: _failure_envelope(
                f"{name}/{path}",
                "private or unavailable source was not fetched",
            )
            for path in selected_member_paths
        }

    if layer_task is not None:
        layer_result = await layer_task
    else:
        layer_result = _failure_envelope(
            f"{FLEET_REPOSITORY}/docs/repos/{name}/README.md",
            "no Fleet Manager Layer-2 record is indexed",
        )

    return DetailSources(
        name=name,
        is_public=is_public,
        layer2_path=normal_layer2,
        layer2_result=layer_result,
        member_results=member_results,
    )


def is_placeholder_text(text: str) -> bool:
    """Identify an unrendered template/placeholder without guessing content."""

    value = str(text or "").strip()
    if not value:
        return True
    if re.search(r"\$\{[^}]+}|\{\{[^}]+}}", value):
        return True
    plain = markdown_to_text(value).casefold().strip(" .:-")
    if re.fullmatch(
        r"(?:tbd|todo|unknown|placeholder|coming soon|none yet|not written yet)",
        plain,
    ):
        return True
    if re.search(r"\b(?:fill|replace) (?:this|me|in)\b", plain):
        return True
    return bool(re.fullmatch(r"<[^>]*(?:todo|tbd|placeholder)[^>]*>", value, re.I))


def _normal_heading(value: str) -> str:
    return markdown_to_text(value).casefold().rstrip(":").strip()


def _section_body(markdown: str, accepted: set[str]) -> list[str]:
    lines = (markdown or "").splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        heading = _HEADING_RE.match(lines[index])
        if not heading or _normal_heading(heading.group(2)) not in accepted:
            index += 1
            continue
        index += 1
        body: list[str] = []
        while index < len(lines) and not _HEADING_RE.match(lines[index]):
            body.append(lines[index])
            index += 1
        blocks.append("\n".join(body).strip())
    return blocks


def _first_prose_block(body: str) -> str:
    for block in re.split(r"\n\s*\n", body or ""):
        lines: list[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("|"):
                continue
            stripped = re.sub(r"^>\s?", "", stripped)
            stripped = re.sub(r"^[-*+]\s+", "", stripped)
            stripped = re.sub(r"^\d+[.)]\s+", "", stripped)
            lines.append(stripped)
        prose = markdown_to_text(" ".join(lines))
        if prose and not is_placeholder_text(prose):
            return prose
    return ""


def _truncate_prose(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars + 1]
    sentence = max(head.rfind(". "), head.rfind("? "), head.rfind("! "))
    if sentence >= max_chars // 2:
        return head[: sentence + 1].strip()
    word = head.rfind(" ", 0, max_chars)
    return head[: max(word, 1)].rstrip(" ,;:") + "…"


def extract_concise_situation(markdown: str, max_chars: int = 360) -> str:
    """Return source-grounded orientation prose, or ``""`` when unknown."""

    if is_placeholder_text(markdown):
        return ""
    for body in _section_body(markdown, _SITUATION_HEADINGS):
        prose = _first_prose_block(body)
        if prose:
            return _truncate_prose(prose, max_chars)

    # README fallback: first ordinary paragraph after the title.  Metadata
    # blockquotes, tables, headings and badges are not treated as a summary.
    paragraphs = re.split(r"\n\s*\n", markdown or "")
    for paragraph in paragraphs:
        stripped = paragraph.lstrip()
        if (
            not stripped
            or stripped.startswith("#")
            or stripped.startswith(">")
            or stripped.startswith("|")
            or stripped.startswith("![")
        ):
            continue
        prose = _first_prose_block(paragraph)
        if prose:
            return _truncate_prose(prose, max_chars)
    return ""


def extract_explicit_next_thread(markdown: str, max_chars: int = 360) -> Optional[str]:
    """Return a next thread only when an exact, explicit heading establishes it."""

    if is_placeholder_text(markdown):
        return None
    for body in _section_body(markdown, _NEXT_HEADINGS):
        prose = _first_prose_block(body)
        if prose:
            return _truncate_prose(prose, max_chars)
    return None
