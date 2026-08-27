"""Fleet Manager owner-comment writeback contract, entirely network-free."""

from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
import httpx

from app import github, owner_comment_writeback as writeback


BASE_SHA = "a" * 40
BASE_TREE_SHA = "b" * 40
NEW_TREE_SHA = "c" * 40
COMMIT_SHA = "d" * 40
EXISTING_SHA = "e" * 40
EXISTING_TREE_SHA = "8" * 40
ADVANCED_SHA = "6" * 40
ADVANCED_TREE_SHA = "7" * 40
PR_URL = "https://github.com/menno420/fleet-manager/pull/1234"
NOW = datetime(2026, 8, 27, 10, 11, 12, tzinfo=timezone.utc)
SUBMISSION_KEY = "0123456789abcdef0123456789abcdef"


def _row(repository: str) -> dict[str, Any]:
    return {
        "repository": repository,
        "index": f"docs/owner-comments/{repository}/README.md",
        "unconsumed_count": 0,
        "consumed_count": 0,
        "latest_unconsumed_at": None,
        "latest_consumed_at": None,
    }


def _root_index(*, websites: dict[str, Any] | None = None) -> dict[str, Any]:
    # websites is intentionally second: the writeback must preserve Fleet
    # Manager's ESTATE-derived row order, not sort this as a second registry.
    return {
        "schema_version": 1,
        "derived_from": list(writeback.DERIVED_FROM),
        "repositories": [_row("fleet-manager"), websites or _row("websites")],
    }


