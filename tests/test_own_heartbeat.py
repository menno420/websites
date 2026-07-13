"""Own-heartbeat parse self-check (dogfood pair to the D-0028 enrichment).

This repo's ``control/status.md`` is a lane heartbeat that `/fleet`, `/queue`
and `/orders` all machine-read via ``app.fleet``'s parsers — and a malformed
heartbeat fails SILENTLY there (it renders wrong on the live fleet page with
no red anywhere; the pre-D-0028 ``routine:`` line leaked into ``blockers:``
for hours exactly this way). These tests run the REAL committed heartbeat
through the same parsers so a malformed one goes red at PR time.

Honest scope note: heartbeat-only PRs ride the ``control/**`` fast lane,
which skips the full pytest suite by design. Originally that meant a bad
heartbeat was caught only by the NEXT non-control PR (running just this
file in the fast lane was once rejected as a second logic path) — until
incident PR #307 merged exactly that way. Since ORDER 027 item 7, the fast
lane's grammar-pins gate (``.github/workflows/quality.yml``) runs THIS file
whenever a control-only diff touches ``control/status.md``, so a malformed
heartbeat now reddens its own PR; the full suite still runs it on every
non-control PR as the standing floor.

Assertions stick to the documented contract (``control/README.md`` § status
format): if a future format change breaks them, the heartbeat and the
parsers must move together — which is precisely the drift this file exists
to catch.
"""

import sys
from pathlib import Path

from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import fleet  # noqa: E402

_STATUS_PATH = Path(__file__).resolve().parents[1] / "control" / "status.md"


def _fields():
    parsed = fleet.parse_status(
        _STATUS_PATH.read_text(encoding="utf-8"), "websites"
    )
    return parsed


def test_heartbeat_file_exists_and_names_the_project():
    parsed = _fields()
    assert parsed["project"] == "websites"


def test_documented_required_fields_present_and_parse():
    fields = _fields()["fields"]
    for key in ("updated", "phase", "health", "orders"):
        assert fields.get(key), f"heartbeat is missing the `{key}:` line"

    # now= frozen per the time-discipline guard; only `ok` (parseability)
    # is asserted, so any instant works.
    fresh = fleet.freshness(
        fields["updated"], now=datetime(2026, 7, 11, 9, 0, tzinfo=timezone.utc)
    )
    assert fresh["ok"], (
        f"`updated:` does not parse as a timestamp: {fields['updated']!r} — "
        "the manager reads an unparseable heartbeat as a dark lane"
    )

    health = fleet.classify_health(fields["health"])
    assert health["kind"] != "unknown", (
        f"`health:` does not classify: {fields['health']!r} (must start "
        "green / red-by-design / broken)"
    )


def test_orders_line_is_machine_readable():
    fields = _fields()["fields"]
    info = fleet.parse_orders(fields["orders"])
    assert info["ok"], (
        f"`orders:` line is not machine-readable: {fields['orders']!r} — "
        "/orders and /fleet compute outstanding work from acked=/done="
    )
    assert info["acked"], "`orders:` parses but carries no acked ids"


def test_optional_enriched_lines_parse_when_present():
    fields = _fields()["fields"]

    if fields.get("routine"):
        r = fleet.classify_routine(fields["routine"])
        assert r["present"], "routine: line present but did not classify"
        # this lane's routine line documents an armed trigger; if that ever
        # changes the line should say so in a parseable way, not vanish into
        # prose the fleet page misreads.
        assert r["armed"] or "none" in fields["routine"].lower()

    if fields.get("landing"):
        l = fleet.classify_landing(fields["landing"])
        assert l["present"]
        assert l["kind"] != "unknown", (
            f"`landing:` does not classify: {fields['landing']!r} (use "
            "all-merged / pushed-unmerged <branch> / LOCAL-ONLY <branch>)"
        )


def test_enriched_keys_do_not_leak_into_blockers():
    """The pre-D-0028 failure class: an unrecognized `key:` line was folded
    into the previous field as a continuation — the live page showed
    `blockers: none routine: ARMED …` for hours."""
    fields = _fields()["fields"]
    blockers = fields.get("blockers", "")
    for needle in ("routine:", "landing:", "deployed:", "orders:"):
        assert needle not in blockers, (
            f"`{needle}` leaked into blockers as a continuation — a status "
            "key is missing from fleet.KNOWN_KEYS"
        )
