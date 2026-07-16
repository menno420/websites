"""Storefront freshness nag (backlog idea, 2026-07-13).

``botsite/data/products.json`` is a hand-curated registry — each entry's
``as_of`` records when it was last re-verified against venture-lab. A
registry drifts silently the moment a product goes live or changes price;
the honesty doctrine (see ``botsite/products.py``'s module docstring) dies
through staleness, not lies. Two things are pinned here: the pure
``stale_products`` classifier (synthetic data, frozen ``now`` — the module
time-discipline convention) and a real nag against the COMMITTED registry
using the actual wall clock, so this test itself goes red the day a live
product's ``as_of`` ages past the horizon — the intended trigger for a
session to re-verify it against venture-lab and bump the date.
"""

from __future__ import annotations

from datetime import datetime, timezone

from botsite.products import STALE_HORIZON_DAYS, load_products, stale_products

FROZEN_NOW = datetime(2026, 7, 27, 0, 0, 0, tzinfo=timezone.utc)


def _product(slug: str, as_of: str) -> dict:
    return {
        "slug": slug,
        "name": slug,
        "tagline": "t",
        "description": "d",
        "price": "$0",
        "availability": "live",
        "url": None,
        "source": "s",
        "as_of": as_of,
    }


def test_fresh_entry_is_not_stale():
    # FROZEN_NOW - 13 days: inside the 14-day horizon.
    fresh = _product("fresh", "2026-07-14")
    assert stale_products([fresh], now=FROZEN_NOW) == []


def test_exactly_at_horizon_is_not_stale():
    # FROZEN_NOW - 14 days exactly: at the boundary, not past it.
    at_horizon = _product("at-horizon", "2026-07-13")
    assert stale_products([at_horizon], now=FROZEN_NOW) == []


def test_strictly_past_horizon_is_stale():
    # FROZEN_NOW - 15 days: one day past the boundary.
    stale = _product("stale", "2026-07-12")
    result = stale_products([stale], now=FROZEN_NOW)
    assert len(result) == 1
    assert result[0]["slug"] == "stale"
    assert result[0]["age_days"] == 15.0


def test_unparseable_as_of_is_skipped_not_crashed():
    bad = _product("bad-date", "not-a-date")
    empty = _product("empty-date", "")
    assert stale_products([bad, empty], now=FROZEN_NOW) == []


def test_custom_horizon_is_respected():
    p = _product("p", "2026-07-20")  # 7 days old at FROZEN_NOW
    assert stale_products([p], now=FROZEN_NOW, horizon_days=10) == []
    assert stale_products([p], now=FROZEN_NOW, horizon_days=5) != []


def test_results_sort_oldest_first():
    newer = _product("newer", "2026-07-10")  # 17 days old
    older = _product("older", "2026-07-01")  # 26 days old
    result = stale_products([newer, older], now=FROZEN_NOW)
    assert [p["slug"] for p in result] == ["older", "newer"]


def test_committed_registry_is_not_stale():
    """The real nag: fails naming which product(s) need re-verification.

    Uses the ACTUAL wall clock on purpose (not a frozen ``now``) — this is
    a drift pin, not a determinism test; it is SUPPOSED to go red as real
    time passes, the same way ``test_outbox_grammar_pin.py`` and
    ``test_fastlane_pin_map.py`` fire on real committed-state drift rather
    than synthetic fixtures.
    """
    products = load_products()
    stale = stale_products(products, now=datetime.now(timezone.utc))
    assert not stale, (
        f"{len(stale)} storefront product(s) have not been re-verified "
        f"against venture-lab in over {STALE_HORIZON_DAYS} days: "
        + ", ".join(
            f"{p['slug']} (as_of {p['as_of']}, {p['age_days']:.0f}d old)"
            for p in stale
        )
        + " — re-check price/availability/description against the source "
        "packet and bump as_of, or file the review as an owner ask if it "
        "can't be verified without them."
    )