def _canonical(data: Any) -> bytes:
    return (
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode()


def _envelope(status: int, data: Any = None, error: str = "") -> dict[str, Any]:
    return {
        "ok": 200 <= status < 300,
        "status": status,
        "data": data,
        "error": error,
    }


def _contents(content: bytes) -> dict[str, Any]:
    return _envelope(
        200,
        {
            "encoding": "base64",
            "content": base64.b64encode(content).decode(),
            "sha": "f" * 40,
        },
    )


class FakeGitHub:
    """Script the exact Git Data transaction and retain every request."""

    def __init__(
        self,
        *,
        root: bytes | None = None,
        readme: bytes | None = None,
        failure: tuple[str, int] | None = None,
        ref_exists: bool = False,
        pr_exists: bool = False,
        existing_payload_matches: bool = True,
        malformed_pr: bool = False,
        malformed: str = "",
        main_sha: str = BASE_SHA,
        existing_parent_sha: str = BASE_SHA,
        pr_number: int = 1234,
        pr_url: str = PR_URL,
        parent_root: bytes | None = None,
        parent_readme: bytes | None = None,
        expected_token: str = "fleet-only-token",
        compare_ahead_by: int = 1,
        preflight_ref_missing: bool = False,
        raced_ref_status: int | None = None,
    ) -> None:
        self.root = root if root is not None else _canonical(_root_index())
        self.readme = readme or writeback.render_repository_readme(
            "websites", [], []
        )
        self.failure = failure
        self.ref_exists = ref_exists
        self.pr_exists = pr_exists
        self.existing_payload_matches = existing_payload_matches
        self.malformed_pr = malformed_pr
        self.malformed = malformed
        self.main_sha = main_sha
        self.main_tree_sha = (
            ADVANCED_TREE_SHA if main_sha == ADVANCED_SHA else BASE_TREE_SHA
        )
        self.existing_parent_sha = existing_parent_sha
        self.parent_root = parent_root if parent_root is not None else self.root
        self.parent_readme = (
            parent_readme if parent_readme is not None else self.readme
        )
        self.pr_number = pr_number
        self.pr_url = pr_url
        self.expected_token = expected_token
        self.compare_ahead_by = compare_ahead_by
        self.preflight_ref_missing = preflight_ref_missing
        self.raced_ref_status = raced_ref_status
        self.branch_ref_reads = 0
        self.compare_response_sizes: list[int] = []
        self.existing_files: dict[str, bytes] = {}
        self.calls: list[tuple[str, str, Any, str]] = []
        self.blob_count = 0
        self.blob_payloads: dict[str, bytes] = {}
        self.files: dict[str, bytes] = {}
        self.branch = ""
        self.ref_created = False
        self.created_commit: dict[str, Any] = {}
        self.initial_tree_created = False

    def _fail(self, seam: str) -> dict[str, Any] | None:
        if self.failure and self.failure[0] == seam:
            status = self.failure[1]
            return _envelope(status, None, f"{seam} failed")
        return None

    def _pr(self, commit_sha: str) -> dict[str, Any]:
        data = {
            "number": self.pr_number,
            "html_url": self.pr_url,
            "state": "open",
            "draft": False,
            "head": {"ref": self.branch, "sha": commit_sha},
            "base": {"ref": "main"},
        }
        if self.malformed_pr:
            data["draft"] = True
        return data

    async def api_request(
        self, method: str, path: str, json_body: Any = None, token: str = ""
    ) -> dict[str, Any]:
        self.calls.append((method, path, json_body, token))
        assert token == self.expected_token

        if method == "GET" and path.endswith("/git/ref/heads/main"):
            if self.malformed == "base_ref":
                return _envelope(200, {"object": "not-an-object"})
            ref_name = (
                "refs/heads/not-main"
                if self.malformed == "base_ref_identity"
                else "refs/heads/main"
            )
            return self._fail("base_ref") or _envelope(
                200,
                {
                    "ref": ref_name,
                    "object": {"sha": self.main_sha, "type": "commit"},
                },
            )
        if method == "GET" and path.endswith(f"/git/commits/{self.main_sha}"):
            if self.malformed == "base_commit":
                return _envelope(200, {"tree": "not-an-object"})
            identity = (
                "9" * 40
                if self.malformed == "base_commit_identity"
                else self.main_sha
            )
            return self._fail("base_commit") or _envelope(
                200,
                {"sha": identity, "tree": {"sha": self.main_tree_sha}},
            )
        if (
            method == "GET"
            and path.endswith(f"/git/commits/{self.existing_parent_sha}")
        ):
            identity = (
                "9" * 40
                if self.malformed == "parent_commit_identity"
                else self.existing_parent_sha
            )
            return _envelope(
                200, {"sha": identity, "tree": {"sha": BASE_TREE_SHA}}
            )
        if method == "GET" and "/compare/" in path:
            if self.malformed == "ancestry":
                return _envelope(200, {"status": "diverged"})
            commits = [
                {"sha": "5" * 40}
                for _ in range(min(self.compare_ahead_by, 250))
            ]
            commits[-1] = {
                "sha": (
                    "9" * 40
                    if self.malformed == "compare_head"
                    else self.main_sha
                )
            }
            self.compare_response_sizes.append(len(commits))
            return _envelope(
                200,
                {
                    "status": "ahead",
                    "ahead_by": self.compare_ahead_by,
                    "behind_by": 0,
                    "base_commit": {"sha": self.existing_parent_sha},
                    "merge_base_commit": {"sha": self.existing_parent_sha},
                    "commits": commits,
                },
            )
        if method == "GET" and "/contents/" in path:
            parsed = urlparse(path)
            ref = parse_qs(parsed.query).get("ref", [""])[0]
            file_path = parsed.path.split("/contents/", 1)[1]
            if ref in {self.main_sha, self.existing_parent_sha}:
                failed = self._fail(
                    "root_read" if file_path.endswith("index.json") else "readme_read"
                )
                if failed:
                    return failed
                use_parent = (
                    ref == self.existing_parent_sha
                    and self.existing_parent_sha != self.main_sha
                )
                root = self.parent_root if use_parent else self.root
                readme = self.parent_readme if use_parent else self.readme
                return _contents(
                    root if file_path.endswith("index.json") else readme
                )
            if ref == EXISTING_SHA:
                payload = self.existing_files.get(file_path, b"")
                if not self.existing_payload_matches and file_path.endswith("index.json"):
                    payload += b"different"
                return _contents(payload)
            if ref == COMMIT_SHA:
                return _contents(self.files.get(file_path, b""))
            raise AssertionError(f"unexpected contents ref {ref}")
        if method == "POST" and path.endswith("/git/blobs"):
            seam = "replay_blob" if self.ref_exists else "blob"
            failed = self._fail(seam)
            if failed:
                return failed
            self.blob_count += 1
            sha = str(self.blob_count) * 40
            payload = base64.b64decode(json_body["content"])
            if self.malformed == "blob_content_mismatch" and self.blob_count <= 3:
                payload = b"not the requested owner-comment bytes\n"
            self.blob_payloads[sha] = payload
            return _envelope(201, {"sha": sha})
        if method == "POST" and path.endswith("/git/trees"):
            if self.malformed == "tree_error_sha":
                return _envelope(400, {"sha": NEW_TREE_SHA}, "bad tree")
            failed = self._fail("tree")
            if failed:
                return failed
            assert json_body["base_tree"] in {
                BASE_TREE_SHA,
                ADVANCED_TREE_SHA,
            }
            rendered_files = {
                entry["path"]: self.blob_payloads[entry["sha"]]
                for entry in json_body["tree"]
            }
            if not self.ref_exists:
                self.files = rendered_files
            return _envelope(
                201,
                {
                    "sha": (
                        EXISTING_TREE_SHA
                        if self.ref_exists
                        and json_body["base_tree"] == BASE_TREE_SHA
                        else NEW_TREE_SHA
                    )
                },
            )
        if method == "POST" and path.endswith("/git/commits"):
            if self.malformed == "commit_error_sha":
                return _envelope(400, {"sha": COMMIT_SHA}, "bad commit")
            failed = self._fail("commit")
            if failed:
                return failed
            self.created_commit = dict(json_body)
            return _envelope(201, {"sha": COMMIT_SHA})
        if method == "POST" and path.endswith("/git/refs"):
            self.branch = json_body["ref"].removeprefix("refs/heads/")
            failed = self._fail("ref")
            if failed:
                return failed
            if self.ref_exists:
                return _envelope(422, None, "Reference already exists")
            self.ref_created = True
            return _envelope(
                201,
                {
                    "ref": json_body["ref"],
                    "object": {"sha": COMMIT_SHA, "type": "commit"},
                },
            )
        if (
            method == "GET"
            and "/git/ref/heads/claude/owner-comments-" in path
        ):
            failed = self._fail("existing_ref_read")
            if failed:
                return failed
            requested_branch = path.split("/git/ref/heads/", 1)[1]
            if not self.branch:
                self.branch = requested_branch
            self.branch_ref_reads += 1
            if self.preflight_ref_missing and self.branch_ref_reads == 1:
                return _envelope(404, None, "Not Found")
            if self.raced_ref_status and self.branch_ref_reads == 2:
                return _envelope(
                    self.raced_ref_status,
                    None,
                    "raced ref lookup failed",
                )
            if not self.ref_exists and not self.ref_created:
                return _envelope(404, None, "Not Found")
            if self.malformed == "existing_ref":
                return _envelope(200, {"object": "not-an-object"})
            return _envelope(
                200,
                {
                    "ref": (
                        "refs/heads/not-this-branch"
                        if self.malformed == "existing_ref_identity"
                        else f"refs/heads/{self.branch}"
                    ),
                    "object": {
                        "sha": EXISTING_SHA if self.ref_exists else COMMIT_SHA,
                        "type": "commit",
                    },
                },
            )
        if method == "GET" and path.endswith(f"/git/commits/{COMMIT_SHA}"):
            return _envelope(
                200,
                {
                    "sha": COMMIT_SHA,
                    "tree": {"sha": self.created_commit.get("tree", NEW_TREE_SHA)},
                    "parents": [
                        {"sha": parent}
                        for parent in self.created_commit.get("parents", [BASE_SHA])
                    ],
                    "message": self.created_commit.get(
                        "message",
                        "Add owner comment for websites (missing)",
                    ),
                },
            )
        if method == "GET" and path.endswith(f"/git/commits/{EXISTING_SHA}"):
            if self.malformed == "existing_commit":
                return _envelope(
                    200,
                    {
                        "tree": "not-an-object",
                        "parents": [{"sha": BASE_SHA}],
                    },
                )
            if self.malformed == "existing_parents":
                return _envelope(
                    200,
                    {
                        "tree": {"sha": NEW_TREE_SHA},
                        "parents": [{"sha": BASE_SHA}, "not-an-object"],
                    },
                )
            return _envelope(
                200,
                {
                    "sha": (
                        "9" * 40
                        if self.malformed == "existing_commit_identity"
                        else EXISTING_SHA
                    ),
                    "tree": {
                        "sha": (
                            EXISTING_TREE_SHA
                            if self.existing_payload_matches
                            else "9" * 40
                        )
                    },
                    "parents": [{"sha": self.existing_parent_sha}],
                    "message": (
                        "Add owner comment for websites "
                        f"({self.branch.removeprefix(writeback.BRANCH_PREFIX)})"
                    ),
                },
            )
        if method == "POST" and path.endswith("/pulls"):
            failed = self._fail("pr")
            if failed:
                return failed
            if self.pr_exists:
                return _envelope(422, None, "A pull request already exists")
            return _envelope(201, self._pr(EXISTING_SHA if self.ref_exists else COMMIT_SHA))
        if method == "GET" and "/pulls?" in path:
            failed = self._fail("pr_list")
            if failed:
                return failed
            return _envelope(
                200,
                [self._pr(EXISTING_SHA)] if self.pr_exists else [],
            )
        raise AssertionError(f"unexpected GitHub call: {method} {path}")


@pytest.fixture(autouse=True)
def _dedicated_token(monkeypatch):
    monkeypatch.setenv(writeback.ENV_TOKEN, "fleet-only-token")


def _submit(
    fake: FakeGitHub,
    monkeypatch,
    *,
    comment: str = "  Keep this wording.\nSecond line.  ",
    repository: str = "websites",
    context: str | None = None,
    submission_key: str = SUBMISSION_KEY,
    now: datetime = NOW,
):
    if fake.ref_exists:
        created_at = getattr(
            fake, "existing_created_at", writeback._timestamp(NOW)
        )
        source_context = context or f"/repos/{repository}"
        comment_id = writeback._comment_id(
            repository,
            comment,
            source_context,
            submission_key,
        )
        fake.branch = f"{writeback.BRANCH_PREFIX}{comment_id}"
        fake.existing_files = writeback._updated_contract_files(
            root_data=json.loads(fake.parent_root),
            repository=repository,
            comment=comment,
            comment_id=comment_id,
            created_at=created_at,
            context=source_context,
            repository_readme=fake.parent_readme,
        )
    monkeypatch.setattr(github, "api_request", fake.api_request)
    return asyncio.run(
        writeback.submit_owner_comment(
            repository,
            comment,
            context=context,
            submission_key=submission_key,
            now=now,
        )
    )


def test_readme_renderer_matches_fleet_manager_v1_vector():
    active = [
        writeback._ActiveIndexEntry(
            "20260827t101112z-abc123def456",
            "2026-08-27T10:11:12Z",
            "control-plane",
        )
    ]
    consumed = [
        writeback._ConsumedIndexEntry(
            "20260826t090000z-fed654cba321",
            "2026-08-26T09:00:00Z",
            "2026-08-27T08:00:00Z",
        )
    ]
    expected = """# Owner comments — `websites`

> **Status:** `living-ledger`
>
> **Generated index.** Run `python3 tools/owner_comments.py reindex`;
> do not hand-edit this file. **Every record and all of its metadata
> are public.** Read the [storage and privacy contract](../README.md)
> before adding feedback. JSON preserves the owner's wording verbatim.

## Unconsumed (1)

| id | created at | source | record |
|---|---|---|---|
| `20260827t101112z-abc123def456` | `2026-08-27T10:11:12Z` | control-plane | [`20260827t101112z-abc123def456.json`](20260827t101112z-abc123def456.json) |

## Consumed history (1)

| id | created at | consumed at | preserved record |
|---|---|---|---|
| `20260826t090000z-fed654cba321` | `2026-08-26T09:00:00Z` | `2026-08-27T08:00:00Z` | [`20260826t090000z-fed654cba321.json`](consumed/20260826t090000z-fed654cba321.json) |

## Consume mechanically

After acting or explicitly reconciling a comment, run:

```text
python3 tools/owner_comments.py consume websites <comment-id> \\
  --actor <session-card-or-actor> --evidence <record-or-PR-link>
```

Commit the moved record and both changed indexes together. Never delete it.
"""

    rendered = writeback.render_repository_readme("websites", active, consumed)
    assert rendered == expected.encode()
    assert writeback._parse_repository_readme(rendered, "websites") == (
        active,
        consumed,
    )


def test_missing_dedicated_token_makes_zero_calls_and_never_falls_back(
    monkeypatch,
):
    monkeypatch.delenv(writeback.ENV_TOKEN, raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-be-used")
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("GitHub must not be reached without the dedicated token")

    monkeypatch.setattr(github, "api_request", forbidden)
    result = asyncio.run(writeback.submit_owner_comment("websites", "hello"))

    assert result.state == "unavailable"
    assert writeback.ENV_TOKEN in result.message
    assert result.record_id == ""
    assert calls == []
    capability = writeback.capability()
    assert capability.available is False
    assert capability.token_env == writeback.ENV_TOKEN
    assert "must-not-be-used" not in repr(capability)


def test_malformed_dedicated_token_never_reaches_or_leaks_from_transport(
    monkeypatch,
):
    sentinel = "fleet-super\nsecret"
    monkeypatch.setenv(writeback.ENV_TOKEN, sentinel)
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(github, "api_request", forbidden)
    result = asyncio.run(
        writeback.submit_owner_comment(
            "websites", "hello", submission_key=SUBMISSION_KEY
        )
    )

    assert result.state == "unavailable"
    assert sentinel not in result.message
    assert "invalid header" in result.message
    assert calls == []


def test_upstream_error_body_cannot_echo_write_token(monkeypatch):
    token = "fleet-only-token"

    async def echoing_api(method, path, json_body=None, token=""):
        return _envelope(403, None, f"denied bearer {token}")

    monkeypatch.setattr(github, "api_request", echoing_api)
    result = asyncio.run(
        writeback.submit_owner_comment(
            "websites", "hello", submission_key=SUBMISSION_KEY
        )
    )

    assert result.state == "unavailable"
    assert token not in result.message
    assert "[credential redacted]" in result.message


def test_successful_contract_payload_cannot_echo_write_token(monkeypatch):
    token_row = _row("fleet-only-token")
    token_row["index"] = "docs/owner-comments/not-the-token/README.md"
    result = _submit(
        FakeGitHub(root=_canonical(_root_index(websites=token_row))),
        monkeypatch,
    )

    assert result.state == "failed"
    assert "fleet-only-token" not in result.message
    assert "[credential redacted]" in result.message


def test_duplicate_key_contract_error_cannot_echo_escaped_token(monkeypatch):
    token = r"fleet\secret-token"
    monkeypatch.setenv(writeback.ENV_TOKEN, token)
    root = (
        b'{"fleet\\\\secret-token":1,"fleet\\\\secret-token":2}\n'
    )
    result = _submit(
        FakeGitHub(root=root, expected_token=token),
        monkeypatch,
    )

    assert result.state == "failed"
    assert "secret-token" not in result.message
    assert result.message == "duplicate JSON key"


def test_upstream_surrogate_error_is_render_safe(monkeypatch):
    async def surrogate_api(method, path, json_body=None, token=""):
        return _envelope(422, None, "\ud800")

    monkeypatch.setattr(github, "api_request", surrogate_api)
    result = asyncio.run(
        writeback.submit_owner_comment(
            "websites", "hello", submission_key=SUBMISSION_KEY
        )
    )

    assert result.state == "failed"
    assert result.message.endswith("HTTP 422 — invalid Unicode error body")
    assert result.message.encode("utf-8")


def test_per_request_transport_error_never_echoes_token(monkeypatch):
    sentinel = "fleet-super\nsecret"

    class BadClient:
        async def request(self, *args, **kwargs):
            raise httpx.LocalProtocolError(
                f"Illegal header value b'Bearer {sentinel}'"
            )

    monkeypatch.setattr(github, "get_client", lambda raw=False: BadClient())
    result = asyncio.run(
        github.api_request("GET", "/repos/example", token=sentinel)
    )

    assert result["ok"] is False
    assert sentinel not in result["error"]
    assert result["error"] == "LocalProtocolError: GitHub request transport failed"


def test_atomic_three_file_commit_preserves_verbatim_text_and_opens_ready_pr(
    monkeypatch,
):
    fake = FakeGitHub()
    comment = "  Keep this wording.\nSecond line.  "
    result = _submit(fake, monkeypatch, comment=comment)

    assert result.state == "pending_pr"
    assert result.ok is True
    assert result.pr_number == 1234 and result.pr_url == PR_URL
    assert result.record_id.startswith("oc-")
    assert len(result.record_id) == 35
    assert result.branch == f"claude/owner-comments-{result.record_id}"
    assert "not durable until" in result.message

    assert set(fake.files) == {
        f"docs/owner-comments/websites/{result.record_id}.json",
        "docs/owner-comments/websites/README.md",
        "docs/owner-comments/index.json",
    }
    record = json.loads(
        fake.files[f"docs/owner-comments/websites/{result.record_id}.json"]
    )
    assert record == {
        "schema_version": 1,
        "id": result.record_id,
        "repository": "websites",
        "created_at": "2026-08-27T10:11:12Z",
        "state": "unconsumed",
        "source": {"surface": "control-plane", "context": "/repos/websites"},
        "comment": comment,
    }
    assert fake.files[
        f"docs/owner-comments/websites/{result.record_id}.json"
    ] == _canonical(record)

    root = json.loads(fake.files["docs/owner-comments/index.json"])
    assert [row["repository"] for row in root["repositories"]] == [
        "fleet-manager",
        "websites",
    ]
    row = root["repositories"][1]
    assert row["unconsumed_count"] == 1
    assert row["latest_unconsumed_at"] == "2026-08-27T10:11:12Z"
    readme = fake.files["docs/owner-comments/websites/README.md"].decode()
    assert "## Unconsumed (1)" in readme
    assert f"`{result.record_id}`" in readme

    # Exact pinned reads precede mutation. After the only ref mutation creates
    # the branch, a second bounded pass proves its commit/tree/three files
    # before the ready PR is opened.
    content_reads = [call for call in fake.calls if call[0] == "GET" and "/contents/" in call[1]]
    assert len(content_reads) == 8
    assert sum(f"ref={BASE_SHA}" in call[1] for call in content_reads) == 4
    assert sum(f"ref={COMMIT_SHA}" in call[1] for call in content_reads) == 4
    blob_calls = [call for call in fake.calls if call[1].endswith("/git/blobs")]
    tree_calls = [call for call in fake.calls if call[1].endswith("/git/trees")]
    commit_calls = [
        call
        for call in fake.calls
        if call[1].endswith("/git/commits") and call[0] == "POST"
    ]
    ref_calls = [call for call in fake.calls if call[1].endswith("/git/refs")]
    assert len(blob_calls) == 6
    assert len(tree_calls) == 2
    assert len(commit_calls) == len(ref_calls) == 1
    assert commit_calls[0][2]["parents"] == [BASE_SHA]
    assert commit_calls[0][2]["tree"] == NEW_TREE_SHA
    assert ref_calls[0][2] == {
        "ref": f"refs/heads/{result.branch}",
        "sha": COMMIT_SHA,
    }
    assert not any(call[0] in {"PATCH", "PUT", "DELETE"} for call in fake.calls)
    pr_call = fake.calls[-1]
    assert pr_call[0] == "POST" and pr_call[1].endswith("/pulls")
    assert pr_call[2]["head"] == result.branch
    assert pr_call[2]["base"] == "main"
    assert pr_call[2]["draft"] is False


def test_source_context_is_pinned_and_part_of_deterministic_id(monkeypatch):
    first = _submit(FakeGitHub(), monkeypatch, context="/repos/websites?filter=active")
    second = _submit(FakeGitHub(), monkeypatch, context="/repos/websites?filter=active")
    third = _submit(FakeGitHub(), monkeypatch, context="/repos/websites")

    assert first.record_id == second.record_id
    assert third.record_id != first.record_id


def test_submission_key_makes_lost_response_replay_exactly_idempotent(
    monkeypatch,
):
    first = _submit(FakeGitHub(), monkeypatch)
    replay = _submit(
        FakeGitHub(ref_exists=True, pr_exists=True),
        monkeypatch,
        submission_key=SUBMISSION_KEY,
    )
    distinct = _submit(
        FakeGitHub(),
        monkeypatch,
        submission_key="fedcba9876543210fedcba9876543210",
    )

    assert replay.state == "pending_pr"
    assert replay.record_id == first.record_id
    assert replay.branch == first.branch
    assert replay.created_at == first.created_at
    assert distinct.record_id != first.record_id


def test_form_age_does_not_backdate_first_submission(monkeypatch):
    late_submit = datetime(2026, 9, 3, 8, 9, 10, tzinfo=timezone.utc)
    fake = FakeGitHub()
    result = _submit(fake, monkeypatch, now=late_submit)

    assert result.state == "pending_pr"
    assert result.created_at == "2026-09-03T08:09:10Z"
    record = json.loads(
        fake.files[
            f"docs/owner-comments/websites/{result.record_id}.json"
        ]
    )
    assert record["created_at"] == result.created_at


def test_exact_replay_after_main_advances_recovers_original_receipt(monkeypatch):
    fake = FakeGitHub(
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
    )
    fake.existing_created_at = "2026-08-27T10:11:12Z"
    replay = _submit(
        fake,
        monkeypatch,
        now=datetime(2026, 8, 28, 10, 11, 12, tzinfo=timezone.utc),
    )

    assert replay.state == "pending_pr"
    assert replay.commit_sha == EXISTING_SHA
    assert replay.base_sha == BASE_SHA
    assert replay.created_at == "2026-08-27T10:11:12Z"
    assert any("/compare/" in call[1] for call in fake.calls)


def test_unpaginated_compare_keeps_current_main_as_tail_beyond_250(monkeypatch):
    fake = FakeGitHub(
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
        compare_ahead_by=251,
    )

    result = _submit(fake, monkeypatch)

    assert result.state == "pending_pr"
    compare_calls = [
        call for call in fake.calls if call[0] == "GET" and "/compare/" in call[1]
    ]
    assert len(compare_calls) == 1
    assert "?" not in compare_calls[0][1]
    assert fake.compare_response_sizes == [250]


def test_replay_rebuilds_against_original_indexes_after_newer_comment(
    monkeypatch,
):
    other = writeback._ActiveIndexEntry(
        "oc-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "2026-08-27T10:10:00Z",
        "control-plane",
    )
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": other.created_at,
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=current_row)),
        readme=writeback.render_repository_readme("websites", [other], []),
        parent_root=_canonical(_root_index()),
        parent_readme=writeback.render_repository_readme("websites", [], []),
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
    )
    replay = _submit(
        fake,
        monkeypatch,
        now=datetime(2026, 8, 28, 10, 11, 12, tzinfo=timezone.utc),
    )

    assert replay.state == "pending_pr"
    assert replay.base_sha == BASE_SHA
    assert replay.created_at == "2026-08-27T10:11:12Z"


