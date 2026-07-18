"""C9 — adversarial pagination-truncation coverage for the open-PR cap.

``readiness.repo_readiness`` fetches open PRs with a hard ``per_page=100`` and
no pagination walk, so a repo with MORE than 100 open PRs silently truncates to
the first 100. The board / owner page's only honest signal that this happened is
``prs.capped`` (``len(open_prs) == 100``), rendered as the "(capped)" marker
beside the open count. Nothing exercised that flag, so the cap was silent — a
regression that dropped or inverted it would ship green.

These tests pin the flag at the boundary: exactly 100 open PRs sets ``capped``;
under 100 leaves it clear; a non-list (degraded) payload never fabricates a cap.
Network-free: ``github.repo_api`` is mocked so only the ``/pulls`` envelope
carries data and every other cell degrades honestly (the readiness path tolerates
that, exactly as the live board does).
"""

from __future__ import annotations

import asyncio

from app import github, readiness


def _envelope(data, *, ok=True, status=200):
    return {
        "ok": ok,
        "status": status,
        "data": data,
        "error": "" if ok else "nf",
        "fetched_at": "",
        "cached": False,
        "url": "",
    }


def _open_prs(n: int) -> list[dict]:
    """``n`` minimal open-PR objects, oldest first (as the fetch sorts them)."""
    return [
        {
            "number": i,
            "title": f"PR {i}",
            "created_at": f"2026-07-{(i % 28) + 1:02d}T00:00:00Z",
            "html_url": f"https://github.com/menno420/superbot/pull/{i}",
        }
        for i in range(1, n + 1)
    ]


def _readiness_with_pulls(pulls_envelope: dict) -> dict:
    """Drive ``repo_readiness`` for a non-``websites`` repo (no deploy board),
    with only the ``/pulls`` envelope populated."""

    async def fake_repo_api(repo, subpath="", refresh=False):
        if subpath.startswith("/pulls"):
            return pulls_envelope
        return _envelope(None, ok=False, status=404)

    async def run():
        orig = github.repo_api
        github.repo_api = fake_repo_api
        try:
            return await readiness.repo_readiness("superbot")
        finally:
            github.repo_api = orig

    return asyncio.run(run())


def test_exactly_100_open_prs_sets_the_capped_flag():
    row = _readiness_with_pulls(_envelope(_open_prs(100)))
    assert row["prs"]["open_count"] == 100
    assert row["prs"]["capped"] is True
    # the oldest (first) PR is still surfaced — truncation keeps the head
    assert row["prs"]["oldest"]["number"] == 1


def test_under_100_open_prs_leaves_the_flag_clear():
    row = _readiness_with_pulls(_envelope(_open_prs(99)))
    assert row["prs"]["open_count"] == 99
    assert row["prs"]["capped"] is False


def test_zero_open_prs_is_not_a_cap():
    row = _readiness_with_pulls(_envelope([]))
    assert row["prs"]["open_count"] == 0
    assert row["prs"]["capped"] is False
    assert row["prs"]["oldest"] is None


def test_degraded_non_list_payload_never_fabricates_a_cap():
    # a failed /pulls fetch degrades to zero open PRs — never a phantom cap
    row = _readiness_with_pulls(_envelope(None, ok=False, status=502))
    assert row["prs"]["open_count"] == 0
    assert row["prs"]["capped"] is False
    # an ok-but-wrong-shape (non-list) body is treated the same way
    row2 = _readiness_with_pulls(_envelope({"message": "not a list"}))
    assert row2["prs"]["open_count"] == 0
    assert row2["prs"]["capped"] is False
