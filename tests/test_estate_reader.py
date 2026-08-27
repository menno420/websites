from __future__ import annotations

import asyncio

import pytest

from app import estate_reader, github


ESTATE_SAMPLE = """\
# The estate — every repository, one line each

## Active — where work actually goes now

| repo | what it is · aliases | state (verified 2026-08-21) | read first (in the repo) | Layer 2 |
|---|---|---|---|---|
| `websites` | estate web surfaces: **control-plane** + botsite | **active** — keep-bot-only cutover landed | `docs/decisions.md` + `.sessions/` | [`repos/websites/`](repos/websites/README.md) |
| `substrate-kit` | the estate's method kit | **infrastructure** — v1.21.0 | `control/status.md` | [`repos/substrate-kit/`](repos/substrate-kit/README.md) |

## Paused / owner-gated — real assets, waiting on the owner

| repo | what it is · aliases | state (verified 2026-08-21) | read first (in the repo) | Layer 2 |
|---|---|---|---|---|
| `venture-lab` | the commerce lane | **paused by OD-11** | `docs/PROJECT-CLOSEOUT.md` | [`repos/venture-lab/`](repos/venture-lab/README.md) |

## Frozen experiments — retained as references

| repo | what it is · aliases | state (verified 2026-08-21) | read first (in the repo) | Layer 2 |
|---|---|---|---|---|
| `sim-lab` | mechanics laboratory | **frozen** — reference only | `README.md` | on demand |
"""


ACTIVITY_SAMPLE = """\
# The estate activity log — derived lane

> **Window:** last 7 days. **Generated:** 2026-08-26 21:24Z.

## In flight right now — cards on open PR branches

| repo | PR | venue | card |
|---|---|---|---|
| `fleet-manager` | [#951](https://github.com/menno420/fleet-manager/pull/951) | `cloud-container` | [2026-08-26-estate-execution-packets.md](https://github.com/menno420/fleet-manager/pull/951/files) |

## Sessions, newest first

| date | repo | venue | model | status | card |
|---|---|---|---|---|---|
| 2026-08-26 ⏳ | `fleet-manager` | `cloud-container` | fable-5 | `in-progress` | [execution packets](https://github.com/menno420/fleet-manager/pull/951/files) |
| 2026-08-25 | `websites` | `unstated` | GPT-5 | `complete` | [railway hardening](https://github.com/menno420/websites/blob/HEAD/.sessions/card.md) |

## Invisible work — repositories that moved without a card to explain it

| repo | last push | why it is here |
|---|---|---|
| `spider-bot` | 2026-08-25 | no `.sessions/` directory |
"""


def envelope(data, *, ok=True, status=200, error="", url="https://example.test"):
    return {
        "ok": ok,
        "status": status,
        "data": data,
        "error": error,
        "fetched_at": "12:00:00 UTC",
        "fetched_at_iso": "2026-08-27T12:00:00Z",
        "cached": False,
        "url": url,
    }


def test_parse_estate_preserves_current_table_shape_and_provenance():
    parsed = estate_reader.parse_estate(ESTATE_SAMPLE)

    assert [row.name for row in parsed.rows] == [
        "websites",
        "substrate-kit",
        "venture-lab",
        "sim-lab",
    ]
    websites = parsed.rows[0]
    assert websites.purpose == "estate web surfaces: **control-plane** + botsite"
    assert websites.purpose_text == "estate web surfaces: control-plane + botsite"
    assert websites.raw_state == "**active** — keep-bot-only cutover landed"
    assert websites.read_first == "`docs/decisions.md` + `.sessions/`"
    assert websites.layer2_path == "docs/repos/websites/README.md"
    assert websites.section == "Active — where work actually goes now"
    assert websites.verified_date == "2026-08-21"
    assert parsed.rows[-1].layer2_path is None
    assert parsed.warnings == ()


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        (
            "`docs/AGENT_ORIENTATION.md` → `docs/current-state.md`",
            ("docs/AGENT_ORIENTATION.md", "docs/current-state.md"),
        ),
        (
            "`docs/decisions.md` + `.sessions/`",
            ("docs/decisions.md",),
        ),
        (
            "`products/phone-controller/README.md`",
            ("products/phone-controller/README.md",),
        ),
    ],
)
def test_read_first_paths_follow_safe_file_routes_only(route, expected):
    assert estate_reader.read_first_paths(route) == expected