def test_replay_rejects_branch_outside_protected_main_history(monkeypatch):
    result = _submit(
        FakeGitHub(
            ref_exists=True,
            pr_exists=True,
            main_sha=ADVANCED_SHA,
            malformed="ancestry",
        ),
        monkeypatch,
    )

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "not based on current main history" in result.message


def test_malformed_submission_key_rejects_before_github(monkeypatch):
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(github, "api_request", forbidden)
    result = asyncio.run(
        writeback.submit_owner_comment(
            "websites", "hello", submission_key="owner-chosen"
        )
    )

    assert result.state == "failed"
    assert "submission key" in result.message
    assert calls == []


@pytest.mark.parametrize(
    ("repository", "comment", "context", "needle"),
    [
        ("../websites", "hello", None, "invalid repository"),
        ("websites", "   \n", None, "non-whitespace"),
        ("websites", "x" * 20_001, None, "exceeds"),
        ("websites", "bad\x00text", None, "NUL"),
        ("websites", "bad\ud800text", None, "surrogate"),
        ("websites", "hello", "bad\x00context", "context"),
    ],
)
def test_validation_rejects_before_any_github_call(
    monkeypatch, repository, comment, context, needle
):
    calls = []

    async def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("invalid input must not reach GitHub")

    monkeypatch.setattr(github, "api_request", forbidden)
    result = asyncio.run(
        writeback.submit_owner_comment(repository, comment, context=context, now=NOW)
    )
    assert result.state == "failed"
    assert needle in result.message
    assert calls == []


