"""Offline unit tests for the enriched machine-readable heartbeat fields
(D-0028, retro G3): the parsed ``orders:`` line (outstanding = acked minus
done) and the OPTIONAL ``routine:`` / ``landing:`` lines, their /fleet
surfacing (lane dict, attention sort, summary roll-ups), and the honest
degradation when a lane writes none of them.
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config, fleet, github  # noqa: E402

NOW = datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc)


# --------------------------------------------------------------------------- #
# parse_orders
# --------------------------------------------------------------------------- #


def test_parse_orders_ranges_and_outstanding():
    """`acked=001-008 done=001-006` -> outstanding 007,008 (padding kept)."""
    out = fleet.parse_orders("acked=001-008 done=001-006")
    assert out["ok"] is True
    assert out["acked"][0] == "001" and out["acked"][-1] == "008"
    assert out["outstanding"] == ["007", "008"]
    assert out["claimed"] is None


def test_parse_orders_comma_lists_and_all_done():
    out = fleet.parse_orders("acked=001,002,003 done=001,002,003")
    assert out["ok"] is True and out["outstanding"] == []


def test_parse_orders_claimed_by_captured_verbatim():
    out = fleet.parse_orders(
        "acked=001-008 done=001-006 claimed-by: 007+008 my-lane 2026-07-10T18:00Z"
    )
    assert out["outstanding"] == ["007", "008"]
    assert out["claimed"] == "007+008 my-lane 2026-07-10T18:00Z"


def test_parse_orders_free_text_is_honest_not_ok():
    """A free-text orders line parses to ok=False — never invented ids."""
    out = fleet.parse_orders("none yet — awaiting first order")
    assert out["ok"] is False and out["outstanding"] == []
    assert fleet.parse_orders("")["ok"] is False


def test_parse_orders_absurd_range_is_skipped():
    """A typo range (001-9999) is refused rather than expanded."""
    out = fleet.parse_orders("acked=001-9999 done=001")
    assert out["acked"] == []  # skipped, not guessed


# --------------------------------------------------------------------------- #
# classify_routine
# --------------------------------------------------------------------------- #


def test_routine_armed_fresh_is_not_silent():
    r = fleet.classify_routine(
        "ARMED — cron 0 */4 * * * · last-fired 2026-07-10T20:01Z", now=NOW
    )
    assert r["present"] and r["armed"] is True
    assert r["silent"] is False and r["no_fire_recorded"] is False
    assert r["cron"].startswith("0 */4")


def test_routine_armed_but_silently_dead_flags():
    """Armed with a last fire older than FLEET_STALE_HOURS = the failure mode
    the field exists for (armed but silently dead)."""
    r = fleet.classify_routine(
        "armed · cron 0 */4 * * * · last-fired 2026-07-08T00:00Z", now=NOW
    )
    assert r["armed"] is True and r["silent"] is True
    assert "ago" in r["fired_age_human"]


def test_routine_armed_no_fire_yet_is_unknown_not_silent():
    r = fleet.classify_routine("armed · cron 0 */4 * * *", now=NOW)
    assert r["armed"] is True and r["silent"] is False
    assert r["no_fire_recorded"] is True


def test_routine_prose_form_parses():
    """The real-world prose form (trigger id, list_triggers last_fired_at)."""
    r = fleet.classify_routine(
        "ARMED + first fire CONFIRMED — trigger trig_x, cron 0 */4 * * *, fresh "
        "session per fire; list_triggers last_fired_at 2026-07-10T20:01:32Z",
        now=NOW,
    )
    assert r["armed"] is True and r["silent"] is False


def test_routine_absent_or_none():
    assert fleet.classify_routine("", now=NOW)["present"] is False
    r = fleet.classify_routine("none", now=NOW)
    assert r["present"] is True and r["armed"] is False and r["silent"] is False


# --------------------------------------------------------------------------- #
# classify_landing
# --------------------------------------------------------------------------- #


def test_landing_kinds_and_attention():
    clean = fleet.classify_landing("all-merged")
    assert clean["kind"] == "clean" and clean["attention"] is False

    pushed = fleet.classify_landing("pushed-unmerged claude/some-branch")
    assert pushed["kind"] == "pushed" and pushed["attention"] is True
    assert pushed["branch"] == "claude/some-branch"

    local = fleet.classify_landing("LOCAL-ONLY claude/stranded-work")
    assert local["kind"] == "local" and local["attention"] is True
    assert local["branch"] == "claude/stranded-work"

    absent = fleet.classify_landing("")
    assert absent["present"] is False and absent["attention"] is False


# --------------------------------------------------------------------------- #
# lane_status + overview surfacing
# --------------------------------------------------------------------------- #

_ENRICHED_MD = (
    "# enriched-lane · status\n"
    "updated: 2026-07-10T20:30Z\n"
    "health: green (all suites passing)\n"
    "last-shipped: #64 — something\n"
    "blockers: none\n"
    "routine: armed · cron 0 */4 * * * · last-fired 2026-07-08T00:00Z\n"
    "landing: pushed-unmerged claude/needs-rescue\n"
    "deployed: abc1234 · verified 2026-07-10T20:15Z\n"
    "orders: acked=001-003 done=001,002\n"
)

_PLAIN_MD = (
    "# plain-lane · status\n"
    "updated: 2026-07-10T20:45Z\n"
    "health: green (fine)\n"
    "orders: routed via chat, nothing formal\n"
)


def _lane(repo="websites", lane="websites"):
    return {"lane": lane, "repo": repo, "status_path": "control/status.md",
            "model": "unknown", "note": ""}


def _fake_repo_api(**_ignored):
    async def fake(repo, subpath="", refresh=False):
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}
    return fake


def test_lane_status_surfaces_enriched_fields(monkeypatch):
    """An enriched heartbeat flows through: routine silent, landing attention,
    deployed passthrough, outstanding orders computed."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": True, "status": 200, "data": _ENRICHED_MD, "error": "",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", _fake_repo_api())
        return await fleet.lane_status(_lane(), now=NOW)

    out = asyncio.run(run())
    assert out["fields"]["routine"].startswith("armed")
    assert out["routine_info"]["silent"] is True  # fired >stale-threshold ago
    assert out["landing_info"]["kind"] == "pushed"
    assert out["landing_info"]["attention"] is True
    assert out["landing_info"]["branch"] == "claude/needs-rescue"
    assert out["fields"]["deployed"].startswith("abc1234")
    assert out["orders_info"]["outstanding"] == ["003"]
    # the enriched lines never leak into blockers as continuations
    assert "routine" not in out["fields"]["blockers"]


