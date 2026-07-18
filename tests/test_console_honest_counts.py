"""C1 — honest counts on the /work, /history, /console category landing pages.

The template already renders a `None` count as an honest `—` and an int as the
number; the risk C1 closes is upstream, in the `_count_*` providers: four of
them (`queue`, `orders`, `ideas`, `activity`) trusted a source roll-up that a
fetch failure silently zeroes, so a failed count used to render as a misleading
`0` — indistinguishable from a genuine zero. These tests pin the distinction at
the provider boundary (mock the source envelope directly, no network):

  (a) a genuine 0 (source ok, truly zero) renders as `0`, never `—`;
  (b) a failed/errored source renders the honest `—`, never `0`;
  (c) a normal non-zero count is unchanged.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main  # noqa: E402


def _run(coro):
    # A fresh loop per call — robust when a sibling test in the full-suite run
    # has already closed the module-global loop (`get_event_loop` would then
    # hand back a closed one).
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# --- _count_queue ---------------------------------------------------------- #


def test_queue_genuine_zero_reports_a_real_zero(monkeypatch):
    async def fake(refresh):
        return {"summary": {"total": 0}, "unreadable_lanes": []}

    monkeypatch.setattr(main.owner_queue, "overview", fake)
    got = _run(main._count_queue(False))
    assert got == (0, "open", "ok")  # a real 0 — NOT the failed sentinel


def test_queue_unreadable_lane_reports_failed_not_zero(monkeypatch):
    async def fake(refresh):
        # A lane fetch failed -> total is an undercount (here it even reads 0).
        return {"summary": {"total": 0}, "unreadable_lanes": ["websites"]}

    monkeypatch.setattr(main.owner_queue, "overview", fake)
    assert _run(main._count_queue(False)) is None  # honest — , never a faked 0


def test_queue_nonzero_unchanged(monkeypatch):
    async def fake(refresh):
        return {"summary": {"total": 3}, "unreadable_lanes": []}

    monkeypatch.setattr(main.owner_queue, "overview", fake)
    assert _run(main._count_queue(False)) == (3, "open", "warn")


# --- _count_orders --------------------------------------------------------- #


def test_orders_genuine_zero_reports_a_real_zero(monkeypatch):
    async def fake(refresh, now=None):
        return {"summary": {"open": 0, "errored": 0}}

    monkeypatch.setattr(main.orders, "overview", fake)
    assert _run(main._count_orders(False)) == (0, "open", "ok")


def test_orders_errored_source_reports_failed_not_zero(monkeypatch):
    async def fake(refresh, now=None):
        # One repo's inbox fetch errored -> the open sum is an undercount.
        return {"summary": {"open": 0, "errored": 2}}

    monkeypatch.setattr(main.orders, "overview", fake)
    assert _run(main._count_orders(False)) is None


def test_orders_nonzero_unchanged(monkeypatch):
    async def fake(refresh, now=None):
        return {"summary": {"open": 5, "errored": 0}}

    monkeypatch.setattr(main.orders, "overview", fake)
    assert _run(main._count_orders(False)) == (5, "open", "warn")


# --- _count_ideas ---------------------------------------------------------- #


def test_ideas_genuine_zero_reports_a_real_zero(monkeypatch):
    async def fake(refresh):
        # An empty-but-readable fleet: repos present, no listing errors.
        return [{"total": 0, "state_counts": {}, "listing_error": None}]

    monkeypatch.setattr(main.ideas, "overview", fake)
    assert _run(main._count_ideas(False)) == (0, "ideas", "repo")


def test_ideas_listing_error_reports_failed_not_zero(monkeypatch):
    async def fake(refresh):
        return [{"total": 0, "state_counts": {}, "listing_error": "rate limited"}]

    monkeypatch.setattr(main.ideas, "overview", fake)
    assert _run(main._count_ideas(False)) is None


def test_ideas_nonzero_unchanged(monkeypatch):
    async def fake(refresh):
        return [{"total": 4, "state_counts": {"captured": 4}, "listing_error": None}]

    monkeypatch.setattr(main.ideas, "overview", fake)
    assert _run(main._count_ideas(False)) == (4, "ideas", "repo")


# --- _count_activity ------------------------------------------------------- #


def test_activity_genuine_zero_reports_a_real_zero(monkeypatch):
    async def fake(refresh):
        return {"items": [], "errors": []}

    monkeypatch.setattr(main.activity, "timeline", fake)
    assert _run(main._count_activity(False)) == (0, "recent PRs", "repo")


def test_activity_fetch_error_reports_failed_not_zero(monkeypatch):
    async def fake(refresh):
        # A per-repo PR fetch failed; items may be understated.
        return {"items": [], "errors": [{"repo": "websites", "error": "HTTP 500"}]}

    monkeypatch.setattr(main.activity, "timeline", fake)
    assert _run(main._count_activity(False)) is None


def test_activity_nonzero_unchanged(monkeypatch):
    async def fake(refresh):
        return {"items": [{"repo": "websites"}, {"repo": "superbot"}], "errors": []}

    monkeypatch.setattr(main.activity, "timeline", fake)
    assert _run(main._count_activity(False)) == (2, "recent PRs", "repo")


# --- end-to-end: the honest marker actually reaches the rendered page ------- #


def test_failed_and_zero_counts_render_distinctly_on_a_landing_page(monkeypatch):
    """A failed counter renders the honest `—` glyph; a genuine 0 renders `0`.
    Exercised through `_category_rows` so the provider→row honesty is proven
    end-to-end, not just at the helper boundary."""
    from app import nav

    async def failed(refresh):
        return None

    async def genuine_zero(refresh):
        return 0, "ideas", "repo"

    # queue fails (→ —), ideas is a genuine zero (→ 0). Other rows are chip-less
    # or covered above; stub the rest to a fixed value so the row build is
    # deterministic and network-free.
    async def some(refresh):
        return 7, "x", "repo"

    monkeypatch.setitem(main._COUNTERS, "queue", failed)
    monkeypatch.setitem(main._COUNTERS, "ideas", genuine_zero)
    for k in ("orders", "reviews"):
        monkeypatch.setitem(main._COUNTERS, k, some)

    cat = nav.category("work")
    rows = _run(main._category_rows(cat, False))
    by_key = {r["key"]: r for r in rows}
    # failed counter: count is the None sentinel (template → —), NOT 0
    assert by_key["queue"]["counted"] is True
    assert by_key["queue"]["count"] is None
    # genuine zero: an actual 0, distinct from the failed sentinel
    assert by_key["ideas"]["counted"] is True
    assert by_key["ideas"]["count"] == 0
