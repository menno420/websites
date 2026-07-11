"""Injectable clock — the route-level half of the time discipline.

The #114 static guard (``tests/test_time_discipline.py``) covers DIRECT
test calls to age-measuring functions; this module covers the half the
scanner cannot see: TestClient route tests exercising the real wall clock
THROUGH the endpoints (/fleet, /orders, the board), where the 08:45Z
time-bomb class could reappear.

Production behavior is unchanged: ``NOW_OVERRIDE`` is ``None`` and
``now()`` returns the real wall clock. The test suite freezes a request's
entire rendering by monkeypatching ``clock.NOW_OVERRIDE`` to a fixed
instant — every age-measuring fallback in the app routes through here.

Rule for new code: an age-measuring function takes an injectable
``now: datetime | None = None`` parameter and falls back to
``clock.now()`` — never to ``datetime.now(timezone.utc)`` directly.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Test-only override. None in production (real wall clock). Tests set this
# via monkeypatch.setattr(clock, "NOW_OVERRIDE", <frozen aware datetime>).
NOW_OVERRIDE: datetime | None = None


def now() -> datetime:
    """The app's single wall-clock read (UTC, aware)."""
    return NOW_OVERRIDE or datetime.now(timezone.utc)
