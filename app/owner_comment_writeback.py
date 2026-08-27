"""Ruleset-safe Fleet Manager owner-comment writeback.

The website owns the authenticated form, but Fleet Manager owns the durable
record.  This module is the narrow bridge between them: it reads the current
Fleet Manager comment indexes at one pinned ``main`` commit, builds the record
and both derived indexes, writes those three files in one Git Data commit on a
fresh ``claude/*`` branch, and opens a ready pull request.

An open pull request is deliberately reported as ``pending_pr``.  It is not a
durable comment until Fleet Manager's protected ``main`` contains the record.
There is no local queue and no direct/forced update of ``main`` here.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.parse import quote

from . import clock, github


ENV_TOKEN = "FLEET_MANAGER_WRITEBACK_TOKEN"
TARGET_REPOSITORY = "menno420/fleet-manager"
BASE_BRANCH = "main"
BRANCH_PREFIX = "claude/owner-comments-"
COMMENTS_ROOT = "docs/owner-comments"
ROOT_INDEX_PATH = f"{COMMENTS_ROOT}/index.json"

SCHEMA_VERSION = 1
MAX_COMMENT_CHARS = 20_000
MAX_CONTEXT_CHARS = 1_000
MAX_INDEX_RECORDS = 10_000
SOURCE_SURFACE = "control-plane"
DERIVED_FROM = [
    "docs/ESTATE.md",
    "docs/owner-comments/<repo>/*.json",
    "docs/owner-comments/<repo>/consumed/*.json",
]

WritebackState = Literal[
    "unavailable", "pending_pr", "failed_retryable", "failed"
]

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
_REPOSITORY_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9_-])?$"
)
_SURFACE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_SUBMISSION_KEY_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_TOKEN_RE = re.compile(r"^[\x21-\x7e]{1,512}$")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
_ROOT_RESERVED = {"readme.md", "index.json", "record.schema.json"}


@dataclass(frozen=True)
class OwnerCommentWritebackResult:
    """One submission attempt, without any false durability claim."""

    state: WritebackState
    repository: str
    comment_id: str = ""
    created_at: str = ""
    branch: str = ""
    base_sha: str = ""
    commit_sha: str = ""
    pr_number: int = 0
    pr_url: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        """True only when a ready PR is open; this still is not durable."""

        return self.state == "pending_pr"

    @property
    def record_id(self) -> str:
        """UI-facing name for the Fleet Manager durable record identifier."""

        return self.comment_id

    @property
    def message(self) -> str:
        """Owner-facing outcome copy without inventing a durable state."""

        if self.error:
            return self.error
        if self.state == "pending_pr":
            return (
                f"Owner comment {self.comment_id} is pending in Fleet Manager "
                f"PR #{self.pr_number}; it is not durable until that PR merges."
            )
        return self.state.replace("_", " ")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class _ActiveIndexEntry:
    comment_id: str
    created_at: str
    surface: str


@dataclass(frozen=True)
class _ConsumedIndexEntry:
    comment_id: str
    created_at: str
    consumed_at: str


class _ContractError(ValueError):
    """The pinned Fleet Manager v1 contract cannot be changed safely."""


@dataclass(frozen=True)
class OwnerCommentWritebackCapability:
    available: bool
    label: str
    reason: str
    token_env: str = ENV_TOKEN
    setup_required: bool = False


def runtime_token() -> str:
    """Read the dedicated Fleet Manager write token for this attempt.

    Never consult ``GITHUB_TOKEN``: that token also backs public/read paths
    and may have broader repository visibility than this mutation needs.
    """

    return os.environ.get(ENV_TOKEN, "").strip()


def _redact_runtime_token(text: Any) -> str:
    """Remove literal and serialized forms of the dedicated credential."""

    rendered = str(text)
    token = runtime_token()
    if not token:
        return rendered
    variants = {
        token,
        repr(token)[1:-1],
        json.dumps(token, ensure_ascii=True)[1:-1],
    }
    for variant in sorted(variants, key=len, reverse=True):
        if variant:
            rendered = rendered.replace(variant, "[credential redacted]")
    return rendered


def _token_problem(token: str) -> str:
    if not token:
        return f"{ENV_TOKEN} is not set on this service."
    if not _TOKEN_RE.fullmatch(token):
        return (
            f"{ENV_TOKEN} contains invalid header characters or has an "
            "unsupported length."
        )
    return ""


def capability() -> OwnerCommentWritebackCapability:
    """Small owner-UI capability summary; token values are never returned."""

    token = runtime_token()
    problem = _token_problem(token)
    available = not problem
    return OwnerCommentWritebackCapability(
        available=available,
        label=(
            "Fleet Manager credential configured"
            if available
            else "Fleet Manager writeback unavailable"
        ),
        reason=(
            "The credential will be verified against Fleet Manager when the "
            "comment is submitted; a ready PR is still not durable until merge."
            if available
            else problem
        ),
        setup_required=not available,
    )


def _contains_surrogate(value: str) -> bool:
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def validate_comment(comment: Any) -> str:
    """Return an owner-readable problem, or ``""`` for valid verbatim text."""

    if not isinstance(comment, str):
        return "comment must be text"
    if not comment.strip():
        return "comment must contain non-whitespace text"
    if len(comment) > MAX_COMMENT_CHARS:
        return f"comment exceeds {MAX_COMMENT_CHARS} characters"
    if "\x00" in comment:
        return "comment must not contain a NUL byte"
    if _contains_surrogate(comment):
        return "comment must not contain an invalid Unicode surrogate"
    return ""


def _valid_repository(repository: Any) -> bool:
    if not isinstance(repository, str) or not _REPOSITORY_RE.fullmatch(repository):
        return False
    folded = repository.casefold()
    first = repository.split(".", 1)[0].casefold()
    return (
        folded not in _ROOT_RESERVED
        and first not in _WINDOWS_RESERVED
        and not repository.endswith((".", " "))
    )


def _validate_context(context: Any) -> str:
    if not isinstance(context, str):
        return "source context must be text"
    if len(context) > MAX_CONTEXT_CHARS:
        return f"source context exceeds {MAX_CONTEXT_CHARS} characters"
    if "\x00" in context or _contains_surrogate(context):
        return "source context contains an invalid character"
    return ""


def _timestamp(value: datetime | None = None) -> str:
    instant = value or clock.now()
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    return instant.astimezone(timezone.utc).replace(microsecond=0).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def new_submission_key(value: datetime | None = None) -> str:
    """Mint a time-free form-scoped nonce without retaining server state."""

    # ``value`` stays accepted for compatibility with deterministic tests, but
    # creation time belongs to the first POST, never to the earlier form GET.
    del value
    return secrets.token_hex(16)


def validate_submission_key(value: Any) -> str:
    """Return an owner-readable problem, or ``""`` for a real form key."""

    if not isinstance(value, str) or not _SUBMISSION_KEY_RE.fullmatch(value):
        return "submission key is missing or malformed; reload the form"
    return ""


def _parse_timestamp(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise _ContractError(f"{field} is not an RFC3339 UTC timestamp")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise _ContractError(f"{field} is not a real timestamp") from exc


def _comment_id(
    repository: str,
    comment: str,
    context: str,
    submission_key: str,
) -> str:
    digest_input = _canonical_json_bytes(
        {
            "comment": comment,
            "repository": repository,
            "source": {"context": context, "surface": SOURCE_SURFACE},
            "submission_key": submission_key,
        }
    )
    return f"oc-{hashlib.sha256(digest_input).hexdigest()[:32]}"


def _canonical_json_bytes(data: Any) -> bytes:
    return (
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _ContractError("duplicate JSON key")
        result[key] = value
    return result


def _decode_canonical_json(raw: bytes, *, label: str) -> dict[str, Any]:
    try:
        data = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except _ContractError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise _ContractError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict):
        raise _ContractError(f"{label} must be a JSON object")
    try:
        canonical = _canonical_json_bytes(data)
    except (UnicodeEncodeError, ValueError, RecursionError) as exc:
        raise _ContractError(f"{label} contains an invalid Unicode surrogate") from exc
    if raw != canonical:
        raise _ContractError(f"{label} is not canonical v1 JSON")
    return data


def _result_error(result: dict[str, Any]) -> str:
    message = _redact_runtime_token(
        result.get("error") or f"HTTP {result.get('status', 0)}"
    )
    return github.short_reason(message, status=result.get("status"))


def _failure_state(result: dict[str, Any]) -> WritebackState:
    status = result.get("status")
    if status in (401, 403, 404):
        return "unavailable"
    if status == 0 or status == 409 or status == 429:
        return "failed_retryable"
    if isinstance(status, int) and status >= 500:
        return "failed_retryable"
    return "failed"


def _failure(
    repository: str,
    state: WritebackState,
    error: str,
    *,
    comment_id: str = "",
    created_at: str = "",
    branch: str = "",
    base_sha: str = "",
    commit_sha: str = "",
) -> OwnerCommentWritebackResult:
    # Contract validation may quote a value read from GitHub. A hostile or
    # malformed 200 response can therefore echo the mutation credential just
    # as an error envelope can. Redact at the final result boundary too, before
    # anything is stored on the result or rendered by Jinja.
    error = _redact_runtime_token(error)
    if state == "unavailable" and ENV_TOKEN not in error:
        error = (
            f"{error}. Verify Fleet Manager's v1 comment contract is present "
            f"and {ENV_TOKEN} has Contents read/write plus Pull requests "
            "read/write access."
        )
    return OwnerCommentWritebackResult(
        state=state,
        repository=repository,
        comment_id=comment_id,
        created_at=created_at,
        branch=branch,
        base_sha=base_sha,
        commit_sha=commit_sha,
        error=error,
    )


def _api_path(suffix: str) -> str:
    return f"/repos/{TARGET_REPOSITORY}{suffix}"


def _nested_sha(result: dict[str, Any], field: str) -> str:
    data = result.get("data")
    if not result.get("ok") or not isinstance(data, dict):
        return ""
    nested = data.get(field)
    if not isinstance(nested, dict):
        return ""
    sha = nested.get("sha")
    return sha if isinstance(sha, str) else ""


def _verified_ref_sha(result: dict[str, Any], branch: str) -> str:
    data = result.get("data")
    object_data = data.get("object") if isinstance(data, dict) else None
    if (
        not result.get("ok")
        or not isinstance(data, dict)
        or data.get("ref") != f"refs/heads/{branch}"
        or not isinstance(object_data, dict)
        or object_data.get("type") != "commit"
    ):
        return ""
    return _nested_sha(result, "object")


def _verified_commit_tree_sha(result: dict[str, Any], commit_sha: str) -> str:
    data = result.get("data")
    if (
        not result.get("ok")
        or not isinstance(data, dict)
        or data.get("sha") != commit_sha
    ):
        return ""
    return _nested_sha(result, "tree")


def _response_sha(result: dict[str, Any]) -> str:
    data = result.get("data")
    if not result.get("ok") or not isinstance(data, dict):
        return ""
    sha = data.get("sha")
    return sha if isinstance(sha, str) else ""


def _contents_path(path: str, ref: str) -> str:
    return _api_path(f"/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}")


def _decode_contents_result(result: dict[str, Any], *, path: str) -> bytes:
    if not result.get("ok") or not isinstance(result.get("data"), dict):
        raise _ContractError(f"could not read {path}: {_result_error(result)}")
    content = result["data"].get("content")
    encoding = result["data"].get("encoding", "base64")
    if not isinstance(content, str) or encoding != "base64":
        raise _ContractError(f"{path} has an unexpected contents payload")
    try:
        compact = "".join(content.split())
        return base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _ContractError(f"{path} has invalid base64 content") from exc


def _validate_root_index(data: dict[str, Any]) -> list[dict[str, Any]]:
    if set(data) != {"schema_version", "derived_from", "repositories"}:
        raise _ContractError("root owner-comment index has unknown or missing fields")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise _ContractError("root owner-comment index schema_version is not v1")
    if data.get("derived_from") != DERIVED_FROM:
        raise _ContractError("root owner-comment index derived_from contract changed")
    rows = data.get("repositories")
    if not isinstance(rows, list) or not rows:
        raise _ContractError("root owner-comment index repositories must be a list")

    expected_keys = {
        "repository",
        "index",
        "unconsumed_count",
        "consumed_count",
        "latest_unconsumed_at",
        "latest_consumed_at",
    }
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise _ContractError("root owner-comment index has a malformed row")
        repository = row.get("repository")
        folded_repository = repository.casefold() if isinstance(repository, str) else ""
        if not _valid_repository(repository) or folded_repository in seen:
            raise _ContractError("root owner-comment index has an unsafe/duplicate repo")
        seen.add(folded_repository)
        if row.get("index") != f"{COMMENTS_ROOT}/{repository}/README.md":
            raise _ContractError(f"root index path is wrong for {repository}")
        for count_field, latest_field in (
            ("unconsumed_count", "latest_unconsumed_at"),
            ("consumed_count", "latest_consumed_at"),
        ):
            count = row.get(count_field)
            latest = row.get(latest_field)
            if type(count) is not int or count < 0:
                raise _ContractError(f"{repository} has an invalid {count_field}")
            if count > MAX_INDEX_RECORDS:
                raise _ContractError(
                    f"{repository} {count_field} exceeds the bounded count"
                )
            if (count == 0) != (latest is None):
                raise _ContractError(
                    f"{repository} has contradictory {count_field}/{latest_field}"
                )
            if latest is not None:
                _parse_timestamp(latest, field=f"{repository}.{latest_field}")
    return rows


def _valid_id(value: str) -> bool:
    return (
        bool(_ID_RE.fullmatch(value))
        and ".." not in value
        and not value.endswith((".", ".lock"))
        and value.split(".", 1)[0].casefold() not in _WINDOWS_RESERVED
    )


def _bounded_index_count(value: str, *, field: str) -> int:
    if len(value) > len(str(MAX_INDEX_RECORDS)):
        raise _ContractError(f"{field} exceeds the bounded count")
    try:
        count = int(value)
    except ValueError as exc:
        raise _ContractError(f"{field} is not an integer") from exc
    if count > MAX_INDEX_RECORDS:
        raise _ContractError(f"{field} exceeds the bounded count")
    if value != str(count):
        raise _ContractError(f"{field} is not canonical")
    return count


def _repository_readme_pattern(repository: str) -> re.Pattern[str]:
    prefix = (
        f"# Owner comments — `{repository}`\n\n"
        "> **Status:** `living-ledger`\n"
        ">\n"
        "> **Generated index.** Run `python3 tools/owner_comments.py reindex`;\n"
        "> do not hand-edit this file. **Every record and all of its metadata\n"
        "> are public.** Read the [storage and privacy contract](../README.md)\n"
        "> before adding feedback. JSON preserves the owner's wording verbatim.\n\n"
        "## Unconsumed ("
    )
    suffix = (
        "\n\n## Consume mechanically\n\n"
        "After acting or explicitly reconciling a comment, run:\n\n"
        "```text\n"
        f"python3 tools/owner_comments.py consume {repository} <comment-id> \\\n"
        "  --actor <session-card-or-actor> --evidence <record-or-PR-link>\n"
        "```\n\n"
        "Commit the moved record and both changed indexes together. Never delete it.\n"
    )
    return re.compile(
        r"\A"
        + re.escape(prefix)
        + r"(?P<active_count>\d+)\)\n\n(?P<active>.*?)"
        + r"\n\n## Consumed history \((?P<consumed_count>\d+)\)\n\n"
        + r"(?P<consumed>.*?)"
        + re.escape(suffix)
        + r"\Z",
        re.DOTALL,
    )


_ACTIVE_ROW_RE = re.compile(
    r"^\| `(?P<id>[a-z0-9._-]+)` \| `(?P<created>[^`]+)` \| "
    r"(?P<surface>[a-z0-9._-]+) \| \[`(?P=id)\.json`\]\((?P=id)\.json\) \|$"
)
_CONSUMED_ROW_RE = re.compile(
    r"^\| `(?P<id>[a-z0-9._-]+)` \| `(?P<created>[^`]+)` \| "
    r"`(?P<consumed>[^`]+)` \| "
    r"\[`(?P=id)\.json`\]\(consumed/(?P=id)\.json\) \|$"
)


def _parse_repository_readme(
    raw: bytes, repository: str
) -> tuple[list[_ActiveIndexEntry], list[_ConsumedIndexEntry]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _ContractError("repository owner-comment index is not UTF-8") from exc
    match = _repository_readme_pattern(repository).fullmatch(text)
    if not match:
        raise _ContractError("repository owner-comment README is not exact v1 output")

    active_count = _bounded_index_count(
        match.group("active_count"), field="repository README active count"
    )
    consumed_count = _bounded_index_count(
        match.group("consumed_count"),
        field="repository README consumed count",
    )
    active_lines = match.group("active").splitlines()
    consumed_lines = match.group("consumed").splitlines()
    active: list[_ActiveIndexEntry] = []
    consumed: list[_ConsumedIndexEntry] = []

    if active_count == 0:
        if active_lines != ["No unconsumed owner comments."]:
            raise _ContractError("repository README has a malformed empty active list")
    else:
        if active_lines[:2] != [
            "| id | created at | source | record |",
            "|---|---|---|---|",
        ]:
            raise _ContractError("repository README has a malformed active table")
        for line in active_lines[2:]:
            row = _ACTIVE_ROW_RE.fullmatch(line)
            if not row:
                raise _ContractError("repository README has a malformed active row")
            comment_id = row.group("id")
            created_at = row.group("created")
            surface = row.group("surface")
            if not _valid_id(comment_id) or not _SURFACE_RE.fullmatch(surface):
                raise _ContractError("repository README active row is unsafe")
            _parse_timestamp(created_at, field=f"{comment_id}.created_at")
            active.append(_ActiveIndexEntry(comment_id, created_at, surface))
        if len(active) != active_count:
            raise _ContractError("repository README active count does not match")

    if consumed_count == 0:
        if consumed_lines != ["No consumed owner comments."]:
            raise _ContractError("repository README has a malformed empty history")
    else:
        if consumed_lines[:2] != [
            "| id | created at | consumed at | preserved record |",
            "|---|---|---|---|",
        ]:
            raise _ContractError("repository README has a malformed history table")
        for line in consumed_lines[2:]:
            row = _CONSUMED_ROW_RE.fullmatch(line)
            if not row:
                raise _ContractError("repository README has a malformed history row")
            comment_id = row.group("id")
            created_at = row.group("created")
            consumed_at = row.group("consumed")
            if not _valid_id(comment_id):
                raise _ContractError("repository README history row id is unsafe")
            created = _parse_timestamp(
                created_at, field=f"{comment_id}.created_at"
            )
            consumed_on = _parse_timestamp(
                consumed_at, field=f"{comment_id}.consumed_at"
            )
            if consumed_on < created:
                raise _ContractError(
                    "repository README consumption predates comment creation"
                )
            consumed.append(
                _ConsumedIndexEntry(comment_id, created_at, consumed_at)
            )
        if len(consumed) != consumed_count:
            raise _ContractError("repository README consumed count does not match")

    ids = [entry.comment_id for entry in active] + [
        entry.comment_id for entry in consumed
    ]
    if len(ids) != len(set(ids)):
        raise _ContractError("repository README contains a duplicate comment id")

    # This is the compatibility pin: accepting a shape that merely happens to
    # parse would let a website renderer silently diverge from Fleet Manager.
    if raw != render_repository_readme(repository, active, consumed):
        raise _ContractError("repository owner-comment README is not canonical v1")
    return active, consumed


def render_repository_readme(
    repository: str,
    active: list[_ActiveIndexEntry],
    consumed: list[_ConsumedIndexEntry],
) -> bytes:
    """Render byte-for-byte Fleet Manager v1 repository index output."""

    active = sorted(
        active,
        key=lambda entry: (
            _parse_timestamp(entry.created_at, field="created_at"),
            entry.comment_id,
        ),
    )
    consumed = sorted(
        consumed,
        key=lambda entry: (
            _parse_timestamp(entry.consumed_at, field="consumed_at"),
            entry.comment_id,
        ),
    )
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
            ["| id | created at | source | record |", "|---|---|---|---|"]
        )
        for entry in active:
            lines.append(
                f"| `{entry.comment_id}` | `{entry.created_at}` | "
                f"{entry.surface} | [`{entry.comment_id}.json`]"
                f"({entry.comment_id}.json) |"
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
        for entry in consumed:
            lines.append(
                f"| `{entry.comment_id}` | `{entry.created_at}` | "
                f"`{entry.consumed_at}` | [`{entry.comment_id}.json`]"
                f"(consumed/{entry.comment_id}.json) |"
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
    return "\n".join(lines).encode("utf-8")


def _updated_contract_files(
    *,
    root_data: dict[str, Any],
    repository: str,
    comment: str,
    comment_id: str,
    created_at: str,
    context: str,
    repository_readme: bytes,
) -> dict[str, bytes]:
    rows = _validate_root_index(root_data)
    target = next((row for row in rows if row["repository"] == repository), None)
    if target is None:
        raise _ContractError(
            f"{repository} is not indexed by Fleet Manager owner comments"
        )
    active, consumed = _parse_repository_readme(repository_readme, repository)
    if target["unconsumed_count"] != len(active):
        raise _ContractError("root and repository unconsumed counts disagree")
    if target["consumed_count"] != len(consumed):
        raise _ContractError("root and repository consumed counts disagree")
    latest_active = (
        max(active, key=lambda entry: _parse_timestamp(entry.created_at, field="x"))
        if active
        else None
    )
    latest_consumed = (
        max(
            consumed,
            key=lambda entry: _parse_timestamp(entry.consumed_at, field="x"),
        )
        if consumed
        else None
    )
    if target["latest_unconsumed_at"] != (
        latest_active.created_at if latest_active else None
    ):
        raise _ContractError("root and repository latest unconsumed timestamps disagree")
    if target["latest_consumed_at"] != (
        latest_consumed.consumed_at if latest_consumed else None
    ):
        raise _ContractError("root and repository latest consumed timestamps disagree")
    if comment_id in {entry.comment_id for entry in active + consumed}:
        raise _ContractError(f"owner-comment id {comment_id} already exists on main")

    record = {
        "schema_version": SCHEMA_VERSION,
        "id": comment_id,
        "repository": repository,
        "created_at": created_at,
        "state": "unconsumed",
        "source": {"surface": SOURCE_SURFACE, "context": context},
        "comment": comment,
    }
    active.append(_ActiveIndexEntry(comment_id, created_at, SOURCE_SURFACE))
    target["unconsumed_count"] += 1
    target["latest_unconsumed_at"] = max(
        (entry.created_at for entry in active),
        key=lambda value: _parse_timestamp(value, field="created_at"),
    )
    record_path = f"{COMMENTS_ROOT}/{repository}/{comment_id}.json"
    readme_path = f"{COMMENTS_ROOT}/{repository}/README.md"
    return {
        record_path: _canonical_json_bytes(record),
        readme_path: render_repository_readme(repository, active, consumed),
        ROOT_INDEX_PATH: _canonical_json_bytes(root_data),
    }


async def _create_blob(
    path: str, content: bytes, token: str
) -> tuple[str, dict[str, Any], str]:
    result = await github.api_request(
        "POST",
        _api_path("/git/blobs"),
        json_body={
            "content": base64.b64encode(content).decode("ascii"),
            "encoding": "base64",
        },
        token=token,
    )
    sha = result.get("data", {}).get("sha") if isinstance(result.get("data"), dict) else ""
    if result.get("ok") and isinstance(sha, str) and _SHA_RE.fullmatch(sha):
        return sha, result, ""
    return "", result, f"could not create blob for {path}: {_result_error(result)}"


def _verified_pr(
    data: Any, *, branch: str, commit_sha: str
) -> tuple[int, str] | None:
    if not isinstance(data, dict):
        return None
    number = data.get("number")
    url = data.get("html_url")
    head = data.get("head")
    base = data.get("base")
    if (
        type(number) is not int
        or number <= 0
        or not isinstance(url, str)
        or url != f"https://github.com/{TARGET_REPOSITORY}/pull/{number}"
        or data.get("state") != "open"
        or data.get("draft") is not False
        or not isinstance(head, dict)
        or head.get("ref") != branch
        or head.get("sha") != commit_sha
        or not isinstance(base, dict)
        or base.get("ref") != BASE_BRANCH
    ):
        return None
    return number, url


async def _verify_existing_branch(
    *,
    branch: str,
    repository: str,
    comment: str,
    comment_id: str,
    context: str,
    token: str,
) -> tuple[str, str, str, dict[str, Any] | None, str]:
    """Return replay identity, failed envelope, and error for an exact retry.

    The branch is deterministic from the form nonce, so it is the durable
    replay receipt after a lost response or process restart. Its parent may be
    an older ancestor of ``main``; validation therefore rebuilds the exact
    three-file tree over that original parent instead of comparing it with a
    tree based on today's moving ``main``.
    """

    ref = await github.api_request(
        "GET", _api_path(f"/git/ref/heads/{quote(branch, safe='/')}"), token=token
    )
    head_sha = _verified_ref_sha(ref, branch)
    if not isinstance(head_sha, str) or not _SHA_RE.fullmatch(head_sha):
        return "", "", "", ref, "existing writeback branch head could not be verified"
    commit = await github.api_request(
        "GET", _api_path(f"/git/commits/{head_sha}"), token=token
    )
    data = commit.get("data") if isinstance(commit.get("data"), dict) else {}
    parents = data.get("parents") if isinstance(data, dict) else None
    existing_tree = _verified_commit_tree_sha(commit, head_sha)
    parent_sha = (
        parents[0].get("sha")
        if isinstance(parents, list)
        and len(parents) == 1
        and isinstance(parents[0], dict)
        else ""
    )
    expected_message = f"Add owner comment for {repository} ({comment_id})"
    if (
        not commit.get("ok")
        or not isinstance(parent_sha, str)
        or not _SHA_RE.fullmatch(parent_sha)
        or not isinstance(existing_tree, str)
        or not _SHA_RE.fullmatch(existing_tree)
        or data.get("message") != expected_message
    ):
        return "", "", "", commit, "existing writeback branch commit is not exact"

    main_ref = await github.api_request(
        "GET", _api_path(f"/git/ref/heads/{BASE_BRANCH}"), token=token
    )
    current_main = _verified_ref_sha(main_ref, BASE_BRANCH)
    if not isinstance(current_main, str) or not _SHA_RE.fullmatch(current_main):
        return "", "", "", main_ref, "protected main ancestry could not be verified"
    if parent_sha != current_main:
        ancestry = await github.api_request(
            "GET", _api_path(f"/compare/{parent_sha}...{current_main}"), token=token
        )
        ancestry_data = (
            ancestry.get("data") if isinstance(ancestry.get("data"), dict) else {}
        )
        merge_base = ancestry_data.get("merge_base_commit")
        base_commit = ancestry_data.get("base_commit")
        compared_commits = ancestry_data.get("commits")
        if (
            not ancestry.get("ok")
            or ancestry_data.get("status") != "ahead"
            or type(ancestry_data.get("behind_by")) is not int
            or ancestry_data.get("behind_by") != 0
            or type(ancestry_data.get("ahead_by")) is not int
            or ancestry_data.get("ahead_by") < 1
            or not isinstance(merge_base, dict)
            or merge_base.get("sha") != parent_sha
            or not isinstance(base_commit, dict)
            or base_commit.get("sha") != parent_sha
            or not isinstance(compared_commits, list)
            or not compared_commits
            or not isinstance(compared_commits[-1], dict)
            or compared_commits[-1].get("sha") != current_main
        ):
            return (
                "",
                "",
                "",
                ancestry,
                "existing writeback branch is not based on current main history",
            )

    record_path = f"{COMMENTS_ROOT}/{repository}/{comment_id}.json"
    record_result = await github.api_request(
        "GET", _contents_path(record_path, head_sha), token=token
    )
    contract_results = [record_result]
    try:
        record_raw = _decode_contents_result(record_result, path=record_path)
        record = _decode_canonical_json(record_raw, label=record_path)
        created_at = record.get("created_at")
        _parse_timestamp(created_at, field=f"{comment_id}.created_at")
        expected_record = {
            "schema_version": SCHEMA_VERSION,
            "id": comment_id,
            "repository": repository,
            "created_at": created_at,
            "state": "unconsumed",
            "source": {"surface": SOURCE_SURFACE, "context": context},
            "comment": comment,
        }
        if record != expected_record or record_raw != _canonical_json_bytes(
            expected_record
        ):
            raise _ContractError("existing owner-comment record payload differs")

        parent_commit = await github.api_request(
            "GET", _api_path(f"/git/commits/{parent_sha}"), token=token
        )
        contract_results.append(parent_commit)
        parent_tree = _verified_commit_tree_sha(parent_commit, parent_sha)
        if not isinstance(parent_tree, str) or not _SHA_RE.fullmatch(parent_tree):
            raise _ContractError("existing branch parent tree is unavailable")
        readme_path = f"{COMMENTS_ROOT}/{repository}/README.md"
        root_result = await github.api_request(
            "GET", _contents_path(ROOT_INDEX_PATH, parent_sha), token=token
        )
        readme_result = await github.api_request(
            "GET", _contents_path(readme_path, parent_sha), token=token
        )
        contract_results.extend((root_result, readme_result))
        root_raw = _decode_contents_result(root_result, path=ROOT_INDEX_PATH)
        readme_raw = _decode_contents_result(readme_result, path=readme_path)
        root_data = _decode_canonical_json(root_raw, label=ROOT_INDEX_PATH)
        files = _updated_contract_files(
            root_data=root_data,
            repository=repository,
            comment=comment,
            comment_id=comment_id,
            created_at=created_at,
            context=context,
            repository_readme=readme_raw,
        )
    except _ContractError as exc:
        failed_result = next(
            (result for result in contract_results if not result.get("ok")),
            None,
        )
        return "", "", "", failed_result, str(exc)

    blob_shas: dict[str, str] = {}
    for path, expected in files.items():
        blob_sha, blob_result, error = await _create_blob(path, expected, token)
        if error:
            return (
                "",
                "",
                "",
                blob_result,
                f"existing branch tree could not be rebuilt: {error}",
            )
        blob_shas[path] = blob_sha
    tree_result = await github.api_request(
        "POST",
        _api_path("/git/trees"),
        json_body={
            "base_tree": parent_tree,
            "tree": [
                {"path": path, "mode": "100644", "type": "blob", "sha": sha}
                for path, sha in blob_shas.items()
            ],
        },
        token=token,
    )
    expected_tree = _response_sha(tree_result)
    if expected_tree != existing_tree:
        return (
            "",
            "",
            "",
            tree_result,
            "existing writeback branch contains changes outside the exact payload",
        )

    for path, expected in files.items():
        current = await github.api_request(
            "GET", _contents_path(path, head_sha), token=token
        )
        try:
            actual = _decode_contents_result(current, path=path)
        except _ContractError:
            return (
                "",
                "",
                "",
                current,
                f"existing writeback branch payload is unreadable at {path}",
            )
        if actual != expected:
            return (
                "",
                "",
                "",
                None,
                f"existing writeback branch payload differs at {path}",
            )
    return head_sha, parent_sha, created_at, None, ""


async def _open_ready_pr(
    *, branch: str, commit_sha: str, repository: str, comment_id: str, token: str
) -> tuple[int, str, dict[str, Any] | None, str]:
    body = (
        "Owner-authenticated control-plane feedback for "
        f"`{repository}`. Fleet Manager remains the durable record owner.\n\n"
        f"Record: `{comment_id}`. This comment is pending until this ready PR "
        "passes the required checks and merges into protected `main`."
    )
    result = await github.api_request(
        "POST",
        _api_path("/pulls"),
        json_body={
            "title": f"Owner comment for {repository}: {comment_id}",
            "head": branch,
            "base": BASE_BRANCH,
            "body": body,
            "draft": False,
        },
        token=token,
    )
    verified = _verified_pr(result.get("data"), branch=branch, commit_sha=commit_sha)
    if result.get("ok") and verified:
        return verified[0], verified[1], None, ""
    if result.get("status") == 422:
        existing = await github.api_request(
            "GET",
            _api_path(
                f"/pulls?head=menno420:{quote(branch, safe='')}&"
                f"base={BASE_BRANCH}&state=open"
            ),
            token=token,
        )
        candidates = existing.get("data") if isinstance(existing.get("data"), list) else []
        verified_candidates = [
            value
            for value in (
                _verified_pr(item, branch=branch, commit_sha=commit_sha)
                for item in candidates
            )
            if value is not None
        ]
        if existing.get("ok") and len(verified_candidates) == 1:
            number, url = verified_candidates[0]
            return number, url, None, ""
        return 0, "", existing, "existing ready PR could not be verified"
    if result.get("ok"):
        return 0, "", result, "GitHub opened a PR but its ready head/base could not be verified"
    return 0, "", result, f"could not open ready PR: {_result_error(result)}"


async def submit_owner_comment(
    repository: str,
    comment: str,
    *,
    context: str | None = None,
    submission_key: str | None = None,
    now: datetime | None = None,
) -> OwnerCommentWritebackResult:
    """Submit one comment to a ruleset-safe Fleet Manager PR.

    Validation checks but never strips ``comment``.  The exact string is
    serialized into the public record.  ``pending_pr`` is the strongest
    synchronous result this engine can return; durability is checked later by
    reading Fleet Manager ``main`` through the separate comment reader.
    """

    if not _valid_repository(repository):
        return _failure(str(repository or ""), "failed", "invalid repository name")
    problem = validate_comment(comment)
    if problem:
        return _failure(repository, "failed", problem)
    source_context = context if context is not None else f"/repos/{repository}"
    problem = _validate_context(source_context)
    if problem:
        return _failure(repository, "failed", problem)
    stable_key = submission_key or new_submission_key(now)
    problem = validate_submission_key(stable_key)
    if problem:
        return _failure(repository, "failed", problem)

    token = runtime_token()
    token_problem = _token_problem(token)
    if token_problem:
        return _failure(
            repository,
            "unavailable",
            f"{token_problem} No GitHub write was attempted.",
        )

    # Creation time is the first mutation request, not the potentially old GET
    # that rendered the form. The nonce keeps the id/branch stable; a replay
    # recovers the winning branch's authoritative timestamp below.
    created_at = _timestamp(now)
    comment_id = _comment_id(
        repository, comment, source_context, stable_key
    )
    branch = f"{BRANCH_PREFIX}{comment_id}"
    common = {
        "comment_id": comment_id,
        "created_at": created_at,
        "branch": branch,
    }

    base_ref = await github.api_request(
        "GET", _api_path(f"/git/ref/heads/{BASE_BRANCH}"), token=token
    )
    base_sha = _verified_ref_sha(base_ref, BASE_BRANCH)
    if not isinstance(base_sha, str) or not _SHA_RE.fullmatch(base_sha):
        return _failure(
            repository,
            _failure_state(base_ref),
            f"could not resolve Fleet Manager main: {_result_error(base_ref)}",
            **common,
        )

    base_commit = await github.api_request(
        "GET", _api_path(f"/git/commits/{base_sha}"), token=token
    )
    tree_sha = _verified_commit_tree_sha(base_commit, base_sha)
    if not isinstance(tree_sha, str) or not _SHA_RE.fullmatch(tree_sha):
        return _failure(
            repository,
            _failure_state(base_commit),
            f"could not resolve pinned Fleet Manager tree: {_result_error(base_commit)}",
            base_sha=base_sha,
            **common,
        )

    readme_path = f"{COMMENTS_ROOT}/{repository}/README.md"
    root_result = await github.api_request(
        "GET", _contents_path(ROOT_INDEX_PATH, base_sha), token=token
    )
    readme_result = await github.api_request(
        "GET", _contents_path(readme_path, base_sha), token=token
    )
    try:
        root_raw = _decode_contents_result(root_result, path=ROOT_INDEX_PATH)
        readme_raw = _decode_contents_result(readme_result, path=readme_path)
        root_data = _decode_canonical_json(root_raw, label=ROOT_INDEX_PATH)
        files = _updated_contract_files(
            root_data=root_data,
            repository=repository,
            comment=comment,
            comment_id=comment_id,
            created_at=created_at,
            context=source_context,
            repository_readme=readme_raw,
        )
    except _ContractError as exc:
        source = root_result if not root_result.get("ok") else readme_result
        state: WritebackState = (
            _failure_state(source)
            if not root_result.get("ok") or not readme_result.get("ok")
            else "failed"
        )
        return _failure(
            repository,
            state,
            str(exc),
            base_sha=base_sha,
            **common,
        )

    blob_shas: dict[str, str] = {}
    for path, content in files.items():
        blob_sha, blob_result, error = await _create_blob(path, content, token)
        if error:
            return _failure(
                repository,
                _failure_state(blob_result),
                error,
                base_sha=base_sha,
                **common,
            )
        blob_shas[path] = blob_sha

    tree_result = await github.api_request(
        "POST",
        _api_path("/git/trees"),
        json_body={
            "base_tree": tree_sha,
            "tree": [
                {"path": path, "mode": "100644", "type": "blob", "sha": sha}
                for path, sha in blob_shas.items()
            ],
        },
        token=token,
    )
    new_tree_sha = _response_sha(tree_result)
    if not isinstance(new_tree_sha, str) or not _SHA_RE.fullmatch(new_tree_sha):
        return _failure(
            repository,
            _failure_state(tree_result),
            f"could not create atomic owner-comment tree: {_result_error(tree_result)}",
            base_sha=base_sha,
            **common,
        )

    commit_result = await github.api_request(
        "POST",
        _api_path("/git/commits"),
        json_body={
            "message": f"Add owner comment for {repository} ({comment_id})",
            "tree": new_tree_sha,
            "parents": [base_sha],
        },
        token=token,
    )
    commit_sha = _response_sha(commit_result)
    if not isinstance(commit_sha, str) or not _SHA_RE.fullmatch(commit_sha):
        return _failure(
            repository,
            _failure_state(commit_result),
            f"could not create owner-comment commit: {_result_error(commit_result)}",
            base_sha=base_sha,
            **common,
        )

    ref_result = await github.api_request(
        "POST",
        _api_path("/git/refs"),
        json_body={"ref": f"refs/heads/{branch}", "sha": commit_sha},
        token=token,
    )
    if not ref_result.get("ok") and ref_result.get("status") != 422:
        permission_failure = ref_result.get("status") in (401, 403, 404)
        return _failure(
            repository,
            "unavailable" if permission_failure else "failed",
            (
                f"{ENV_TOKEN} cannot create the Fleet Manager branch; "
                "grant Contents read/write access and retry the unchanged "
                f"form: {_result_error(ref_result)}"
                if permission_failure
                else "writeback branch creation could not be confirmed; "
                "inspect Fleet Manager before retrying: "
                f"{_result_error(ref_result)}"
            ),
            base_sha=base_sha,
            commit_sha=commit_sha,
            **common,
        )

    # A shape-valid success response is not proof that GitHub stored the exact
    # commit. Verify the deterministic branch, commit identity, ancestry, full
    # tree, and all three bytes before opening or reporting a PR. The same path
    # safely reconciles a 422 from an unchanged lost-response replay.
    verified_sha, verified_base, verified_created_at, failed_result, error = (
        await _verify_existing_branch(
            branch=branch,
            repository=repository,
            comment=comment,
            comment_id=comment_id,
            context=source_context,
            token=token,
        )
    )
    if error:
        return _failure(
            repository,
            _failure_state(failed_result) if failed_result else "failed",
            f"writeback branch could not be verified: {error}",
            base_sha=base_sha,
            commit_sha=commit_sha,
            **common,
        )
    commit_sha = verified_sha
    base_sha = verified_base
    created_at = verified_created_at
    common["created_at"] = verified_created_at

    pr_number, pr_url, failed_result, error = await _open_ready_pr(
        branch=branch,
        commit_sha=commit_sha,
        repository=repository,
        comment_id=comment_id,
        token=token,
    )
    if error:
        permission_failure = (failed_result or {}).get("status") in (
            401,
            403,
            404,
        )
        return _failure(
            repository,
            "unavailable" if permission_failure else "failed",
            (
                f"{ENV_TOKEN} cannot open or verify the Fleet Manager PR; "
                "grant Pull requests read/write access, then open or inspect "
                f"a ready PR from `{branch}` to protected `{BASE_BRANCH}`. "
                "Do not resubmit this form until that branch is reconciled: "
                f"{error}"
                if permission_failure
                else f"{error}; inspect Fleet Manager before retrying"
            ),
            base_sha=base_sha,
            commit_sha=commit_sha,
            **common,
        )
    return OwnerCommentWritebackResult(
        state="pending_pr",
        repository=repository,
        comment_id=comment_id,
        created_at=created_at,
        branch=branch,
        base_sha=base_sha,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=pr_url,
        error="",
    )
