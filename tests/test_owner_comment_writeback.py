"""Fleet Manager owner-comment writeback contract, entirely network-free."""

from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from app import github, owner_comment_writeback as writeback


BASE_SHA = "a" * 40
BASE_TREE_SHA = "b" * 40
NEW_TREE_SHA = "c" * 40
COMMIT_SHA = "d" * 40
EXISTING_SHA = "e" * 40
PR_URL = "https://github.com/menno420/fleet-manager/pull/1234"
NOW = datetime(2026, 8, 27, 10, 11, 12, tzinfo=timezone.utc)
SUBMISSION_KEY = "20260827t101112z-0123456789abcdef0123456789abcdef"


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
        self.calls: list[tuple[str, str, Any, str]] = []
        self.blob_count = 0
        self.blob_payloads: dict[str, bytes] = {}
        self.files: dict[str, bytes] = {}
        self.branch = ""

    def _fail(self, seam: str) -> dict[str, Any] | None:
        if self.failure and self.failure[0] == seam:
            status = self.failure[1]
            return _envelope(status, None, f"{seam} failed")
        return None

    def _pr(self, commit_sha: str) -> dict[str, Any]:
        data = {
            "number": 1234,
            "html_url": PR_URL,
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
        assert token == "fleet-only-token"

        if method == "GET" and path.endswith("/git/ref/heads/main"):
            if self.malformed == "base_ref":
                return _envelope(200, {"object": "not-an-object"})
            return self._fail("base_ref") or _envelope(
                200, {"object": {"sha": BASE_SHA}}
            )
        if method == "GET" and path.endswith(f"/git/commits/{BASE_SHA}"):
            if self.malformed == "base_commit":
                return _envelope(200, {"tree": "not-an-object"})
            return self._fail("base_commit") or _envelope(
                200, {"tree": {"sha": BASE_TREE_SHA}}
            )
        if method == "GET" and "/contents/" in path:
            parsed = urlparse(path)
            ref = parse_qs(parsed.query).get("ref", [""])[0]
            file_path = parsed.path.split("/contents/", 1)[1]
            if ref == BASE_SHA:
                failed = self._fail(
                    "root_read" if file_path.endswith("index.json") else "readme_read"
                )
                if failed:
                    return failed
                return _contents(
                    self.root if file_path.endswith("index.json") else self.readme
                )
            if ref == EXISTING_SHA:
                payload = self.files.get(file_path, b"")
                if not self.existing_payload_matches and file_path.endswith("index.json"):
                    payload += b"different"
                return _contents(payload)
            raise AssertionError(f"unexpected contents ref {ref}")
        if method == "POST" and path.endswith("/git/blobs"):
            failed = self._fail("blob")
            if failed:
                return failed
            self.blob_count += 1
            sha = str(self.blob_count) * 40
            self.blob_payloads[sha] = base64.b64decode(json_body["content"])
            return _envelope(201, {"sha": sha})
        if method == "POST" and path.endswith("/git/trees"):
            failed = self._fail("tree")
            if failed:
                return failed
            assert json_body["base_tree"] == BASE_TREE_SHA
            self.files = {
                entry["path"]: self.blob_payloads[entry["sha"]]
                for entry in json_body["tree"]
            }
            return _envelope(201, {"sha": NEW_TREE_SHA})
        if method == "POST" and path.endswith("/git/commits"):
            failed = self._fail("commit")
            if failed:
                return failed
            return _envelope(201, {"sha": COMMIT_SHA})
        if method == "POST" and path.endswith("/git/refs"):
            self.branch = json_body["ref"].removeprefix("refs/heads/")
            failed = self._fail("ref")
            if failed:
                return failed
            if self.ref_exists:
                return _envelope(422, None, "Reference already exists")
            return _envelope(201, {"ref": json_body["ref"], "object": {"sha": COMMIT_SHA}})
        if (
            method == "GET"
            and "/git/ref/heads/claude/owner-comments-" in path
        ):
            if self.malformed == "existing_ref":
                return _envelope(200, {"object": "not-an-object"})
            return _envelope(200, {"object": {"sha": EXISTING_SHA}})
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
                    "tree": {
                        "sha": NEW_TREE_SHA if self.existing_payload_matches else "9" * 40
                    },
                    "parents": [{"sha": BASE_SHA}],
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
):
    monkeypatch.setattr(github, "api_request", fake.api_request)
    return asyncio.run(
        writeback.submit_owner_comment(
            repository,
            comment,
            context=context,
            submission_key=submission_key,
            now=NOW,
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


def test_atomic_three_file_commit_preserves_verbatim_text_and_opens_ready_pr(
    monkeypatch,
):
    fake = FakeGitHub()
    comment = "  Keep this wording.\nSecond line.  "
    result = _submit(fake, monkeypatch, comment=comment)

    assert result.state == "pending_pr"
    assert result.ok is True
    assert result.pr_number == 1234 and result.pr_url == PR_URL
    assert result.record_id.startswith("20260827t101112z-")
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

    # Exact pinned reads precede mutation, then three blobs feed one tree and
    # one commit. The only ref mutation is creation of a new branch.
    content_reads = [call for call in fake.calls if call[0] == "GET" and "/contents/" in call[1]]
    assert len(content_reads) == 2
    assert all(f"ref={BASE_SHA}" in call[1] for call in content_reads)
    blob_calls = [call for call in fake.calls if call[1].endswith("/git/blobs")]
    tree_calls = [call for call in fake.calls if call[1].endswith("/git/trees")]
    commit_calls = [
        call
        for call in fake.calls
        if call[1].endswith("/git/commits") and call[0] == "POST"
    ]
    ref_calls = [call for call in fake.calls if call[1].endswith("/git/refs")]
    assert len(blob_calls) == 3
    assert len(tree_calls) == len(commit_calls) == len(ref_calls) == 1
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
        submission_key=(
            "20260827t101112z-fedcba9876543210fedcba9876543210"
        ),
    )

    assert replay.state == "pending_pr"
    assert replay.record_id == first.record_id
    assert replay.branch == first.branch
    assert replay.created_at == first.created_at
    assert distinct.record_id != first.record_id


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
    assert "unchanged form" in result.message


def test_success_response_with_unverified_pr_is_not_pending(monkeypatch):
    fake = FakeGitHub(malformed_pr=True)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "could not be verified" in result.message
    assert result.commit_sha == COMMIT_SHA
    assert result.pr_number == 0


@pytest.mark.parametrize("seam", ("base_ref", "base_commit"))
def test_malformed_base_nested_shape_is_an_honest_failure(monkeypatch, seam):
    result = _submit(FakeGitHub(malformed=seam), monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "could not resolve" in result.message


@pytest.mark.parametrize(
    "seam", ("existing_ref", "existing_commit", "existing_parents")
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
    )


def test_422_branch_and_pr_are_reused_only_after_exact_verification(monkeypatch):
    fake = FakeGitHub(ref_exists=True, pr_exists=True)
    result = _submit(fake, monkeypatch)

    assert result.state == "pending_pr"
    assert result.commit_sha == EXISTING_SHA
    assert result.pr_number == 1234
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
    assert len(existing_reads) == 3
    assert any(call[0] == "GET" and "/pulls?" in call[1] for call in fake.calls)


def test_422_existing_branch_with_different_payload_is_a_hard_failure(monkeypatch):
    fake = FakeGitHub(ref_exists=True, existing_payload_matches=False)
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert "does not match" in result.message or "differs" in result.message
    assert result.pr_number == 0
    assert not any(call[0] == "POST" and call[1].endswith("/pulls") for call in fake.calls)


def test_422_pr_without_one_exact_ready_candidate_is_not_pending(monkeypatch):
    fake = FakeGitHub(pr_exists=True, failure=("pr_list", 500))
    result = _submit(fake, monkeypatch)

    assert result.state == "failed"
    assert result.pr_number == 0
    assert "could not be verified" in result.message
    assert "before retrying" in result.message
