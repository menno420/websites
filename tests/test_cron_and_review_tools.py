"""Offline unit tests for the slice-14 tooling: cron_slots (wall-clock slot
math — the five-wrong-heartbeats lesson made mechanical) and
review_row_check (the fleet review-queue's binding 50-line rule).
"""

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, _ROOT / "scripts" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cron_slots = _load("cron_slots")
review_row_check = _load("review_row_check")


# --------------------------------------------------------------------------- #
# cron_slots
# --------------------------------------------------------------------------- #


def test_next_slots_wall_clock_anchored_the_incident_case():
    """The exact incident: `17 */6 * * *` after 2026-07-10T21:03Z fires at
    00:17Z next day — NOT '+6h from merge' (~03:03) and NOT 02:17."""
    now = datetime(2026, 7, 10, 21, 3, tzinfo=timezone.utc)
    slots = cron_slots.next_slots("17 */6 * * *", count=3, now=now)
    assert [s.strftime("%dT%H:%M") for s in slots] == [
        "11T00:17", "11T06:17", "11T12:17"
    ]


def test_next_slots_hourly_and_lists_and_ranges():
    now = datetime(2026, 7, 11, 3, 40, tzinfo=timezone.utc)
    hourly = cron_slots.next_slots("0 * * * *", count=2, now=now)
    assert [s.strftime("%H:%M") for s in hourly] == ["04:00", "05:00"]
    listed = cron_slots.next_slots("0 4,16 * * *", count=2, now=now)
    assert [s.strftime("%H:%M") for s in listed] == ["04:00", "16:00"]
    ranged = cron_slots.next_slots("30 8-10 * * *", count=3, now=now)
    assert [s.strftime("%H:%M") for s in ranged] == ["08:30", "09:30", "10:30"]


def test_next_slots_strictly_after_now():
    """A slot AT now must not count — the next fire is the future one."""
    now = datetime(2026, 7, 11, 0, 17, tzinfo=timezone.utc)
    slots = cron_slots.next_slots("17 */6 * * *", count=1, now=now)
    assert slots[0].strftime("%H:%M") == "06:17"


def test_parse_cron_loud_on_malformed_never_guesses():
    import pytest

    with pytest.raises(ValueError):
        cron_slots.parse_cron("17 */6 * *")  # 4 fields
    with pytest.raises(ValueError):
        cron_slots.parse_cron("61 * * * *")  # minute out of range
    with pytest.raises(ValueError):
        cron_slots.parse_cron("*/0 * * * *")  # zero step


# --------------------------------------------------------------------------- #
# review_row_check
# --------------------------------------------------------------------------- #


def test_is_runtime_path_matches_the_ledger_exclusions():
    f = review_row_check.is_runtime_path
    assert f("app/fleet.py") is True
    assert f("scripts/open_work.py") is True
    assert f("app/templates/fleet.html") is True
    assert f("docs/site.md") is False
    assert f("control/status.md") is False
    assert f(".sessions/2026-07-11-card.md") is False
    assert f("tests/test_fleet.py") is False
    assert f("botsite/tests/test_botsite.py") is False
    assert f("README.md") is False  # markdown = documentation


def test_runtime_lines_sums_and_skips_binary():
    numstat = (
        "120\t30\tapp/fleet.py\n"
        "10\t2\ttests/test_fleet.py\n"     # excluded: tests
        "40\t0\tdocs/site.md\n"            # excluded: docs
        "-\t-\tassets/logo.png\n"          # binary: counts 0, never guessed
        "5\t5\tapp/templates/fleet.html\n"
    )
    total, counted = review_row_check.runtime_lines(numstat)
    assert total == 160
    assert sorted(p for _, p in counted) == [
        "app/fleet.py", "app/templates/fleet.html", "assets/logo.png"
    ]
    assert dict((p, n) for n, p in counted)["assets/logo.png"] == 0


def test_threshold_semantics():
    assert review_row_check.THRESHOLD == 50  # the ledger's binding number