def test_member_probe_paths_put_routed_truth_first_without_duplicates():
    paths = estate_reader.member_probe_paths(
        "`docs/current-state.md` → `CLAUDE.md`"
    )
    assert paths[:2] == ("docs/current-state.md", "CLAUDE.md")
    assert paths.count("docs/current-state.md") == 1
    assert len(paths) <= estate_reader.MAX_MEMBER_PROBE_PATHS


def test_parse_estate_row_date_overrides_header_and_bad_row_degrades_alone():
    markdown = ESTATE_SAMPLE.replace(
        "**active** — keep-bot-only cutover landed",
        "**active** (verified 2026-08-24) — live",
    ).replace(
        "| `substrate-kit` | the estate's method kit | **infrastructure** — v1.21.0 | `control/status.md` | [`repos/substrate-kit/`](repos/substrate-kit/README.md) |",
        "| `substrate-kit` | missing cells | **infrastructure** |",
    )

    parsed = estate_reader.parse_estate(markdown)

    assert parsed.rows[0].verified_date == "2026-08-24"
    substrate = next(row for row in parsed.rows if row.name == "substrate-kit")
    assert substrate.read_first == ""
    assert substrate.layer2_path is None
    assert any("expected 5 cells, found 3" in warning for warning in substrate.warnings)
    # Other rows are retained intact instead of the malformed row blanking the index.
    assert any(row.name == "venture-lab" for row in parsed.rows)


def test_duplicate_and_contradictory_rows_are_preserved_and_warned():
    duplicate = """\
## Active
| repo | purpose | state (verified 2026-08-21) | read first | Layer 2 |
|---|---|---|---|---|
| `same-repo` | first purpose | active | `README.md` | on demand |
## Paused
| repo | purpose | state (verified 2026-08-22) | read first | Layer 2 |
|---|---|---|---|---|
| `same-repo` | changed purpose | paused | `docs/current-state.md` | on demand |
"""

    parsed = estate_reader.parse_estate(duplicate)

    assert len(parsed.rows) == 2
    assert any("duplicate repository 'same-repo'" in value for value in parsed.warnings)
    assert any(
        "contradictory repository 'same-repo'" in value for value in parsed.warnings
    )
    assert all(len(row.warnings) == 2 for row in parsed.rows)


def test_invalid_estate_identifier_is_not_exposed_as_a_fetchable_repo():
    malicious = ESTATE_SAMPLE.replace("`websites`", "`../private`", 1)

    parsed = estate_reader.parse_estate(malicious)

    assert "../private" not in {row.name for row in parsed.rows}
    assert any("invalid or missing repository identifier" in w for w in parsed.warnings)


def test_parse_activity_keeps_generated_inflight_sessions_and_invisible_work():
    parsed = estate_reader.parse_activity(ACTIVITY_SAMPLE)

    assert parsed.generated_at == "2026-08-26 21:24Z"
    assert len(parsed.in_flight) == 1
    assert parsed.in_flight[0].repo == "fleet-manager"
    assert parsed.in_flight[0].status == "in-progress"
    assert parsed.in_flight[0].related_url.endswith("/pull/951")
    assert [record.repo for record in parsed.sessions] == [
        "fleet-manager",
        "websites",
    ]
    assert parsed.sessions[0].date == "2026-08-26"
    assert parsed.sessions[1].source_url.endswith("/.sessions/card.md")
    assert parsed.invisible_work[0].repo == "spider-bot"
    assert parsed.invisible_work[0].status == "unexplained"
    assert parsed.invisible_work[0].detail == "no .sessions/ directory"
    assert parsed.invisible_work[0].source_url.endswith(
        "/fleet-manager/blob/main/docs/activity/estate-log.md"
    )