@pytest.mark.parametrize(
    "root",
    [
        _canonical({**_root_index(), "schema_version": 2}),
        _canonical({**_root_index(), "schema_version": True}),
        json.dumps(_root_index()).encode(),  # valid but non-canonical JSON
        _canonical({**_root_index(), "derived_from": ["a newer contract"]}),
        b'{"schema_version": ' + (b"9" * 5_000) + b"}\n",
        b'{"x":' + (b"[" * 2_000) + b"0" + (b"]" * 2_000) + b"}\n",
    ],
)
def test_v1_root_schema_or_canonical_mismatch_blocks_mutation(monkeypatch, root):
    fake = FakeGitHub(root=root)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert not any(call[0] == "POST" for call in fake.calls)


def test_casefold_duplicate_root_repository_blocks_mutation(monkeypatch):
    root = _root_index()
    root["repositories"].append(_row("Websites"))
    fake = FakeGitHub(root=_canonical(root))

    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "duplicate repo" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_malformed_repository_readme_blocks_mutation(monkeypatch):
    fake = FakeGitHub(readme=b"# hand-edited markdown\n")
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "README" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_hostile_repository_count_blocks_mutation_without_escaping(monkeypatch):
    hostile = writeback.render_repository_readme("websites", [], []).replace(
        b"## Unconsumed (0)",
        b"## Unconsumed (" + (b"9" * 5_000) + b")",
    )
    fake = FakeGitHub(readme=hostile)

    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "bounded count" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


