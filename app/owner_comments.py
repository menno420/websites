"""Public Fleet Manager owner-comment reads and contract normalization.

Fleet Manager owns the durable records.  This module is a bounded, anonymous
read projection only: it uses :func:`github.fetch_public_file` exclusively,
retains source envelopes/provenance, and converts malformed or contradictory
upstream data into explicit unavailable/unknown states instead of zeroes.

The estate overview reads only ``index.json``.  A selected repository detail
adds its generated README and at most ``MAX_ACTIVE_RECORDS`` active plus
``MAX_CONSUMED_RECORDS`` historical JSON fetches, with bounded concurrency.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional
from urllib.parse import quote

from . import config, estate, github

UTC = timezone.utc
FLEET_REPOSITORY = "fleet-manager"
ROOT_INDEX_PATH = "docs/owner-comments/index.json"
SCHEMA_VERSION = 1
MAX_ACTIVE_RECORDS = 50
MAX_CONSUMED_RECORDS = 10
DETAIL_CONCURRENCY = 4
DETAIL_TIMEOUT_SECONDS = 8.0
MAX_INDEX_CHARS = 1_000_000
MAX_COMMENT_CHARS = 20_000
MAX_CONTEXT_CHARS = 1_000
MAX_INDEX_RECORDS = 10_000

DERIVED_FROM = (
    "docs/ESTATE.md",
    "docs/owner-comments/<repo>/*.json",
    "docs/owner-comments/<repo>/consumed/*.json",
)

_ROOT_KEYS = {"schema_version", "derived_from", "repositories"}
_ROOT_ROW_KEYS = {
    "repository",
    "index",
    "unconsumed_count",
    "consumed_count",
    "latest_unconsumed_at",
    "latest_consumed_at",
}
_RECORD_REQUIRED_KEYS = {
    "schema_version",
    "id",
    "repository",
    "created_at",
    "state",
    "source",
    "comment",
}
_ID_RE = re.compile(
    r"^(?!(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$))"
    r"(?!.*\.\.)(?!.*\.lock$)(?!.*\.$)"
    r"[a-z0-9][a-z0-9._-]{2,79}$"
)
_REPOSITORY_RE = re.compile(
    r"^(?!(?:README\.md|index\.json|record\.schema\.json)$)"
    r"(?!(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$))"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9_-])?$",
    re.IGNORECASE,
)
_SURFACE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


class OwnerCommentContractError(ValueError):
    """A public Fleet Manager comment source violates contract v1."""


@dataclass(frozen=True)
class OwnerCommentIndexRow:
    repository: str
    index_path: str
    unconsumed_count: int
    consumed_count: int
    latest_unconsumed_at: Optional[datetime]
    latest_consumed_at: Optional[datetime]


@dataclass(frozen=True)
class OwnerCommentIndexRead:
    rows: tuple[OwnerCommentIndexRow, ...]
    source: estate.SourceReference
    warnings: tuple[str, ...] = ()
    valid: bool = False

    def row(self, repository: str) -> Optional[OwnerCommentIndexRow]:
        return next(
            (item for item in self.rows if item.repository == repository),
            None,
        )


@dataclass(frozen=True)
class _RepositoryIndexEntry:
    id: str
    created_at_text: str
    created_at: datetime
    state: str
    source_surface: Optional[str] = None
    consumed_at_text: Optional[str] = None
    consumed_at: Optional[datetime] = None


@dataclass(frozen=True)
class _RepositoryIndex:
    repository: str
    active: tuple[_RepositoryIndexEntry, ...]
    consumed: tuple[_RepositoryIndexEntry, ...]


def _has_forbidden_codepoint(value: str) -> bool:
    return "\x00" in value or any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not _UTC_TIMESTAMP_RE.fullmatch(value):
        raise OwnerCommentContractError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise OwnerCommentContractError(
            f"{label} must be a real RFC3339 UTC timestamp"
        ) from exc
    return parsed.astimezone(UTC)


def _bounded_index_count(value: str, label: str) -> int:
    if len(value) > len(str(MAX_INDEX_RECORDS)):
        raise OwnerCommentContractError(f"{label} exceeds the bounded count")
    try:
        count = int(value)
    except ValueError as exc:
        raise OwnerCommentContractError(f"{label} is not an integer") from exc
    if count > MAX_INDEX_RECORDS:
        raise OwnerCommentContractError(f"{label} exceeds the bounded count")
    if value != str(count):
        raise OwnerCommentContractError(f"{label} is not canonical")
    return count


def _retrieved_at(result: Mapping[str, Any]) -> Optional[datetime]:
    value = result.get("fetched_at_iso")
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _envelope_freshness(result: Mapping[str, Any]) -> estate.Freshness:
    retrieved = _retrieved_at(result)
    if not result.get("ok"):
        return estate.Freshness.unavailable(
            retrieved_at=retrieved,
            reason=str(result.get("error") or f"HTTP {result.get('status')}"),
        )
    if result.get("cached"):
        if retrieved is None:
            return estate.Freshness.unknown(
                reason="Cached owner-comment source has no retrieval timestamp."
            )
        return estate.Freshness.measured(retrieved, retrieved_at=retrieved)
    return estate.Freshness.live(retrieved_at=retrieved)


def _source(
    path: str,
    freshness: estate.Freshness,
    *,
    label: str,
    available: Optional[bool],
) -> estate.SourceReference:
    safe_path = quote(path, safe="/")
    return estate.SourceReference(
        label=label,
        url=(
            f"https://github.com/{config.OWNER}/{FLEET_REPOSITORY}/blob/main/"
            f"{safe_path}"
        ),
        repository=FLEET_REPOSITORY,
        path=path,
        authority="authoritative",
        freshness=freshness,
        available=available,
    )


def _unavailable_source(path: str, label: str, reason: str) -> estate.SourceReference:
    return _source(
        path,
        estate.Freshness.unavailable(reason=reason),
        label=label,
        available=False,
    )


def _strict_json(text: str, label: str) -> Any:
    if not isinstance(text, str):
        raise OwnerCommentContractError(f"{label} must be UTF-8 JSON text")
    if len(text) > MAX_INDEX_CHARS:
        raise OwnerCommentContractError(f"{label} exceeds the bounded read size")

    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, value in values:
            if key in output:
                raise OwnerCommentContractError(
                    f"{label} contains duplicate key {key!r}"
                )
            output[key] = value
        return output

    try:
        data = json.loads(
            text,
            object_pairs_hook=pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                OwnerCommentContractError(
                    f"{label} contains non-finite number {value}"
                )
            ),
        )
    except OwnerCommentContractError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError, RecursionError) as exc:
        raise OwnerCommentContractError(f"{label} is malformed JSON") from exc
    try:
        canonical = (
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n"
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise OwnerCommentContractError(
            f"{label} cannot be represented as canonical v1 JSON"
        ) from exc
    if text != canonical:
        raise OwnerCommentContractError(
            f"{label} is not canonical v1 JSON"
        )
    return data


def _exact_keys(data: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = sorted(expected - set(data))
    unknown = sorted(set(data) - expected)
    if missing:
        raise OwnerCommentContractError(
            f"{label} is missing field(s): {', '.join(missing)}"
        )
    if unknown:
        raise OwnerCommentContractError(
            f"{label} has unknown field(s): {', '.join(unknown)}"
        )


def parse_root_index(text: str) -> tuple[OwnerCommentIndexRow, ...]:
    """Validate and parse Fleet Manager's exact root index v1 shape."""

    data = _strict_json(text, "owner-comment root index")
    if not isinstance(data, dict):
        raise OwnerCommentContractError("owner-comment root index must be an object")
    _exact_keys(data, _ROOT_KEYS, "owner-comment root index")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise OwnerCommentContractError("owner-comment root index schema_version must be 1")
    if data["derived_from"] != list(DERIVED_FROM):
        raise OwnerCommentContractError("owner-comment root index derived_from is not v1")
    raw_rows = data["repositories"]
    if not isinstance(raw_rows, list):
        raise OwnerCommentContractError(
            "owner-comment root index repositories must be a list"
        )

    rows: list[OwnerCommentIndexRow] = []
    seen: set[str] = set()
    for position, raw in enumerate(raw_rows):
        label = f"owner-comment root index row {position}"
        if not isinstance(raw, dict):
            raise OwnerCommentContractError(f"{label} must be an object")
        _exact_keys(raw, _ROOT_ROW_KEYS, label)
        repository = raw["repository"]
        if not isinstance(repository, str) or not _REPOSITORY_RE.fullmatch(repository):
            raise OwnerCommentContractError(f"{label} has invalid repository")
        folded = repository.casefold()
        if folded in seen:
            raise OwnerCommentContractError(
                f"{label} duplicates repository {repository!r}"
            )
        seen.add(folded)
        expected_path = f"docs/owner-comments/{repository}/README.md"
        if raw["index"] != expected_path:
            raise OwnerCommentContractError(
                f"{label} index must be {expected_path}"
            )
        counts: list[int] = []
        for key in ("unconsumed_count", "consumed_count"):
            value = raw[key]
            if type(value) is not int or value < 0:
                raise OwnerCommentContractError(
                    f"{label} {key} must be a non-negative integer"
                )
            if value > MAX_INDEX_RECORDS:
                raise OwnerCommentContractError(
                    f"{label} {key} exceeds the bounded count"
                )
            counts.append(value)
        latest_values: list[Optional[datetime]] = []
        for count, key in zip(
            counts, ("latest_unconsumed_at", "latest_consumed_at"), strict=True
        ):
            value = raw[key]
            if count == 0:
                if value is not None:
                    raise OwnerCommentContractError(
                        f"{label} {key} must be null when its count is zero"
                    )
                latest_values.append(None)
            else:
                latest_values.append(_timestamp(value, f"{label} {key}"))
        rows.append(
            OwnerCommentIndexRow(
                repository=repository,
                index_path=expected_path,
                unconsumed_count=counts[0],
                consumed_count=counts[1],
                latest_unconsumed_at=latest_values[0],
                latest_consumed_at=latest_values[1],
            )
        )
    return tuple(rows)