def test_overview_is_exactly_two_public_files_and_one_public_listing(
    monkeypatch,
):
    file_calls = []
    api_calls = []

    async def fake_file(repo, path, ref="main", refresh=False):
        file_calls.append((repo, path, ref, refresh))
        return envelope(ESTATE_SAMPLE if path.endswith("ESTATE.md") else ACTIVITY_SAMPLE)

    async def fake_api(path, refresh=False, *, coalesce=True):
        api_calls.append((path, refresh, coalesce))
        return envelope(
            [
                {
                    "name": "websites",
                    "description": "surfaces",
                    "html_url": "https://github.com/menno420/websites",
                    "private": False,
                    "visibility": "public",
                    "archived": False,
                    "disabled": False,
                    "pushed_at": "2026-08-27T08:00:00Z",
                    "updated_at": "2026-08-27T08:00:00Z",
                    "default_branch": "main",
                    "open_issues_count": 3,
                },
                {
                    "name": "new-public-repo",
                    "description": None,
                    "html_url": "https://github.com/menno420/new-public-repo",
                    "private": False,
                    "visibility": "public",
                    "archived": True,
                    "pushed_at": "2026-08-20T08:00:00Z",
                    "updated_at": "2026-08-20T08:00:00Z",
                    "default_branch": "main",
                },
            ]
        )

    monkeypatch.setattr(github, "fetch_public_file", fake_file, raising=False)
    monkeypatch.setattr(github, "public_api", fake_api, raising=False)

    sources = asyncio.run(
        estate_reader.read_overview_sources(
            refresh=True,
            coalesce_public_listing=False,
        )
    )

    assert file_calls == [
        ("fleet-manager", "docs/ESTATE.md", "main", True),
        ("fleet-manager", "docs/activity/estate-log.md", "main", True),
    ]
    assert len(api_calls) == 1
    assert api_calls[0][0].startswith("/users/menno420/repos?")
    assert api_calls[0][1:] == (True, False)
    assert [repo.name for repo in sources.unindexed_public_repositories] == [
        "new-public-repo"
    ]
    assert sources.unindexed_public_repositories[0].archived is True


def test_overview_preserves_partial_failures_and_suppresses_private_rows(
    monkeypatch,
):
    async def fake_file(repo, path, **_kwargs):
        if path == estate_reader.ESTATE_PATH:
            return envelope(ESTATE_SAMPLE)
        return envelope(None, ok=False, status=503, error="upstream unavailable")

    async def fake_api(_path, **_kwargs):
        return envelope(
            [
                {
                    "name": "secret-repo",
                    "private": True,
                    "visibility": "private",
                },
                "not a repository",
            ]
        )

    monkeypatch.setattr(github, "fetch_public_file", fake_file, raising=False)
    monkeypatch.setattr(github, "public_api", fake_api, raising=False)

    sources = asyncio.run(estate_reader.read_overview_sources())

    assert sources.activity_result["status"] == 503
    assert sources.estate.rows
    assert sources.activity.records == ()
    assert sources.public_repositories == ()
    assert any("activity log unavailable" in warning for warning in sources.warnings)
    assert any("private and was suppressed" in warning for warning in sources.warnings)


@pytest.mark.parametrize("name", ["../secret", ".hidden", "bad/name", "", "a" * 101])
def test_detail_rejects_unsafe_name_before_fetch(monkeypatch, name):
    calls = []

    async def fake_file(*args, **kwargs):
        calls.append((args, kwargs))
        return envelope("should not happen")

    monkeypatch.setattr(github, "fetch_public_file", fake_file, raising=False)

    with pytest.raises(ValueError, match="invalid repository identifier"):
        asyncio.run(estate_reader.read_detail_sources(name, True, None))
    assert calls == []