@pytest.mark.parametrize("field", ("unconsumed_count", "consumed_count"))
def test_root_count_over_contract_bound_blocks_mutation(monkeypatch, field):
    row = _row("websites")
    row[field] = writeback.MAX_INDEX_RECORDS + 1
    row[
        "latest_unconsumed_at"
        if field == "unconsumed_count"
        else "latest_consumed_at"
    ] = "2026-08-27T10:11:12Z"

    fake = FakeGitHub(root=_canonical(_root_index(websites=row)))
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "exceeds the bounded count" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_prospective_active_count_at_contract_bound_blocks_mutation(monkeypatch):
    monkeypatch.setattr(writeback, "MAX_INDEX_RECORDS", 1)
    active = [
        writeback._ActiveIndexEntry(
            "oc-existing",
            "2026-08-26T10:11:12Z",
            "control-plane",
        )
    ]
    row = _row("websites")
    row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": "2026-08-26T10:11:12Z",
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=row)),
        readme=writeback.render_repository_readme("websites", active, []),
    )

    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "prospective repository README active count" in result.message
    assert "exceeds the bounded count" in result.message
    assert fake.branch_ref_reads == 2
    assert not any(call[0] == "POST" for call in fake.calls)


@pytest.mark.parametrize(
    ("remaining_chars", "expected_state"),
    ((0, "pending_pr"), (-1, "failed")),
)
def test_prospective_readme_size_honors_exact_character_bound(
    monkeypatch, remaining_chars, expected_state
):
    comment = "  Keep this wording.\nSecond line.  "
    comment_id = writeback._comment_id(
        "websites", comment, "/repos/websites", SUBMISSION_KEY
    )
    prospective = writeback.render_repository_readme(
        "websites",
        [
            writeback._ActiveIndexEntry(
                comment_id,
                writeback._timestamp(NOW),
                writeback.SOURCE_SURFACE,
            )
        ],
        [],
    )
    monkeypatch.setattr(
        writeback,
        "MAX_INDEX_CHARS",
        len(prospective) + remaining_chars,
    )
    fake = FakeGitHub()

    result = _submit(fake, monkeypatch, comment=comment)

    assert result.state == expected_state
    if remaining_chars == 0:
        assert len(fake.files["docs/owner-comments/websites/README.md"]) == len(
            prospective
        )
    else:
        assert "prospective repository owner-comment README" in result.message
        assert "exceeds bounded read size" in result.message
        assert not any(call[0] == "POST" for call in fake.calls)