async def read_index(refresh: bool = False) -> OwnerCommentIndexRead:
    """Read the one cheap public estate-level owner-comment projection."""

    try:
        result = await github.fetch_public_file(
            FLEET_REPOSITORY, ROOT_INDEX_PATH, refresh=refresh
        )
    except Exception as exc:  # defensive: a comment source must not sink /repos
        reason = f"Owner-comment index fetch failed: {type(exc).__name__}"
        return OwnerCommentIndexRead(
            (),
            _unavailable_source(
                ROOT_INDEX_PATH, "Fleet Manager owner-comment index", reason
            ),
            (reason,),
            False,
        )

    base_freshness = _envelope_freshness(result)
    if not result.get("ok"):
        reason = str(result.get("error") or f"HTTP {result.get('status')}")
        source = _source(
            ROOT_INDEX_PATH,
            base_freshness,
            label="Fleet Manager owner-comment index",
            available=False,
        )
        return OwnerCommentIndexRead(
            (), source, (f"Fleet Manager owner comments unavailable: {reason}",), False
        )
    try:
        rows = parse_root_index(result.get("data"))
    except OwnerCommentContractError as exc:
        reason = str(exc)
        freshness = estate.Freshness.unavailable(
            retrieved_at=base_freshness.retrieved_at,
            reason=reason,
        )
        source = _source(
            ROOT_INDEX_PATH,
            freshness,
            label="Fleet Manager owner-comment index",
            available=False,
        )
        return OwnerCommentIndexRead((), source, (reason,), False)
    source = _source(
        ROOT_INDEX_PATH,
        base_freshness,
        label="Fleet Manager owner-comment index",
        available=True,
    )
    return OwnerCommentIndexRead(rows, source, (), True)