def test_private_detail_fetches_only_public_fleet_manager_layer2(monkeypatch):
    calls = []

    async def fake_file(repo, path, **_kwargs):
        calls.append((repo, path))
        return envelope("# public layer 2")

    monkeypatch.setattr(github, "fetch_public_file", fake_file, raising=False)

    sources = asyncio.run(
        estate_reader.read_detail_sources(
            "private-product",
            False,
            "docs/repos/private-product/README.md",
        )
    )

    assert calls == [
        ("fleet-manager", "docs/repos/private-product/README.md")
    ]
    assert sources.layer2_result["ok"] is True
    assert set(sources.member_results) == set(estate_reader.MEMBER_PROBE_PATHS)
    assert all(not result["ok"] for result in sources.member_results.values())
    assert all(
        "private or unavailable" in result["error"]
        for result in sources.member_results.values()
    )


def test_public_detail_is_selected_repo_only_and_concurrency_is_bounded(
    monkeypatch,
):
    calls = []
    active = 0
    peak = 0

    async def fake_file(repo, path, **kwargs):
        nonlocal active, peak
        calls.append((repo, path, kwargs.get("ref")))
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.005)
        active -= 1
        return envelope(f"# {repo}/{path}")

    monkeypatch.setattr(github, "fetch_public_file", fake_file, raising=False)

    sources = asyncio.run(
        estate_reader.read_detail_sources(
            "websites",
            True,
            "repos/websites/README.md",
            member_paths=("docs/decisions.md", "README.md"),
            member_ref="master",
        )
    )

    assert peak <= estate_reader.DETAIL_CONCURRENCY
    assert len(calls) == 3
    assert calls.count(
        ("fleet-manager", "docs/repos/websites/README.md", "main")
    ) == 1
    assert ("websites", "docs/decisions.md", "master") in calls
    assert ("websites", "README.md", "master") in calls
    assert all(repo in {"fleet-manager", "websites"} for repo, _path, _ref in calls)
    assert sources.member_results["README.md"]["ok"] is True


def test_normalize_layer2_refuses_other_repo_or_arbitrary_path():
    assert (
        estate_reader.normalize_layer2_path(
            "websites", "[entry](repos/websites/README.md)"
        )
        == "docs/repos/websites/README.md"
    )
    assert estate_reader.normalize_layer2_path("websites", "docs/ESTATE.md") is None
    assert (
        estate_reader.normalize_layer2_path(
            "websites", "docs/repos/private-product/README.md"
        )
        is None
    )


def test_prose_extractors_require_explicit_non_template_evidence():
    source = """\
# Product

## The one-paragraph answer

This is the **owner's review surface**. It stays server-rendered and honest.

## Current next thread

Ship the repository catalogue after the required checks pass.
"""
    assert estate_reader.extract_concise_situation(source) == (
        "This is the owner's review surface. It stays server-rendered and honest."
    )
    assert estate_reader.extract_explicit_next_thread(source) == (
        "Ship the repository catalogue after the required checks pass."
    )

    scattered = """\
# Product

The prose says next: maybe rewrite everything eventually.

### Thread: next feature — active

This is not an exact next-thread heading.
"""
    assert estate_reader.extract_explicit_next_thread(scattered) is None

    template = """\
# Current state

## Current situation

${CURRENT_SITUATION}

## Next action

TBD
"""
    assert estate_reader.is_placeholder_text(template)
    assert estate_reader.extract_concise_situation(template) == ""
    assert estate_reader.extract_explicit_next_thread(template) is None


def test_next_heading_must_be_exact_not_a_confident_sounding_variant():
    assert estate_reader.extract_explicit_next_thread(
        "## Next steps and roadmap\n\nDo everything."
    ) is None
    assert estate_reader.extract_explicit_next_thread(
        "## Next action:\n\n- Verify live state.\n- Then ship."
    ) == "Verify live state. Then ship."