@pytest.mark.parametrize(
    ("remaining_chars", "expected_state"),
    ((0, "pending_pr"), (-1, "failed")),
)
def test_prospective_root_size_honors_exact_character_bound_before_blobs(
    monkeypatch, remaining_chars, expected_state
):
    root = _root_index()
    root["repositories"][1:1] = [
        _row(f"padding-repository-{index:02d}") for index in range(12)
    ]
    comment = "  Keep this wording.\nSecond line.  "
    comment_id = writeback._comment_id(
        "websites", comment, "/repos/websites", SUBMISSION_KEY
    )
    expected = writeback._updated_contract_files(
        root_data=json.loads(_canonical(root)),
        repository="websites",
        comment=comment,
        comment_id=comment_id,
        created_at=writeback._timestamp(NOW),
        context="/repos/websites",
        repository_readme=writeback.render_repository_readme(
            "websites", [], []
        ),
    )
    prospective_root = expected[writeback.ROOT_INDEX_PATH]
    assert len(prospective_root) > len(
        expected["docs/owner-comments/websites/README.md"]
    )
    monkeypatch.setattr(
        writeback,
        "MAX_INDEX_CHARS",
        len(prospective_root.decode("utf-8")) + remaining_chars,
    )
    fake = FakeGitHub(root=_canonical(root))

    result = _submit(fake, monkeypatch, comment=comment)

    assert result.state == expected_state
    if remaining_chars == 0:
        assert fake.files[writeback.ROOT_INDEX_PATH] == prospective_root
    else:
        assert "prospective root owner-comment index" in result.message
        assert "exceeds bounded read size" in result.message
        assert not any(call[0] == "POST" for call in fake.calls)


def test_active_count_rejection_recovers_a_concurrently_created_branch(monkeypatch):
    monkeypatch.setattr(writeback, "MAX_INDEX_RECORDS", 1)
    other = writeback._ActiveIndexEntry(
        "oc-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "2026-08-27T10:10:00Z",
        writeback.SOURCE_SURFACE,
    )
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": other.created_at,
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=current_row)),
        readme=writeback.render_repository_readme("websites", [other], []),
        parent_root=_canonical(_root_index()),
        parent_readme=writeback.render_repository_readme("websites", [], []),
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
        preflight_ref_missing=True,
    )

    replay = _submit(fake, monkeypatch)

    assert replay.state == "pending_pr"
    assert replay.base_sha == BASE_SHA
    assert fake.branch_ref_reads == 2
    assert any(
        call[0] == "GET"
        and "/contents/" in call[1]
        and f"ref={ADVANCED_SHA}" in call[1]
        for call in fake.calls
    )
    assert not any(
        call[0] == "POST"
        and (call[1].endswith("/git/refs") or call[1].endswith("/git/commits"))
        for call in fake.calls
    )


def test_readme_growth_rejection_recovers_a_concurrently_created_branch(monkeypatch):
    other = writeback._ActiveIndexEntry(
        "oc-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "2026-08-27T10:10:00Z",
        writeback.SOURCE_SURFACE,
    )
    current_readme = writeback.render_repository_readme(
        "websites", [other], []
    )
    replay_id = writeback._comment_id(
        "websites",
        "  Keep this wording.\nSecond line.  ",
        "/repos/websites",
        SUBMISSION_KEY,
    )
    prospective_readme = writeback.render_repository_readme(
        "websites",
        [
            other,
            writeback._ActiveIndexEntry(
                replay_id,
                writeback._timestamp(NOW),
                writeback.SOURCE_SURFACE,
            ),
        ],
        [],
    )
    assert len(prospective_readme) > len(current_readme)
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": other.created_at,
        }
    )
    monkeypatch.setattr(writeback, "MAX_INDEX_CHARS", len(current_readme))
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=current_row)),
        readme=current_readme,
        parent_root=_canonical(_root_index()),
        parent_readme=writeback.render_repository_readme("websites", [], []),
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
        preflight_ref_missing=True,
    )

    replay = _submit(fake, monkeypatch)

    assert replay.state == "pending_pr"
    assert replay.base_sha == BASE_SHA
    assert fake.branch_ref_reads == 2
    assert any(
        call[0] == "GET"
        and "/contents/" in call[1]
        and f"ref={ADVANCED_SHA}" in call[1]
        for call in fake.calls
    )
    assert not any(
        call[0] == "POST"
        and (call[1].endswith("/git/refs") or call[1].endswith("/git/commits"))
        for call in fake.calls
    )