def summary_for(
    index: Optional[OwnerCommentIndexRead], repository: str
) -> estate.OwnerCommentSummary:
    """Return exact-case tri-state counts for one Fleet-indexed repository."""

    if index is None:
        return estate.OwnerCommentSummary(
            freshness=estate.Freshness.unavailable(
                reason="Fleet Manager owner-comment index was not read."
            )
        )
    if not index.valid:
        return estate.OwnerCommentSummary(
            freshness=index.source.freshness,
            source=index.source,
        )
    row = index.row(repository)
    if row is None:
        case_mismatch = next(
            (
                item.repository
                for item in index.rows
                if item.repository.casefold() == repository.casefold()
            ),
            None,
        )
        reason = (
            f"Owner-comment index spells this repository {case_mismatch!r}; "
            f"Fleet Manager estate spells it {repository!r}."
            if case_mismatch
            else f"Owner-comment index has no entry for {repository}."
        )
        return estate.OwnerCommentSummary(
            freshness=estate.Freshness.unknown(
                retrieved_at=index.source.freshness.retrieved_at,
                reason=reason,
            ),
            source=index.source,
        )
    return estate.OwnerCommentSummary(
        unconsumed_count=row.unconsumed_count,
        consumed_count=row.consumed_count,
        freshness=index.source.freshness,
        source=index.source,
    )


