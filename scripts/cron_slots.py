#!/usr/bin/env python3
"""Cron-slot helper: compute a cron expression's next wall-clock fire slots.

──────────────────────────────────────────────────────────────────────────────
PROVENANCE / KILL-SWITCH HEADER
  Why:   Cron fields are wall-clock anchored (`17 */6 * * *` fires at 00:17,
         06:17, 12:17, 18:17 — NOT "+6h from when you looked"). This repo's
         record carried the same wrong hand-computed slot ("~02:17Z") across
         five heartbeats and timed a wake against it (CAPABILITIES append,
         2026-07-11). This helper makes slot math mechanical so heartbeats
         and plans stop inheriting arithmetic errors.
  Added: 2026-07-11 (continuous-mode wake; captured as the cron-slot-helper
         backlog idea the same night the error was found).
  Trust: DETERMINISTIC pure stdlib. Supports the 5-field subset the fleet
         actually writes: numbers, `*`, `*/N`, and comma lists per field
         (minute hour dom month dow). Ranges (a-b) also accepted. Anything
         it cannot parse is a loud error, never a guess.
  KILL-SWITCH: convenience helper — DELETE if unused; nothing depends on it.
──────────────────────────────────────────────────────────────────────────────

Usage:  python3 scripts/cron_slots.py "17 */6 * * *" [count]
Prints the next <count> (default 3) fire times in UTC.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

_FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]  # min hr dom mon dow


def _parse_field(spec: str, lo: int, hi: int) -> set[int]:
    """One cron field → the set of matching values. Loud on the unparseable."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if part == "*":
            out.update(range(lo, hi + 1))
        elif part.startswith("*/"):
            step = int(part[2:])
            if step <= 0:
                raise ValueError(f"bad step in {part!r}")
            out.update(range(lo, hi + 1, step))
        elif "-" in part:
            a, b = part.split("-", 1)
            a_i, b_i = int(a), int(b)
            if not (lo <= a_i <= b_i <= hi):
                raise ValueError(f"range {part!r} outside {lo}-{hi}")
            out.update(range(a_i, b_i + 1))
        else:
            v = int(part)
            if not (lo <= v <= hi):
                raise ValueError(f"value {part!r} outside {lo}-{hi}")
            out.add(v)
    return out


def parse_cron(expr: str) -> list[set[int]]:
    """A 5-field cron expression → per-field value sets. Loud on malformed."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError(f"expected 5 cron fields, got {len(fields)}: {expr!r}")
    return [
        _parse_field(f, lo, hi) for f, (lo, hi) in zip(fields, _FIELD_RANGES)
    ]


def _matches(dt: datetime, sets: list[set[int]]) -> bool:
    minute, hour, dom, month, dow = sets
    # cron dow: 0 = Sunday; Python weekday(): 0 = Monday.
    py_dow = (dt.weekday() + 1) % 7
    # Standard cron semantics: when BOTH dom and dow are restricted, either
    # may match; when only one is restricted, it must match. Both-star = any.
    dom_star = dom == set(range(1, 32))
    dow_star = dow == set(range(0, 7))
    if dom_star and dow_star:
        day_ok = True
    elif dom_star:
        day_ok = py_dow in dow
    elif dow_star:
        day_ok = dt.day in dom
    else:
        day_ok = dt.day in dom or py_dow in dow
    return (
        dt.minute in minute and dt.hour in hour
        and dt.month in month and day_ok
    )


def next_slots(
    expr: str, count: int = 3, now: datetime | None = None
) -> list[datetime]:
    """The next ``count`` UTC fire times STRICTLY AFTER ``now``.

    Minute-resolution walk bounded to 366 days — a valid fleet cron always
    fires well within that; hitting the bound raises rather than looping.
    """
    sets = parse_cron(expr)
    now = (now or datetime.now(timezone.utc)).replace(second=0, microsecond=0)
    cursor = now + timedelta(minutes=1)
    end = now + timedelta(days=366)
    out: list[datetime] = []
    while cursor <= end and len(out) < count:
        if _matches(cursor, sets):
            out.append(cursor)
        cursor += timedelta(minutes=1)
    if len(out) < count:
        raise ValueError(f"no fire slot within 366 days for {expr!r}")
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print('usage: cron_slots.py "<5-field cron>" [count]')
        return 1
    count = int(argv[2]) if len(argv) > 2 else 3
    try:
        slots = next_slots(argv[1], count)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    for s in slots:
        print(s.strftime("%Y-%m-%dT%H:%MZ"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