def test_root_growth_rejection_recovers_a_concurrently_created_branch(monkeypatch):
    active = [
        writeback._ActiveIndexEntry(
            f"oc-existing-{index:02d}",
            f"2026-08-27T10:10:{index:02d}Z",
            writeback.SOURCE_SURFACE,
        )
        for index in range(9)
    ]
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 9,
            "latest_unconsumed_at": active[-1].created_at,
        }
    )
    current_root = _root_index(websites=current_row)
    current_root["repositories"][1:1] = [
        _row(f"padding-repository-{index:02d}") for index in range(20)
    ]
    parent_root = json.loads(_canonical(current_root))
    parent_row = next(
        row
        for row in parent_root["repositories"]
        if row["repository"] == "websites"
    )
    parent_row.update(
        {"unconsumed_count": 0, "latest_unconsumed_at": None}
    )
    current_root_bytes = _canonical(current_root)
    prospective_root = json.loads(current_root_bytes)
    prospective_row = next(
        row
        for row in prospective_root["repositories"]
        if row["repository"] == "websites"
    )
    prospective_row.update(
        {
            "unconsumed_count": 10,
            "latest_unconsumed_at": writeback._timestamp(NOW),
        }
    )
    assert len(_canonical(prospective_root)) == len(current_root_bytes) + 1
    current_readme = writeback.render_repository_readme(
        "websites", active, []
    )
    assert len(current_root_bytes) > len(current_readme)
    monkeypatch.setattr(
        writeback, "MAX_INDEX_CHARS", len(current_root_bytes.decode("utf-8"))
    )
    fake = FakeGitHub(
        root=current_root_bytes,
        readme=current_readme,
        parent_root=_canonical(parent_root),
        parent_readme=writeback.render_repository_readme("websites", [], []),
        ref_exists=True,
        pr_exists=True,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
        preflight_ref_missing=True,
    )

    replay = _submit(fake, monkeypatch)

    assert replay.state == "pending_pr"
    assert replay.base_sha == BASE_SHA
    assert fake.branch_ref_reads == 2
    assert any(
        call[0] == "GET"
        and "/contents/" in call[1]
        and f"ref={ADVANCED_SHA}" in call[1]
        for call in fake.calls
    )
    assert not any(
        call[0] == "POST"
        and (call[1].endswith("/git/refs") or call[1].endswith("/git/commits"))
        for call in fake.calls
    )


def test_contract_rejection_race_never_reuses_a_different_branch(monkeypatch):
    monkeypatch.setattr(writeback, "MAX_INDEX_RECORDS", 1)
    other = writeback._ActiveIndexEntry(
        "oc-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "2026-08-27T10:10:00Z",
        writeback.SOURCE_SURFACE,
    )
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": other.created_at,
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=current_row)),
        readme=writeback.render_repository_readme("websites", [other], []),
        parent_root=_canonical(_root_index()),
        parent_readme=writeback.render_repository_readme("websites", [], []),
        ref_exists=True,
        pr_exists=True,
        existing_payload_matches=False,
        main_sha=ADVANCED_SHA,
        existing_parent_sha=BASE_SHA,
        preflight_ref_missing=True,
    )

    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert fake.branch_ref_reads == 2
    assert "could not be verified" in result.message
    assert not any(
        call[0] == "POST" and call[1].endswith("/pulls")
        for call in fake.calls
    )


def test_contract_rejection_with_unknown_raced_ref_is_retryable(monkeypatch):
    monkeypatch.setattr(writeback, "MAX_INDEX_RECORDS", 1)
    other = writeback._ActiveIndexEntry(
        "oc-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "2026-08-27T10:10:00Z",
        writeback.SOURCE_SURFACE,
    )
    current_row = _row("websites")
    current_row.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": other.created_at,
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=current_row)),
        readme=writeback.render_repository_readme("websites", [other], []),
        preflight_ref_missing=True,
        raced_ref_status=503,
    )

    result = _submit(fake, monkeypatch)

    assert result.state == "failed_retryable"
    assert fake.branch_ref_reads == 2
    assert "replay branch existence could not be rechecked" in result.message
    assert "bounded count" not in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_consumption_before_creation_blocks_mutation(monkeypatch):
    consumed = [
        writeback._ConsumedIndexEntry(
            "20260827t101112z-abc123def456",
            "2026-08-27T10:11:12Z",
            "2026-08-27T10:11:11Z",
        )
    ]
    readme = writeback.render_repository_readme("websites", [], consumed)
    root_row = _row("websites")
    root_row.update(
        {
            "consumed_count": 1,
            "latest_consumed_at": "2026-08-27T10:11:11Z",
        }
    )
    fake = FakeGitHub(
        root=_canonical(_root_index(websites=root_row)), readme=readme
    )

    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "predates" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_stale_root_count_disagreeing_with_readme_blocks_mutation(monkeypatch):
    stale = _row("websites")
    stale.update(
        {
            "unconsumed_count": 1,
            "latest_unconsumed_at": "2026-08-26T00:00:00Z",
        }
    )
    fake = FakeGitHub(root=_canonical(_root_index(websites=stale)))
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "counts disagree" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


def test_repository_must_exist_in_pinned_fleet_index(monkeypatch):
    fake = FakeGitHub()
    result = _submit(fake, monkeypatch, repository="substrate-kit")

    assert result.state == "failed"
    assert "not indexed" in result.message
    assert not any(call[0] == "POST" for call in fake.calls)


@pytest.mark.parametrize(
    ("seam", "status", "expected"),
    [
        ("base_ref", 403, "unavailable"),
        ("base_ref", 500, "failed_retryable"),
        ("base_commit", 409, "failed_retryable"),
        ("root_read", 404, "unavailable"),
        ("readme_read", 503, "failed_retryable"),
        ("blob", 403, "unavailable"),
        ("tree", 422, "failed"),
        ("commit", 500, "failed_retryable"),
        ("ref", 403, "unavailable"),
        ("ref", 503, "failed"),
        ("pr", 403, "unavailable"),
        ("pr", 500, "failed"),
    ],
)
def test_upstream_failures_never_claim_pending_or_durable(
    monkeypatch, seam, status, expected
):
    fake = FakeGitHub(failure=(seam, status))
    result = _submit(fake, monkeypatch)

    assert result.state == expected
    assert result.ok is False
    assert result.pr_number == 0 and result.pr_url == ""
    assert "durable" not in result.state