def unavailable_summary(reason: str) -> estate.OwnerCommentSummary:
    """Explicit summary for repositories outside Fleet Manager's comment index."""

    return estate.OwnerCommentSummary(
        freshness=estate.Freshness.unavailable(reason=reason)
    )


def _expect(lines: list[str], cursor: int, expected: str, label: str) -> int:
    if cursor >= len(lines) or lines[cursor] != expected:
        raise OwnerCommentContractError(
            f"{label} is not the generated Fleet Manager v1 shape"
        )
    return cursor + 1


def parse_repository_index(text: str, repository: str) -> _RepositoryIndex:
    """Validate the exact generated per-repository README and extract paths."""

    if not _REPOSITORY_RE.fullmatch(repository or ""):
        raise OwnerCommentContractError("invalid owner-comment repository")
    if not isinstance(text, str) or len(text) > MAX_INDEX_CHARS:
        raise OwnerCommentContractError("owner-comment repository index is unavailable")
    if not text.endswith("\n"):
        raise OwnerCommentContractError(
            "owner-comment repository index lacks its generated final newline"
        )
    if "\r" in text:
        raise OwnerCommentContractError(
            "owner-comment repository index is not canonical LF text"
        )
    # The Fleet Manager renderer is canonical LF text. ``splitlines()`` also
    # treats Unicode and C0 separators as line endings, which would silently
    # normalize noncanonical bytes into the accepted generated shape.
    lines = text.split("\n")[:-1]
    label = f"owner-comment repository index for {repository}"
    cursor = 0
    for expected in (
        f"# Owner comments — `{repository}`",
        "",
        "> **Status:** `living-ledger`",
        ">",
        "> **Generated index.** Run `python3 tools/owner_comments.py reindex`;",
        "> do not hand-edit this file. **Every record and all of its metadata",
        "> are public.** Read the [storage and privacy contract](../README.md)",
        "> before adding feedback. JSON preserves the owner's wording verbatim.",
        "",
    ):
        cursor = _expect(lines, cursor, expected, label)

    if cursor >= len(lines):
        raise OwnerCommentContractError(f"{label} is truncated")
    active_heading = re.fullmatch(r"## Unconsumed \((\d+)\)", lines[cursor])
    if not active_heading:
        raise OwnerCommentContractError(f"{label} has invalid Unconsumed heading")
    active_count = _bounded_index_count(
        active_heading.group(1), f"{label} Unconsumed count"
    )
    cursor += 1
    cursor = _expect(lines, cursor, "", label)

    active: list[_RepositoryIndexEntry] = []
    if active_count == 0:
        cursor = _expect(lines, cursor, "No unconsumed owner comments.", label)
    else:
        cursor = _expect(lines, cursor, "| id | created at | source | record |", label)
        cursor = _expect(lines, cursor, "|---|---|---|---|", label)
        active_pattern = re.compile(
            r"\| `([^`]+)` \| `([^`]+)` \| "
            r"([a-z0-9][a-z0-9._-]{0,63}) \| "
            r"\[`([^`]+)\.json`]\(([^)]+)\) \|"
        )
        for _ in range(active_count):
            if cursor >= len(lines):
                raise OwnerCommentContractError(f"{label} active table is truncated")
            match = active_pattern.fullmatch(lines[cursor])
            if not match:
                raise OwnerCommentContractError(f"{label} has invalid active row")
            comment_id, created_text, surface, link_id, target = match.groups()
            if not _ID_RE.fullmatch(comment_id):
                raise OwnerCommentContractError(f"{label} has invalid active id")
            if link_id != comment_id or target != f"{comment_id}.json":
                raise OwnerCommentContractError(f"{label} has noncanonical active path")
            active.append(
                _RepositoryIndexEntry(
                    comment_id,
                    created_text,
                    _timestamp(created_text, f"{label} active created_at"),
                    "unconsumed",
                    source_surface=surface,
                )
            )
            cursor += 1

    cursor = _expect(lines, cursor, "", label)
    if cursor >= len(lines):
        raise OwnerCommentContractError(f"{label} is truncated")
    consumed_heading = re.fullmatch(r"## Consumed history \((\d+)\)", lines[cursor])
    if not consumed_heading:
        raise OwnerCommentContractError(f"{label} has invalid consumed heading")
    consumed_count = _bounded_index_count(
        consumed_heading.group(1), f"{label} consumed count"
    )
    cursor += 1
    cursor = _expect(lines, cursor, "", label)

    consumed: list[_RepositoryIndexEntry] = []
    if consumed_count == 0:
        cursor = _expect(lines, cursor, "No consumed owner comments.", label)
    else:
        cursor = _expect(
            lines,
            cursor,
            "| id | created at | consumed at | preserved record |",
            label,
        )
        cursor = _expect(lines, cursor, "|---|---|---|---|", label)
        consumed_pattern = re.compile(
            r"\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| "
            r"\[`([^`]+)\.json`]\(consumed/([^)]+)\) \|"
        )
        for _ in range(consumed_count):
            if cursor >= len(lines):
                raise OwnerCommentContractError(
                    f"{label} consumed table is truncated"
                )
            match = consumed_pattern.fullmatch(lines[cursor])
            if not match:
                raise OwnerCommentContractError(f"{label} has invalid consumed row")
            comment_id, created_text, consumed_text, link_id, target = match.groups()
            if not _ID_RE.fullmatch(comment_id):
                raise OwnerCommentContractError(f"{label} has invalid consumed id")
            if link_id != comment_id or target != f"{comment_id}.json":
                raise OwnerCommentContractError(
                    f"{label} has noncanonical consumed path"
                )
            created = _timestamp(created_text, f"{label} consumed created_at")
            consumed_at = _timestamp(consumed_text, f"{label} consumption.at")
            if consumed_at < created:
                raise OwnerCommentContractError(
                    f"{label} consumption.at precedes created_at"
                )
            consumed.append(
                _RepositoryIndexEntry(
                    comment_id,
                    created_text,
                    created,
                    "consumed",
                    consumed_at_text=consumed_text,
                    consumed_at=consumed_at,
                )
            )
            cursor += 1

    for expected in (
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
    ):
        cursor = _expect(lines, cursor, expected, label)
    if cursor != len(lines):
        raise OwnerCommentContractError(f"{label} has unexpected trailing content")

    all_ids = [item.id for item in (*active, *consumed)]
    if len(set(all_ids)) != len(all_ids):
        raise OwnerCommentContractError(f"{label} contains duplicate comment ids")
    active_order = [(item.created_at, item.id) for item in active]
    if active_order != sorted(active_order):
        raise OwnerCommentContractError(f"{label} active rows are not canonical order")
    consumed_order = [(item.consumed_at, item.id) for item in consumed]
    if consumed_order != sorted(consumed_order):
        raise OwnerCommentContractError(f"{label} consumed rows are not canonical order")
    return _RepositoryIndex(repository, tuple(active), tuple(consumed))