def test_lane_without_optional_fields_renders_as_before(monkeypatch):
    """A lane that writes none of the optional lines: no attention flags, no
    invented values — exactly the pre-enrichment behavior."""

    async def fake_fetch(repo, path, ref="main", refresh=False):
        return {"ok": True, "status": 200, "data": _PLAIN_MD, "error": "",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", _fake_repo_api())
        return await fleet.lane_status(_lane(repo="plain", lane="plain"), now=NOW)

    out = asyncio.run(run())
    assert out["routine_info"]["present"] is False
    assert out["landing_info"]["present"] is False
    assert out["landing_info"]["attention"] is False
    assert out["orders_info"]["ok"] is False  # free-text orders line
    assert "deployed" not in out["fields"]


def test_overview_sorts_stranded_landing_above_healthy_and_counts(monkeypatch):
    """A green lane with a stranded landing outranks a plain healthy lane, and
    the summary rolls up stranded / silent-routine / outstanding counts."""

    bodies = {
        "websites": _ENRICHED_MD,          # green but stranded + silent routine
        "substrate-kit": _PLAIN_MD,        # plain healthy
    }

    async def fake_fetch(repo, path, ref="main", refresh=False):
        if repo in bodies:
            return {"ok": True, "status": 200, "data": bodies[repo], "error": "",
                    "fetched_at": "", "cached": False, "url": ""}
        return {"ok": False, "status": 404, "data": None, "error": "nf",
                "fetched_at": "", "cached": False, "url": ""}

    async def run():
        monkeypatch.setattr(github, "fetch_file", fake_fetch)
        monkeypatch.setattr(github, "repo_api", _fake_repo_api())
        # Frozen `now`: with wall-clock time this test TIME-BOMBED on
        # 2026-07-11T08:45Z — the plain lane's fixed `updated:` stamp
        # crossed FLEET_STALE_HOURS, both lanes collapsed into the same
        # attention rank, and within-rank age ordering flipped the sort.
        return await fleet.overview(now=NOW)

    out = asyncio.run(run())
    lanes = out["lanes"]
    enriched_i = next(i for i, x in enumerate(lanes) if x["repo"] == "websites")
    plain_i = next(i for i, x in enumerate(lanes) if x["repo"] == "substrate-kit")
    assert enriched_i < plain_i  # attention-first: stranded work rises
    assert out["summary"]["stranded"] == 1
    assert out["summary"]["silent_routines"] == 1
    assert out["summary"]["outstanding_orders"] == 1
    assert out["summary"]["total"] == len(config.FLEET_LANES)