@pytest.mark.parametrize(
    ("seam", "scope"),
    (("ref", "Contents read/write"), ("pr", "Pull requests read/write")),
)
def test_post_commit_permission_failure_names_required_scope(
    monkeypatch, seam, scope
):
    result = _submit(FakeGitHub(failure=(seam, 403)), monkeypatch)

    assert result.state == "unavailable"
    assert writeback.ENV_TOKEN in result.message
    assert scope in result.message
    if seam == "ref":
        assert "unchanged form" in result.message
    else:
        assert result.branch in result.message
        assert "Do not resubmit" in result.message


def test_deep_github_json_becomes_an_honest_writer_failure(monkeypatch):
    deep = b"[" * 10_000 + b"0" + b"]" * 10_000

    async def exercise():
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=deep,
                headers={"content-type": "application/json"},
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        github.set_clients(client, client)
        try:
            return await writeback.submit_owner_comment(
                "websites",
                "hello",
                submission_key=SUBMISSION_KEY,
            )
        finally:
            await client.aclose()

    result = asyncio.run(exercise())

    assert result.state == "failed_retryable"
    assert result.ok is False
    assert "malformed GitHub JSON response" in result.message


def test_success_response_with_unverified_pr_is_not_pending(monkeypatch):
    fake = FakeGitHub(malformed_pr=True)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "could not be verified" in result.message
    assert result.commit_sha == COMMIT_SHA
    assert result.pr_number == 0


@pytest.mark.parametrize("ref_exists", (False, True))
def test_pr_url_must_match_returned_number_on_create_and_reuse(
    monkeypatch, ref_exists
):
    result = _submit(
        FakeGitHub(
            ref_exists=ref_exists,
            pr_exists=ref_exists,
            pr_number=1234,
            pr_url=(
                "https://github.com/menno420/fleet-manager/pull/9999"
            ),
        ),
        monkeypatch,
    )

    assert result.state == "failed"
    assert result.pr_number == 0
    assert result.pr_url == ""
    assert "could not be verified" in result.message


@pytest.mark.parametrize("seam", ("tree_error_sha", "commit_error_sha"))
def test_error_envelope_with_valid_sha_never_advances_to_pending(
    monkeypatch, seam
):
    fake = FakeGitHub(malformed=seam)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert not any(
        call[0] == "POST" and call[1].endswith("/git/refs")
        for call in fake.calls
    )


@pytest.mark.parametrize(
    "seam",
    ("base_ref", "base_commit", "base_ref_identity", "base_commit_identity"),
)
def test_malformed_base_nested_shape_is_an_honest_failure(monkeypatch, seam):
    result = _submit(FakeGitHub(malformed=seam), monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "could not resolve" in result.message


@pytest.mark.parametrize(
    "seam",
    (
        "existing_ref",
        "existing_commit",
        "existing_parents",
        "existing_ref_identity",
        "existing_commit_identity",
    ),
)
def test_malformed_existing_branch_shape_never_escapes_or_reuses(
    monkeypatch, seam
):
    result = _submit(
        FakeGitHub(ref_exists=True, malformed=seam), monkeypatch
    )

    assert result.state == "failed"
    assert result.pr_number == 0
    assert (
        "could not be verified" in result.message
        or "does not match" in result.message
        or "not exact" in result.message
    )


@pytest.mark.parametrize("seam", ("compare_head", "parent_commit_identity"))
def test_replay_binds_compare_head_and_parent_commit_identity(monkeypatch, seam):
    result = _submit(
        FakeGitHub(
            ref_exists=True,
            pr_exists=True,
            main_sha=ADVANCED_SHA,
            existing_parent_sha=BASE_SHA,
            malformed=seam,
            compare_ahead_by=251 if seam == "compare_head" else 1,
        ),
        monkeypatch,
    )

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "could not be verified" in result.message


def test_422_branch_and_pr_are_reused_only_after_exact_verification(monkeypatch):
    fake = FakeGitHub(
        ref_exists=True,
        pr_exists=True,
        preflight_ref_missing=True,
    )
    result = _submit(fake, monkeypatch)

    assert result.state == "pending_pr"
    assert result.commit_sha == EXISTING_SHA
    assert result.pr_number == 1234
    assert fake.branch_ref_reads == 2
    assert any(
        call[0] == "POST" and call[1].endswith("/git/refs")
        for call in fake.calls
    )
    # Existing branch verification pins parent/tree and all three exact files.
    assert any(
        call[0] == "GET" and call[1].endswith(f"/git/commits/{EXISTING_SHA}")
        for call in fake.calls
    )
    existing_reads = [
        call
        for call in fake.calls
        if call[0] == "GET" and f"ref={EXISTING_SHA}" in call[1]
    ]
    assert len(existing_reads) == 4
    assert any(call[0] == "GET" and "/pulls?" in call[1] for call in fake.calls)


def test_422_existing_branch_with_different_payload_is_a_hard_failure(monkeypatch):
    fake = FakeGitHub(ref_exists=True, existing_payload_matches=False)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert (
        "does not match" in result.message
        or "differs" in result.message
        or "outside the exact payload" in result.message
    )
    assert result.pr_number == 0
    assert not any(call[0] == "POST" and call[1].endswith("/pulls") for call in fake.calls)


def test_fresh_branch_is_read_back_before_pending_pr(monkeypatch):
    fake = FakeGitHub(malformed="blob_content_mismatch")
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "writeback branch could not be verified" in result.message
    assert not any(
        call[0] == "POST" and call[1].endswith("/pulls")
        for call in fake.calls
    )


@pytest.mark.parametrize("seam", ("existing_ref_read", "replay_blob"))
def test_replay_permission_failure_is_unavailable_with_scope_action(
    monkeypatch, seam
):
    result = _submit(
        FakeGitHub(ref_exists=True, failure=(seam, 403)),
        monkeypatch,
    )

    assert result.state == "unavailable"
    assert writeback.ENV_TOKEN in result.message
    assert "Contents read/write" in result.message
    assert result.pr_number == 0


def test_422_pr_without_one_exact_ready_candidate_is_not_pending(monkeypatch):
    fake = FakeGitHub(pr_exists=True, failure=("pr_list", 500))
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "could not be verified" in result.message
    assert "before retrying" in result.message