def _record_path(repository: str, entry: _RepositoryIndexEntry) -> str:
    middle = "consumed/" if entry.state == "consumed" else ""
    return f"docs/owner-comments/{repository}/{middle}{entry.id}.json"


def _validate_text(
    value: Any,
    label: str,
    *,
    limit: int,
    require_non_whitespace: bool,
) -> str:
    if not isinstance(value, str):
        raise OwnerCommentContractError(f"{label} must be a string")
    if require_non_whitespace and not value.strip():
        raise OwnerCommentContractError(f"{label} must contain non-whitespace text")
    if len(value) > limit:
        raise OwnerCommentContractError(f"{label} exceeds {limit} characters")
    if _has_forbidden_codepoint(value):
        raise OwnerCommentContractError(f"{label} contains a forbidden codepoint")
    return value


def parse_record(
    text: str,
    repository: str,
    entry: _RepositoryIndexEntry,
    result: Mapping[str, Any],
) -> estate.OwnerCommentRecord:
    """Validate one v1 record against its routed index row and path."""

    data = _strict_json(text, f"owner-comment record {entry.id}")
    if not isinstance(data, dict):
        raise OwnerCommentContractError(f"owner-comment record {entry.id} must be an object")
    expected_keys = set(_RECORD_REQUIRED_KEYS)
    if entry.state == "consumed":
        expected_keys.add("consumption")
    _exact_keys(data, expected_keys, f"owner-comment record {entry.id}")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise OwnerCommentContractError(f"owner-comment record {entry.id} schema mismatch")
    if data["id"] != entry.id:
        raise OwnerCommentContractError(f"owner-comment record {entry.id} id/path mismatch")
    if data["repository"] != repository:
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} repository/path mismatch"
        )
    if data["state"] != entry.state:
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} state/path mismatch"
        )
    created_at = _timestamp(data["created_at"], f"record {entry.id} created_at")
    if data["created_at"] != entry.created_at_text:
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} created_at/index mismatch"
        )
    comment = _validate_text(
        data["comment"],
        f"record {entry.id} comment",
        limit=MAX_COMMENT_CHARS,
        require_non_whitespace=True,
    )
    raw_source = data["source"]
    if not isinstance(raw_source, dict):
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} source must be an object"
        )
    if set(raw_source) not in ({"surface"}, {"surface", "context"}):
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} source fields are invalid"
        )
    surface = raw_source.get("surface")
    if not isinstance(surface, str) or not _SURFACE_RE.fullmatch(surface):
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} source.surface is invalid"
        )
    if entry.source_surface is not None and surface != entry.source_surface:
        raise OwnerCommentContractError(
            f"owner-comment record {entry.id} source/index mismatch"
        )
    context = raw_source.get("context")
    if context is not None:
        context = _validate_text(
            context,
            f"record {entry.id} source.context",
            limit=MAX_CONTEXT_CHARS,
            require_non_whitespace=False,
        )

    consumed_at: Optional[datetime] = None
    actor: Optional[str] = None
    evidence: Optional[str] = None
    if entry.state == "consumed":
        consumption = data["consumption"]
        if not isinstance(consumption, dict):
            raise OwnerCommentContractError(
                f"owner-comment record {entry.id} consumption must be an object"
            )
        _exact_keys(
            consumption,
            {"at", "actor", "evidence"},
            f"owner-comment record {entry.id} consumption",
        )
        consumed_at = _timestamp(consumption["at"], f"record {entry.id} consumption.at")
        if consumption["at"] != entry.consumed_at_text:
            raise OwnerCommentContractError(
                f"owner-comment record {entry.id} consumption/index mismatch"
            )
        if consumed_at < created_at:
            raise OwnerCommentContractError(
                f"owner-comment record {entry.id} consumption precedes creation"
            )
        actor = _validate_text(
            consumption["actor"],
            f"record {entry.id} consumption.actor",
            limit=MAX_CONTEXT_CHARS,
            require_non_whitespace=True,
        )
        evidence = _validate_text(
            consumption["evidence"],
            f"record {entry.id} consumption.evidence",
            limit=MAX_CONTEXT_CHARS,
            require_non_whitespace=True,
        )

    path = _record_path(repository, entry)
    record_source = _source(
        path,
        _envelope_freshness(result),
        label=f"Fleet Manager owner comment {entry.id}",
        available=True,
    )
    return estate.OwnerCommentRecord(
        id=entry.id,
        repository=repository,
        comment=comment,
        created_at=created_at,
        state=entry.state,
        source_surface=surface,
        source_context=context,
        consumed_at=consumed_at,
        consumption_actor=actor,
        consumption_evidence=evidence,
        source=record_source,
    )


async def read_repository_comments(
    repository: str,
    *,
    expected_summary: Optional[estate.OwnerCommentSummary] = None,
    refresh: bool = False,
) -> estate.OwnerCommentCollection:
    """Read one repository's bounded active and recent consumed records."""

    if not _REPOSITORY_RE.fullmatch(repository or ""):
        return estate.OwnerCommentCollection(
            warnings=("Invalid Fleet Manager owner-comment repository.",),
            freshness=estate.Freshness.unavailable(
                reason="Invalid owner-comment repository identifier."
            ),
        )
    index_path = f"docs/owner-comments/{repository}/README.md"
    try:
        index_result = await github.fetch_public_file(
            FLEET_REPOSITORY, index_path, refresh=refresh
        )
    except Exception as exc:  # defensive isolation from the selected page
        reason = f"Owner-comment repository index fetch failed: {type(exc).__name__}"
        return estate.OwnerCommentCollection(
            warnings=(reason,),
            freshness=estate.Freshness.unavailable(reason=reason),
            source=_unavailable_source(
                index_path, f"Owner comments for {repository}", reason
            ),
        )

    index_freshness = _envelope_freshness(index_result)
    if not index_result.get("ok"):
        reason = str(index_result.get("error") or f"HTTP {index_result.get('status')}")
        source = _source(
            index_path,
            index_freshness,
            label=f"Owner comments for {repository}",
            available=False,
        )
        return estate.OwnerCommentCollection(
            warnings=(f"Owner comments unavailable: {reason}",),
            freshness=index_freshness,
            source=source,
        )
    try:
        parsed = parse_repository_index(index_result.get("data"), repository)
    except OwnerCommentContractError as exc:
        reason = str(exc)
        freshness = estate.Freshness.unavailable(
            retrieved_at=index_freshness.retrieved_at,
            reason=reason,
        )
        source = _source(
            index_path,
            freshness,
            label=f"Owner comments for {repository}",
            available=False,
        )
        return estate.OwnerCommentCollection(
            warnings=(reason,), freshness=freshness, source=source
        )

    source = _source(
        index_path,
        index_freshness,
        label=f"Owner comments for {repository}",
        available=True,
    )
    warnings: list[str] = []
    if expected_summary is not None and expected_summary.is_known:
        if (
            expected_summary.unconsumed_count != len(parsed.active)
            or expected_summary.consumed_count != len(parsed.consumed)
        ):
            warnings.append(
                "Fleet Manager root and repository owner-comment indexes disagree."
            )

    active_entries = parsed.active[-MAX_ACTIVE_RECORDS:]
    consumed_entries = parsed.consumed[-MAX_CONSUMED_RECORDS:]
    truncated = (
        len(active_entries) < len(parsed.active)
        or len(consumed_entries) < len(parsed.consumed)
    )
    semaphore = asyncio.Semaphore(DETAIL_CONCURRENCY)

    async def fetch_entry(
        entry: _RepositoryIndexEntry,
    ) -> tuple[Optional[estate.OwnerCommentRecord], Optional[str]]:
        path = _record_path(repository, entry)
        try:
            async with semaphore:
                result = await github.fetch_public_file(
                    FLEET_REPOSITORY, path, refresh=refresh
                )
        except Exception as exc:
            return None, f"{entry.id}: fetch failed ({type(exc).__name__})."
        if not result.get("ok"):
            reason = str(result.get("error") or f"HTTP {result.get('status')}")
            return None, f"{entry.id}: record unavailable ({reason})."
        try:
            return parse_record(result.get("data"), repository, entry, result), None
        except OwnerCommentContractError as exc:
            return None, f"{entry.id}: {exc}"

    entries = (*active_entries, *consumed_entries)
    tasks = [asyncio.create_task(fetch_entry(entry)) for entry in entries]
    done: set[asyncio.Task] = set()
    pending: set[asyncio.Task] = set()
    if tasks:
        done, pending = await asyncio.wait(
            tasks, timeout=DETAIL_TIMEOUT_SECONDS
        )
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
        warnings.append(
            f"{len(pending)} owner-comment record read(s) exceeded the "
            f"{DETAIL_TIMEOUT_SECONDS:g}s detail budget."
        )
    fetched = [task.result() for task in tasks if task in done]
    records: dict[str, estate.OwnerCommentRecord] = {}
    for record, warning in fetched:
        if record is not None:
            records[record.id] = record
        if warning:
            warnings.append(warning)

    active_records = tuple(
        records[entry.id] for entry in active_entries if entry.id in records
    )
    consumed_records = tuple(
        records[entry.id] for entry in consumed_entries if entry.id in records
    )
    collection_freshness = index_freshness
    if warnings:
        collection_freshness = estate.Freshness.unknown(
            retrieved_at=index_freshness.retrieved_at,
            reason="Owner-comment detail is incomplete or contradictory.",
        )
    return estate.OwnerCommentCollection(
        unconsumed=active_records,
        consumed=consumed_records,
        warnings=tuple(warnings),
        freshness=collection_freshness,
        source=source,
        truncated=truncated,
    )
