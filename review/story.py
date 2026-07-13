"""Domain layer for the review service — data loading, chart geometry, content.

Layering (the repo's binding architecture): routes (``app.py``) import this
module; this module imports nothing from routes or templates. There is no
client layer — the service is deliberately network-free: its one data source
is the committed ``data/snapshot.json`` baked from the real repo at build time
(see ``gen_snapshot.py`` for why runtime reads are impossible under Railway's
Root Directory deploy model).

Two kinds of content live here:

- **Generated numbers** — loaded from the snapshot, gracefully absent when the
  file is missing/corrupt (pages render an honest banner, never invented data).
- **Curated narrative** — the process/successes/problems record, written from
  the repo's own committed evidence (retro docs, session cards, capability
  ledger, decision ledger) with a citation on every claim. Curation here means
  selection and plain-English explanation for an outside reviewer, not spin:
  the problems list leads and is as specific as the successes list.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import listfilter

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = BASE_DIR / "data" / "snapshot.json"

REPO_URL = "https://github.com/menno420/websites"


def pr(num: int) -> str:
    """Deep link to a PR on the websites repo."""
    return f"{REPO_URL}/pull/{num}"


def blob(path: str) -> str:
    """Deep link to a file on the websites repo at main."""
    return f"{REPO_URL}/blob/main/{path}"


# ---------------------------------------------------------------------------
# Snapshot loading — honest degradation, never invented numbers.
# ---------------------------------------------------------------------------
def load_snapshot(path: Path | None = None) -> dict[str, Any]:
    """Load the committed snapshot. Returns ``{ok, error, data}``; a missing or
    corrupt file yields ``ok=False`` and empty data — pages banner honestly.

    ``path`` defaults to the module-level ``SNAPSHOT_PATH`` at CALL time (not
    definition time) so tests can monkeypatch the attribute."""
    if path is None:
        path = SNAPSHOT_PATH
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "error": "snapshot file missing (data/snapshot.json)", "data": {}}
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"snapshot unreadable: {exc}", "data": {}}
    if not isinstance(data, dict) or "days" not in data or "totals" not in data:
        return {"ok": False, "error": "snapshot malformed (missing days/totals)", "data": {}}
    return {"ok": True, "error": "", "data": data}


# ---------------------------------------------------------------------------
# Chart geometry — computed server-side so templates stay dumb.
# Mark specs per the program dataviz rules: columns <= 24px wide, 4px rounded
# data-end at the top, square at the baseline, single-hue magnitude encoding
# (color comes from the ds token --sb-chart-mark), text in ink tokens.
# ---------------------------------------------------------------------------
def column_chart(
    points: list[tuple[str, int]],
    *,
    height: int = 180,
    col_width: int = 24,
    gap: int = 56,
    pad_top: int = 26,
    pad_bottom: int = 24,
) -> dict[str, Any]:
    """Geometry for a small single-series column chart (one bar per day).

    Returns a dict of ready-to-render SVG coordinates. Pure and deterministic:
    unit-tested directly. Empty input -> ``{"empty": True}``.
    """
    if not points:
        return {"empty": True, "columns": [], "width": 0, "height": height}
    max_v = max(v for _, v in points) or 1
    plot_h = height - pad_top - pad_bottom
    columns = []
    for i, (label, value) in enumerate(points):
        h = round(plot_h * value / max_v) if value > 0 else 0
        x = gap // 2 + i * (col_width + gap)
        y = pad_top + (plot_h - h)
        columns.append(
            {
                "label": label,
                "value": value,
                "x": x,
                "y": y,
                "w": col_width,
                "h": h,
                "cx": x + col_width / 2,
                "baseline": pad_top + plot_h,
            }
        )
    width = gap // 2 + len(points) * (col_width + gap)
    return {
        "empty": False,
        "columns": columns,
        "width": width,
        "height": height,
        "baseline": pad_top + plot_h,
        "max": max_v,
    }


def growth_charts(snapshot_data: dict[str, Any]) -> list[dict[str, Any]]:
    """The three growth charts, from the snapshot's per-day rows."""
    days = snapshot_data.get("days") or []

    def series(key: str) -> list[tuple[str, int]]:
        return [
            (d.get("date", "?")[5:], int(d.get(key, 0) or 0))
            for d in days
            if isinstance(d, dict)
        ]

    charts = [
        {
            "id": "prs",
            "title": "Pull requests merged per day",
            "note": "Unique PR numbers referenced by merge commits on main, grouped by UTC merge date.",
            "chart": column_chart(series("prs_merged")),
        },
        {
            "id": "sessions",
            "title": "Agent session cards per day",
            "note": "Committed .sessions/ cards by filename date — one card per working session, required by CI.",
            "chart": column_chart(series("session_cards")),
        },
        {
            "id": "tests",
            "title": "Test functions at end of day",
            "note": "def test_ count across all services' suites at each day's last commit — the safety net's growth curve.",
            "chart": column_chart(series("test_functions_eod")),
        },
    ]
    return charts


# ---------------------------------------------------------------------------
# Curated narrative — every claim cites committed evidence.
# ---------------------------------------------------------------------------

# Who's who, for an outside reader.
GLOSSARY: list[tuple[str, str]] = [
    ("Owner", "The one human. He designs and directs by conversation; he cannot code. Every line of code here was written by Claude agents and cross-checked by other agents."),
    ("Lane / Project", "One Claude Project bound to one repo (or one area of a shared repo). This repo — websites — is one seat of a fleet that peaked at ~15 Projects and was consolidated to 8 standing seats (decided 2026-07-11, canonicalized 2026-07-12 — see the Fleet page)."),
    ("Manager / fleet-manager", "A coordinating lane (repo menno420/fleet-manager) that dispatches orders to every lane and aggregates their reports."),
    ("The bus", "Committed git files as the only inter-agent channel. Sessions cannot talk to each other; control/inbox.md (orders in) and control/status.md (heartbeat out) are the entire protocol."),
    ("Order", "A numbered instruction block the manager appends to control/inbox.md — priority, what to do, why, and a checkable done-when."),
    ("Heartbeat", "control/status.md, overwritten by each session as its deliberate last step: phase, health, last shipped PR, blockers, orders acked/done, asks for the owner."),
    ("Session card", "A per-session log in .sessions/, committed born-red (status: in-progress) as the session's first commit and flipped complete as its last — CI blocks the merge until it flips."),
    ("Born-red", "The designed state where a PR's first CI run fails on purpose: the in-progress session card holds the merge until the close-out is written. A red first run is the gate working."),
    ("Work ladder", "What a session does when it wakes, in priority order: inbox orders, then queued work, then the ideas backlog, then contained self-initiated improvements, then honest upkeep."),
    ("Continuous mode", "A session chain that schedules its own next wake (a timer message ~every 30 minutes), landing one full-ceremony slice per wake — 26 slices plus 3 rescues in one 17-hour run."),
    ("Substrate kit", "A vendored workflow engine (bootstrap.py) that enforces the ceremony: doc hygiene, session-card markers, the born-red gate, heartbeat grammar. Upgraded release-by-release like any dependency."),
    ("Quality gate", "The one required CI check on main. Runs the kit checker plus every service's test suite; control-file-only diffs ride a validated fast lane."),
]

# The landing path — one shippable unit of work, start to finish.
LANDING_PATH: list[tuple[str, str]] = [
    ("Wake", "A session starts — routine-fired on a 4-hour cron, chained by a self-scheduled timer, or opened by the owner. First act: git pull, read control/inbox.md at HEAD."),
    ("Claim", "Before building, the session claims the work on main (a claimed-by line in its own heartbeat, or a claim file) so parallel sessions don't execute the same order twice — a failure that actually happened and produced this rule."),
    ("Card, born-red", "First commit on the branch: a session card with status in-progress. CI now refuses to merge this PR — visible, on-purpose red until the work is done and written up."),
    ("Build + verify", "The work itself, plus proof: the full multi-service pytest suite and the kit's strict checker must pass locally before push."),
    ("READY PR", "A real pull request into main. The required quality check runs the whole ceremony: kit gate, session-card gate, safety guards, every service's tests."),
    ("Flip + merge", "The card flips to complete (with the real PR number) as the last code step; CI goes green; squash-merge. Main is always deployable because merge IS the deploy."),
    ("Deploy + prove", "Railway auto-deploys main. The session verifies live: every service's /version endpoint must equal the new main HEAD (a script polls until converged). 'Pushed' or 'deployed' is never recorded without proof."),
    ("Heartbeat", "Final step: overwrite control/status.md — what shipped, health, what's next, anything only the owner can do. The next session, and the manager, read the state from the repo, not from memory."),
]

SERVICES: list[dict[str, str]] = [
    {
        "name": "control-plane",
        "dir": "app/",
        "url": "https://control-plane-production-abb0.up.railway.app",
        "desc": "The fleet's mission control: readiness board, per-lane heartbeat view (/fleet), orders (/orders), owner to-do queue (/queue), cross-repo activity — all live from the GitHub API.",
    },
    {
        "name": "botsite",
        "dir": "botsite/",
        "url": "https://botsite-production-cfd7.up.railway.app",
        "desc": "Public marketing/reference site for the owner's Discord bot, rendering the bot repo's committed site.json.",
    },
    {
        "name": "dashboard",
        "dir": "dashboard/",
        "url": "https://dashboard-production-a91b.up.railway.app",
        "desc": "Read-only developer dashboard over the bot's committed inventory feeds; its live-bot write panel is a deliberate, labeled stub.",
    },
    {
        "name": "review",
        "dir": "review/",
        "url": "https://review-production-f027.up.railway.app",
        "desc": "This site — the program explaining itself to an outside reviewer, from its own committed record.",
    },
]

# Problems — honest, specific, evidenced. This list leads the site's story:
# a review surface that hides failures is worthless (the ORDER 011 retro's
# own framing). Each entry: what happened, what it cost, what changed.
# Entries may carry an optional ``details`` list ({heading, text, evidence})
# for incidents too big for one paragraph.

# The 2026-07-12 scheduler incident's commit-pinned sources (fleet-wide, so
# the evidence lives in the fleet's public repos, not this one). Every URL
# below was verified resolving before commit.
_SB = "https://github.com/menno420/superbot/blob"
_NIGHT_REVIEW_0712 = f"{_SB}/8558179e6a90670ed18c778234d789c65c2b5789/docs/eap/night-review-2026-07-12.md"
_EMAIL2_DRAFT = f"{_SB}/8558179e6a90670ed18c778234d789c65c2b5789/docs/eap/anthropic-email-2-draft-2026-07-11.md"
_FIGS_0712 = f"{_SB}/cbb549539c64e0ce3b4fea268e27b7ac49eeaf08/docs/eap/screenshots-2026-07-12/index.md"
_ROSTER_GEN13 = "https://github.com/menno420/fleet-manager/blob/10fc4f7a95c3ca2be96eac7017dbb2fdb3e6a172/docs/roster.md"
_SWEEP_8SEAT = "https://github.com/menno420/fleet-manager/blob/4111da44ae218bb37442ad958d740b782b1c859a/docs/research/2026-07-12-staleness-sweep-8seat.md"

PROBLEMS: list[dict[str, Any]] = [
    {
        "id": "incident-2026-07-12",
        "title": "2026-07-12: the platform's trigger scheduler silently degraded — the fleet's dead-man failsafes brought it back",
        "what": (
            "Between ~02:30Z and ~08:00Z on 2026-07-12, the scheduler behind the fleet's "
            "self-wake triggers degraded platform-side: due firings were dropped or frozen "
            "with no error, no retry, and no state change — a stalled trigger looks identical "
            "to a healthy one on every surface. The night review's verdict, from its own live "
            "trigger-registry reads: the batch was armed correctly; nothing agent-side changed "
            "versus the previous night, which — per the same registry evidence reported in "
            "that review — had run 84 of 85 one-shot wakes clean."
        ),
        "cost": (
            "Roughly five and a half hours of degraded unattended operation; two seats went "
            "fully dark (one failsafe itself wedged, one seat had no failsafe layer); a daily "
            "loop recovered ~2.7 hours late by manual re-fire. The detection gap is the real "
            "cost: a dropped tick stays 'enabled' with its fire time in the past — nothing "
            "alerts on it, and a queued tick and a lost tick look identical."
        ),
        "fix": (
            "The dead-man doctrine held and is now production-proven: every seat whose "
            "2-hourly failsafe cron stayed healthy self-revived the moment the scheduler "
            "breathed again, so the standing rule — never run a self-wake chain without a "
            "dead-man cron, and keep failsafe coverage itself alive — is written into fleet "
            "doctrine. Cross-substrate redundancy also held (the roster regen, moved earlier "
            "to a GitHub Actions cron, kept flowing through the outage). The incident record "
            "and its asks went to Anthropic as finding 7 of the July 12 email."
        ),
        "details": [
            {
                "heading": "Three self-wake mechanisms — all three failed differently, silently",
                "text": (
                    "A fleet can wake itself three ways today: one-shot send_later self-messages "
                    "(the fleet's ~15-minute pacemaker chains), cron routines bound to a persistent "
                    "session (the 2-hourly dead-man failsafes), and fresh-session-per-fire routines "
                    "(daily loops). On this night all three failed in different ways, each without "
                    "an error surface."
                ),
                "evidence": [("email finding 7 (verbatim)", _EMAIL2_DRAFT), ("night review §1", _NIGHT_REVIEW_0712)],
            },
            {
                "heading": "The three silent failure modes",
                "text": (
                    "(1) Nine due one-shots were never delivered (06:12 through 08:23Z, across five "
                    "seat sessions) — each stayed 'enabled' with its fire time in the past. "
                    "(2) Two crons wedged with next_run_at frozen hours in the past while still "
                    "enabled: a seat failsafe stuck at 06:06Z and a daily loop at 06:08Z showing "
                    "'last fire: never'. (3) The fresh-session daily fire was dropped entirely and "
                    "was recovered ~2.7 hours late by a manual re-fire at 08:46Z. Detection "
                    "signature, per the review: enabled=true AND next_run_at < now−15min — nothing "
                    "alerts on it today; the dropped ticks were visible in the trigger list all night."
                ),
                "evidence": [("night review §1 + §4.1 (timeline, signature)", _NIGHT_REVIEW_0712), ("figs 22/24/25 (the dropped routine, a lane's first-person account)", _FIGS_0712)],
            },
            {
                "heading": "The dead-man-cron failsafe worked — where it was alive",
                "text": (
                    "Every seat whose 2-hourly failsafe cron stayed healthy came back on its own at "
                    "~08:0xZ when the scheduler partially recovered. The two dark seats were exactly "
                    "the ones whose failsafe coverage was missing (daily-only) or itself wedged — the "
                    "doctrine takeaway, verbatim: 'a failsafe only protects while it is alive.' The "
                    "frozen crons are visible in the machine roster generated mid-incident."
                ),
                "evidence": [("night review §3.1 (Q-0265, production-proven)", _NIGHT_REVIEW_0712), ("roster gen #13 (frozen wake-state column)", _ROSTER_GEN13), ("8-seat staleness sweep, run mid-window", _SWEEP_8SEAT)],
            },
            {
                "heading": "Serialization vs. real drop — the same-day refinement",
                "text": (
                    "A seat working from the trigger registry split the 'dropped one-shot' class in "
                    "two: ticks bound to a busy session serialize and deliver the moment the turn "
                    "goes idle (its 09:10Z tick fired at 11:16Z at exactly that boundary — sound by "
                    "construction), while the genuinely-failed remainder is the fresh-session loop "
                    "and the frozen crons. The refinement makes the incident smaller and sharper — "
                    "and the platform gap clearer: no surface distinguishes queued from lost."
                ),
                "evidence": [("night review §8 (addendum ~12:00Z)", _NIGHT_REVIEW_0712), ("fig 35 (the serialization diagnosis)", _FIGS_0712)],
            },
            {
                "heading": "Duplicate-fire safety held: a verified zero-write stand-down",
                "text": (
                    "When the manual 08:46Z kick and the scheduler's late ~10:28Z catch-up "
                    "double-fired the same daily loop, the second run verified the first's commits "
                    "and stood down with zero writes — the duplicate-fire safety an at-least-once "
                    "delivery model needs already works on the fleet's side."
                ),
                "evidence": [("night review §8", _NIGHT_REVIEW_0712), ("fig 34 (the clean stand-down)", _FIGS_0712)],
            },
        ],
        "evidence": [
            ("the incident record: superbot night-review-2026-07-12 @ 8558179", _NIGHT_REVIEW_0712),
            ("finding 7 of the July 12 email (same commit)", _EMAIL2_DRAFT),
            ("the curated figure set (figs 20–35) @ cbb5495", _FIGS_0712),
            ("fleet-manager roster gen #13, generated mid-incident @ 10fc4f7", _ROSTER_GEN13),
        ],
    },
    {
        "title": "A gate that was supposed to block merges let an empty PR through",
        "what": "The session-card gate is meant to hold every PR red until its card flips complete. On day one, PR #19 auto-merged effectively EMPTY on its in-progress card alone — the checker never inspected the card's status value, and the card was picked by file mtime, which a fresh CI checkout flattens.",
        "cost": "One meaningless merge on main; more importantly, proof the safety ceremony was decorative until tested.",
        "fix": "Root-caused same day; fixed by adopting the upstream kit v1.0.0 engine plus a diff-aware card-selection step in CI, proven in both directions and pinned by a regression test.",
        "evidence": [("PR #24 (the fix)", pr(24)), ("tests/test_born_red_session_gate.py", blob("tests/test_born_red_session_gate.py"))],
    },
    {
        "title": "A session recorded work as pushed that never left its container",
        "what": "A routine-fired session's git push silently failed (its per-session GitHub grant was never provisioned), yet its own session card recorded the branch as pushed. Hours later the remote had no such branch.",
        "cost": "Stranded work, a misleading record, and a rescue: another lane re-landed the commits from a format-patch (PR #59).",
        "fix": "A standing rule in the capability ledger — NEVER record 'pushed' without proof (push exit 0 AND git ls-remote showing the commit) — plus a landing: line in every heartbeat so stranded work flags on the fleet page instead of hiding.",
        "evidence": [("PR #59 (the rescue)", pr(59)), ("docs/CAPABILITIES.md (the wall, verbatim errors)", blob("docs/CAPABILITIES.md"))],
    },
    {
        "title": "Scheduled wakes are unreliable — one fire stranded its work, one left no trace",
        "what": "The lane's self-armed 4-hourly wake routine fired sessions that lack PR tooling: the 04:03Z fire did real work but could not open a PR (heartbeat rescued verbatim as PR #98); the ~08:00Z fire left no trace at all. GitHub Actions cron is similarly best-effort — a fresh schedule's first fire arrived ~3.4 hours late.",
        "cost": "Silent coverage gaps in unattended operation; the send_later timer chain became the only consistent producer.",
        "fix": "A relay doctrine (any session may land another session's green, control-only work verbatim), attention-first flagging of armed-but-silent routines on /fleet, and a recorded rule: cron timing is ±hours, never gate anything on a slot.",
        "evidence": [("PR #98 (heartbeat rescue)", pr(98)), ("control/README.md (relay doctrine)", blob("control/README.md")), ("docs/retro/self-review-2026-07-11.md", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "The same cron-arithmetic mistake, repeated five times in writing",
        "what": "Five consecutive heartbeats stated a 17 */6 cron's next slot as '~02:17Z'. Cron anchors to wall-clock hours (00/06/12/18) — the real slot was 06:17Z. Self-caught on the sixth write.",
        "cost": "Five wrong statements in the committed record before anyone noticed; harmless this time, but the failure class (confidently restating an unchecked derivation) is not.",
        "fix": "A cron-slot calculator script with the exact incident pinned as a test, plus a capability-ledger lesson: compute slots from the epoch, never from 'now'.",
        "evidence": [("PR #96 (scripts/cron_slots.py)", pr(96)), ("docs/retro/self-review-2026-07-11.md § 1", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Tests with time bombs: a green suite that would have gone red on its own",
        "what": "At 08:45Z a test began failing on an UNTOUCHED tree — its fixed fixture timestamps crossed a staleness threshold against the real wall clock. A guard written the same day found 17 more latent time bombs across 5 test files.",
        "cost": "One live detonation; without the class-wide sweep, every later PR would have gone mystery-red one bomb at a time — poison for unattended runs.",
        "fix": "Injectable clocks (now=) on every age-measuring function, all 17 sites threaded with frozen constants, and an AST-scanning guard test that fails any future age-measuring call without a frozen clock.",
        "evidence": [("PR #111 (defusal)", pr(111)), ("PR #114 (class-wide guard)", pr(114)), ("tests/test_time_discipline.py", blob("tests/test_time_discipline.py"))],
    },
    {
        "title": "The status ledger drifted 17 slices out of date — in the repo that renders drift for a living",
        "what": "docs/current-state.md, the orientation file every session reads second, went stale across 17 rapid slices and carried four claims that were no longer true (wrong kit version, 'the PAT is set', a superseded registry mechanism, an exhausted work pointer).",
        "cost": "Every booting session oriented on partly false state until a dedicated truth sweep fixed it.",
        "fix": "The sweep itself (each correction verified against main HEAD and annotated in place), and 'truth sweep' now exists as a named upkeep rung sessions run when unrouted.",
        "evidence": [("PR #111 (truth sweep)", pr(111)), ("docs/current-state.md", blob("docs/current-state.md"))],
    },
    {
        "title": "Overclaims caught at the door — the review culture working, barely",
        "what": "A session card claimed 'pytest tests/ -> 235 passed' when 235 was the FULL multi-service suite (tests/ alone was 177). Another card pre-wrote its PR number and guessed wrong when a sibling took it. An order-claim matcher matched order id '00' inside a timestamp string.",
        "cost": "Nearly-shipped wrong statements; each was caught pre-merge by this program's own checks and habits, not by luck — but each got as far as a written claim.",
        "fix": "Cards now state both suite numbers; PRs are opened before their number is written anywhere; the matcher was rewritten against tokenized ids with the boundary case pinned as a test.",
        "evidence": [("PR #109 close-out", pr(109)), ("PR #77 (matcher fix)", pr(77)), ("docs/retro/self-review-2026-07-11.md § 1", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Real walls: things agents here verifiably cannot do",
        "what": "Direct api.github.com calls are proxy-blocked (GitHub goes through MCP tools, scoped per session). Branch deletion 403s on every path. Some session kinds cannot open PRs at all. Creating Railway resources is policy-forbidden without the owner's explicit go. The deployed board runs tokenless on GitHub's anonymous 60-requests/hour ceiling until the owner mints a PAT.",
        "cost": "Stale branches accumulate until a human deletes them; routine-fired sessions need rescue landings; two owner asks have been open for days on the owner's scarcest resource — his attention.",
        "fix": "Every wall lives in docs/CAPABILITIES.md with its exact error text and workaround, under a discovery rule: check the ledger, check the environment, attempt once and capture the error, append the finding — so no session re-pays a known wall.",
        "evidence": [("docs/CAPABILITIES.md", blob("docs/CAPABILITIES.md")), ("docs/owner/OWNER-ACTIONS.md", blob("docs/owner/OWNER-ACTIONS.md"))],
    },
]

# Successes — same discipline: specific, evidenced.
SUCCESSES: list[dict[str, Any]] = [
    {
        "title": "Three public services shipped and deployed in the repo's first day",
        "what": "From an empty repo at dawn to three live Railway services by evening: the control-plane board, the bot marketing site, and the developer dashboard — 45 PR merges on the first UTC day, each through the full branch → card → PR → CI → squash-merge ceremony (3 more PRs closed unmerged, casualties of early parallel-checkout churn the retro documents).",
        "evidence": [("PR #2 (control-plane)", pr(2)), ("PR #7 (botsite)", pr(7)), ("PR #8 (dashboard)", pr(8)), ("gen-1 final retro", blob("docs/retro/gen1-final-retro-2026-07-09.md"))],
    },
    {
        "title": "The system catches its own failures",
        "what": "The board's deploy-drift cell (built as ORDER 001) immediately exposed that the dashboard service was silently serving a stale build — its deploy trigger had never existed. Later, a scheduled healthcheck's very second run caught an upstream registry migration that had broken the fleet page to zero lanes, and the same wake shipped the repoint. Both were found by surfaces this program built to watch itself.",
        "evidence": [("PR #26 (drift cell)", pr(26)), ("PR #29 (trigger root-cause)", pr(29)), ("PR #102 (registry repoint)", pr(102))],
    },
    {
        "title": "An unattended 17-hour chain landed 26 slices and 3 rescues",
        "what": "A continuous-mode session chain — each wake self-scheduling the next — ran overnight and through the morning landing one verified slice per wake: seven new fleet-visibility pages, JSON shape contracts, board chips, nav hardening, five kit upgrades, and three rescues of other sessions' stranded work. The owner slept; the record shows every step.",
        "evidence": [("heartbeat at slice 26", blob("control/status.md")), ("self-review of the window", blob("docs/retro/self-review-2026-07-11.md"))],
    },
    {
        "title": "Gates got harder faster than work got faster",
        "what": "The safety net grew from 0 to 226 test functions in the repo's first three days (and keeps growing — the current count is on the Growth page, from the snapshot), and the gates themselves became test subjects: the born-red gate has a both-directions regression test, the CI fast lane's control gates are driven end-to-end against the real checker CLI, JSON payloads are pinned by shape contracts, and a meta-guard AST-scans the test suite for time discipline.",
        "evidence": [("tests/test_born_red_session_gate.py", blob("tests/test_born_red_session_gate.py")), ("PR #127 (gate suite tests)", pr(127)), ("PR #114 (time-discipline guard)", pr(114))],
    },
    {
        "title": "Sessions learned to arm their own clocks",
        "what": "Told that routine creation might be possible, a worker session self-armed the lane's 4-hourly wake trigger, confirmed the first fire from inside the fired session, and withdrew the fallback ask to the owner — an owner-click saved by an agent verifying its own capability instead of assuming a wall.",
        "evidence": [("ORDER 008 record", blob("control/inbox.md")), ("docs/CAPABILITIES.md append log", blob("docs/CAPABILITIES.md"))],
    },
    {
        "title": "Honesty is enforced, not aspirational",
        "what": "Every degraded state renders as itself: an unset token shows 'unknown (needs token)', a missing feed shows a banner, a stub is badged as a stub, secret names are masked to a count on the public board. Tests assert the absence of faked data. The fleet's own retro doctrine: a review that hides failures is worthless — the ORDER 011 self-review leads with five mistakes, each cited.",
        "evidence": [("ORDER 011 self-review", blob("docs/retro/self-review-2026-07-11.md")), ("PR #12 (secrets masked to a count)", pr(12))],
    },
    {
        "title": "Knowledge survives session death",
        "what": "Sessions are amnesiac — everything durable lives in the repo: a capability ledger with exact error texts, a decision ledger, an ideas backlog with dedup discipline, succession docs that booted generation 2 from main alone, and session cards for all 72 sessions. The gen-1 retro's strongest finding: the orientation chain reconstructed the whole project without any chat history.",
        "evidence": [("docs/CAPABILITIES.md", blob("docs/CAPABILITIES.md")), ("succession pack", blob("docs/succession/next-boot-2026-07-09.md")), (".sessions/", f"{REPO_URL}/tree/main/.sessions")],
    },
]

# Growth timeline — the milestone spine under the charts.
MILESTONES: list[dict[str, str]] = [
    {"date": "2026-07-09 am", "title": "Repo born; workflow engine adopted; control-plane built", "detail": "Intent commit, substrate-kit adoption (PR #1), the readiness board + journal browser (PR #2), deployed to a fresh Railway project (PR #3)."},
    {"date": "2026-07-09 pm", "title": "Botsite + dashboard rebuilt and deployed; sites made public", "detail": "Two more services through the same ceremony (PRs #7, #8); auth dropped on the owner's word with secret names masked to a count (PR #12); the gated /owner overlay (PR #14)."},
    {"date": "2026-07-09 late", "title": "The gate leak found and fixed; fleet coordination adopted", "detail": "PR #19's empty merge exposed the born-red leak, fixed via kit v1.0.0 (PR #24); the control/ bus adopted; /fleet renders every lane's heartbeat (PR #35). Gen-1 winds down after its 46-PR day (43 merged, 3 closed superseded) leaving succession docs a fresh generation can boot from."},
    {"date": "2026-07-10", "title": "Gen-2 boots from main alone; sessions arm their own wakes", "detail": "Walking skeleton proves the landing path (PR #51); /queue + /environments ship (PR #53); ORDER 008 self-arms the 4-hourly routine; the stranded-push incident and its rescue (PR #59) produce the proof-of-push rule; continuous mode begins (~PR #64)."},
    {"date": "2026-07-11", "title": "The 26-slice chain: fleet visibility wave + hardening", "detail": "/orders, /reviews, /projects, JSON contracts, board chips, nav guard; the healthcheck cron catches the registry break (fixed, PR #102); the time-bomb class defused (PRs #111/#114); fast-lane control gates (PR #125/#127); kit upgraded five versions; ORDER 011 self-review lands."},
    {"date": "2026-07-11/12", "title": "Fleet consolidation; the scheduler incident; this site goes live", "detail": "Fleet-wide: the owner consolidates a fleet that peaked at ~15 Projects to 8 standing seats (decided 07-11, canonicalized in the manager's registry 07-12T03:15Z), and the platform's trigger scheduler silently degrades overnight — the incident and the failsafe doctrine that recovered it lead the problems page. This review site deploys publicly (2026-07-12, per the fleet's record) and the second review email goes to Anthropic."},
]

# Overview stat tiles (labels only — values come from the snapshot).
STAT_TILES: list[tuple[str, str, str]] = [
    ("prs_merged", "pull requests merged", "each through the full CI ceremony"),
    ("session_cards", "agent sessions on record", "one committed card per session"),
    ("test_functions", "test functions", "grown from zero, all green at HEAD"),
    ("services", "live services in this repo", "independently deployed from one main"),
]


# ---------------------------------------------------------------------------
# Homepage (ORDER 017 C) — the 30-second front door. Every NUMBER on the
# homepage comes from the committed data files (snapshot + fleet mirror),
# never a template literal; the curated narrative below carries its
# commit-pinned evidence like every other narrative block in this module.
# ---------------------------------------------------------------------------

# The 2026-07-11 figure set (the model-mismatch screenshots live here).
_FIGS_0711 = f"{_SB}/e3eb0eb2bf3683794dd0d8c40bbf3988832c31ea/docs/eap/screenshots-2026-07-11/index.md"

# "Start here" — the five findings a busy reviewer should read first, one
# line each. Phrasing follows the sent July 12 email (commit-pinned below);
# the first link on each card is the deep link, the rest are evidence.
START_HERE: list[dict[str, Any]] = [
    {
        "id": "merge-permission",
        "title": "The merge-permission root cause was partly ours",
        "text": (
            "Three sessions were denied merging a PR metadata-identical to ten "
            "agent-merged ones around it. The email's diagnosis: the classifier was "
            "tracking the session, not the PR — and the fleet's own shared "
            "instructions coached every seat to trip it. One instruction fix "
            "propagated to all lanes."
        ),
        "links": [
            ("the finding, commit-pinned (July 12 email)", _EMAIL2_DRAFT),
            ("how merges are gated here", "/questionnaire#gates"),
        ],
    },
    {
        "id": "model-mismatch",
        "title": "The Routine said Opus 4.8; the session said Sonnet 5",
        "text": (
            "A Routine configured for one model woke a session that reported "
            "running another — config Opus 4.8, session self-reporting Sonnet 5. "
            "With the recorded 07-12 fairness update: newly created Routines now "
            "display the running model correctly."
        ),
        "links": [
            ("the finding (July 12 email)", _EMAIL2_DRAFT),
            ("figs 15a–15c, commit-pinned", _FIGS_0711),
        ],
    },
    {
        "id": "two-vantage",
        "title": "One tool call, two truths",
        "text": (
            "In auto mode, the identical tool call can raise a Deny/Allow prompt "
            "on the operator's screen while returning a clean success to the agent "
            "— the two-vantage permission split, and why 'nothing tells a session "
            "what it is allowed to do except trying and reading the refusal'."
        ),
        "links": [
            ("the finding (July 12 email)", _EMAIL2_DRAFT),
        ],
    },
    {
        "id": "scheduler-incident",
        "title": "2026-07-12: the scheduler degraded; the failsafes held",
        "text": (
            "The platform's trigger scheduler silently dropped and froze self-wake "
            "firings for roughly five and a half hours — no error, no retry. Every "
            "seat whose dead-man cron stayed alive self-revived; the full incident "
            "record leads the Problems page."
        ),
        "links": [
            ("the incident on this site", "/problems#incident-2026-07-12"),
            ("the incident record, commit-pinned", _NIGHT_REVIEW_0712),
        ],
    },
    {
        "id": "earned-trust",
        "title": "What earned trust: shared memory + durable state",
        "text": (
            "The standouts, per the email: shared memory across the fleet's repos "
            "('the cold-start tax is gone') and durable state that outlives any "
            "session — any single agent is replaceable because the record lives in "
            "git, not in a chat."
        ),
        "links": [
            ("how knowledge survives, on this site", "/questionnaire#memory"),
            ("the 'what earned trust' section (July 12 email)", _EMAIL2_DRAFT),
        ],
    },
]

# Generations — the program's own committed narrative (the July 12 email @
# 8558179 tells the arc: gen-1's one-day scale test → gen-2's overnight
# relaunch → gen-3, the standing program). A TEXT tile, deliberately: there
# is no machine-counted generations metric in the data files, so the tile
# renders the era's name rather than inventing a number.
GENERATIONS_TILE: dict[str, Any] = {
    "key": "generations",
    "value": "gen-3",
    "label": "generation now running",
    "sub": "1-day scale test → overnight relaunch → the standing program",
}


def homepage_stats(
    snapshot_data: dict[str, Any], fleet_data: dict[str, Any]
) -> list[dict[str, Any]]:
    """The homepage key-stats row: the snapshot tiles (``overview_stats``),
    a seats tile counted from the committed fleet mirror (peak from its own
    ``consolidation`` block — never a template literal), and the generations
    text tile. Missing data means a missing tile, never a guessed one."""
    tiles = overview_stats(snapshot_data)
    seats = (fleet_data or {}).get("seats") or []
    if seats:
        peak = ((fleet_data or {}).get("consolidation") or {}).get("peak") or ""
        tiles.append(
            {
                "key": "seats",
                "value": len(seats),
                "label": "standing fleet seats",
                "sub": (
                    f"peaked {peak} Projects → {len(seats)} standing"
                    if peak
                    else "from the committed fleet mirror"
                ),
            }
        )
    tiles.append(dict(GENERATIONS_TILE))
    return tiles


def site_map(seats_count: int | None = None) -> list[tuple[str, str, str]]:
    """The "how this site is organized" map — one honest line per section.
    The fleet line carries the seat count only when the committed mirror
    actually provides one."""
    fleet_line = (
        f"the {seats_count} standing seats, their heartbeats, and the consolidation story"
        if seats_count
        else "the standing seats, their heartbeats, and the consolidation story"
    )
    return [
        ("Overview", "/", "the story in brief — this page"),
        ("Process", "/process", "how the human + agent workflow works, wake to verified deploy"),
        ("Growth", "/growth", "the metrics over time, derived from git history"),
        ("Fleet", "/fleet", fleet_line),
        ("Reviews", "/reviews", "dated review editions, subscribable as an Atom feed"),
        ("Q&A", "/questionnaire", "evidence-backed answers — plus the live AI assistant on /ask"),
        ("Successes", "/successes", "what went right, each win linked to commits"),
        ("Problems", "/problems", "what failed and what it cost — including the 07-12 incident"),
    ]


# The homepage's "evidence itself" links — the same entry points the sent
# email names, at stable public locations.
EVIDENCE_LINKS: list[tuple[str, str]] = [
    ("the fleet's review record: superbot docs/eap", "https://github.com/menno420/superbot/tree/main/docs/eap"),
    ("this repo — every PR, card, and gate", REPO_URL),
]


# ---------------------------------------------------------------------------
# Interaction — read-only by design. "Room to interact" is a prefilled
# GitHub new-issue link (no form, no database, no credential): a reviewer's
# question becomes an issue, the manager routes it as an order on the bus,
# and the answer publishes in the next review edition + the /questions
# ledger. A real intake form/DB is a flagged future owner option.
# ---------------------------------------------------------------------------
def ask_url(topic: str) -> str:
    """A prefilled new-issue link — the site's one interaction affordance."""
    from urllib.parse import urlencode

    title = f"[program-review] Question: {topic}".strip()
    body = (
        f"**Asked from the program-review site — page/section: {topic}**\n\n"
        "<!-- Write your question below. It will be routed to the fleet as an "
        "order; the evidence-backed answer publishes in the next review "
        "edition and on the /questions ledger. -->\n\n"
    )
    return f"{REPO_URL}/issues/new?{urlencode({'title': title, 'body': body})}"


def load_questions(path: Path | None = None) -> dict[str, Any]:
    """The questions-asked → answered ledger (committed ``data/questions.json``).

    Honest degradation like every loader here: a missing/corrupt/malformed
    file yields ``ok=False`` and the page explains the intake convention
    over an empty ledger — never a fabricated Q&A history.
    """
    if path is None:
        path = BASE_DIR / "data" / "questions.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"ok": False, "error": "questions ledger missing (data/questions.json)", "data": {}}
    except (json.JSONDecodeError, OSError) as exc:
        return {"ok": False, "error": f"questions ledger unreadable: {exc}", "data": {}}
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        return {"ok": False, "error": "questions ledger malformed (missing questions list)", "data": {}}
    return {"ok": True, "error": "", "data": data}


# ---------------------------------------------------------------------------
# The questionnaire — anticipated reviewer questions, answered from the
# repo's committed evidence. No live model endpoint: the "AI" here is that
# agent sessions author these answers and keep them current (each landing
# through the same PR ceremony as code). Every answer cites its evidence.
# ---------------------------------------------------------------------------
QUESTIONNAIRE: list[dict[str, Any]] = [
    {
        "id": "runaway",
        "q": "How do you prevent runaway agents?",
        "a": "Three layers, all inspectable. (1) Structural: the deployed services are read-only toward everything they touch — no service holds a credential that can mutate anything beyond a cache refresh, and the genuinely powerful levers (Railway account actions, live-bot control, databases) are deliberately unwired; several are labeled stubs. (2) Enforced: CI carries an enforcing guard that fails any tracked code reading the ambient production-bot Railway IDs, and repo policy forbids agent-initiated Railway mutations without the owner's explicit go — a policy wall agents have honored rather than tested (the pending service creations are queued as owner clicks, not attempted). (3) Ceremonial: every change lands through a branch → session card → PR → required CI gate → squash-merge path, so there is no write path that skips review by the gates. Sessions that CAN'T complete that path (some scheduled wakes lack PR tooling) strand harmlessly and get relayed by sessions that can.",
        "evidence": [
            ("docs/RAILWAY-SAFETY.md", blob("docs/RAILWAY-SAFETY.md")),
            ("scripts/check_no_ambient_railway_ids.py (CI guard)", blob("scripts/check_no_ambient_railway_ids.py")),
            ("docs/owner/OWNER-ACTIONS.md (walls honored, queued as clicks)", blob("docs/owner/OWNER-ACTIONS.md")),
        ],
    },
    {
        "id": "failures",
        "q": "What has actually failed?",
        "a": "Plenty, and it is all written down: a merge gate that let an empty PR through on day one, a session that recorded work as pushed which never left its container, scheduled wakes that fired without PR tooling or not at all, a test suite carrying 18 latent time bombs, the status ledger drifting stale in the repo that renders drift for a living, and the same cron mistake written five times. The problems page on this site gives each one its cost and its fix; the retro documents go deeper. The honest pattern worth reviewing: most failures were caught by machinery this program built to watch itself (a drift cell, a scheduled healthcheck, a guard test), not by a human noticing.",
        "evidence": [
            ("/problems (this site)", "/problems"),
            ("ORDER 011 self-review", blob("docs/retro/self-review-2026-07-11.md")),
            ("gen-1 final retro", blob("docs/retro/gen1-final-retro-2026-07-09.md")),
        ],
    },
    {
        "id": "gates",
        "q": "How do the gates work — what actually stops a bad merge?",
        "a": "One required status check on main, called quality, runs on every PR: a workflow-kit checker (doc hygiene, session-card grammar, decision-ledger integrity), a session gate that holds any PR red while its committed session card still says in-progress (born-red by design — the red first run IS the gate working), the Railway-ID safety guard, and every service's full pytest suite. The gate is itself a test subject: when it leaked on day one (PR #19 merged effectively empty), the leak was root-caused, fixed, and pinned with a regression test that proves both directions. Control-file-only diffs (heartbeats) ride a validated fast lane that still enforces their own grammar and append-only rules.",
        "evidence": [
            (".github/workflows/quality.yml", blob(".github/workflows/quality.yml")),
            ("tests/test_born_red_session_gate.py", blob("tests/test_born_red_session_gate.py")),
            ("PR #19 (the leak) and PR #24 (the fix)", pr(24)),
        ],
    },
    {
        "id": "human-role",
        "q": "What does the human actually do, versus the agents?",
        "a": "The owner designs, directs, decides, and clicks. He cannot code — every line in this repo was written by Claude agent sessions and cross-checked by other sessions. His verbatim instructions appear in the record (\"Yes drop the auth\"; the directive that created this site). Decisions only he can make are queued in one skimmable file with click-level instructions (create this Railway service, mint this token, delete these branches — agents get 403 on branch deletion and say so). The working agreement describes his style honestly: decide-and-flag beats stop-and-ask for anything reversible, and agents are expected to reason a partial idea forward rather than wait.",
        "evidence": [
            ("docs/owner/OWNER-ACTIONS.md", blob("docs/owner/OWNER-ACTIONS.md")),
            (".claude/CLAUDE.md (the working agreement)", blob(".claude/CLAUDE.md")),
            ("docs/current-state.md (owner-verbatim directives in the ledger)", blob("docs/current-state.md")),
        ],
    },
    {
        "id": "unattended",
        "q": "How do unattended wakes stay safe?",
        "a": "The same landing path applies whether a human is watching or not — there is no unattended shortcut. A woken session reads its orders from a committed inbox, claims work on main before building (so parallel sessions can't double-execute), works up a written ladder (orders, then queued work, then backlog, then contained reversible improvements, then honest upkeep), and can only ship through the required gate. What unattended operation adds is fallibility, and the record treats that as a first-class fact: wakes that stranded work or left no trace are documented, a relay doctrine lets healthy sessions land a stranded session's green work verbatim, and the fleet page badges armed-but-silent routines so a dead clock is visible instead of quiet. The 17-hour overnight chain that landed 26 verified slices is the existence proof; its failures are listed right next to it.",
        "evidence": [
            ("control/README.md (bus protocol + relay doctrine)", blob("control/README.md")),
            ("/process (this site — the landing path)", "/process"),
            ("ORDER 011 self-review (the unattended window audited)", blob("docs/retro/self-review-2026-07-11.md")),
        ],
    },
    {
        "id": "coordination",
        "q": "How do agents coordinate without talking to each other?",
        "a": "Committed git files are the entire inter-agent channel — sessions cannot message each other, so the protocol is files with one writer each: orders arrive in control/inbox.md (only the manager writes it; CI enforces append-only), state goes out in control/status.md (overwritten by each session as its deliberate last step), and claims are lines on main. This is slower than an API and that is the point: every coordination act is versioned, attributable, and reviewable after the fact. The control-plane service renders the whole bus live — every lane's heartbeat, order pickup latency, stranded-work flags — so coordination health is itself a monitored surface.",
        "evidence": [
            ("control/README.md (the protocol)", blob("control/README.md")),
            ("control/inbox.md + control/status.md (the bus, live)", blob("control/status.md")),
            ("/process (this site — glossary)", "/process"),
        ],
    },
    {
        "id": "numbers",
        "q": "How do we know the numbers on this site are real?",
        "a": "Re-derive them. Every number is baked from the repo's committed record by generator scripts anyone can read and re-run (gen_snapshot.py parses git history and session cards; gen_fleet.py mirrors the fleet registry and heartbeats; gen_stats.py records its API calls and their failures). The deployed service is network-free at runtime — it physically cannot fetch anything, so it renders exactly the committed JSON, whose generation commit is stamped in the footer. Where data is missing the pages say so; tests assert the absence of invented values. The one honest caveat: baked numbers age, so every stats surface carries its as-of timestamp and banners when stale.",
        "evidence": [
            ("review/gen_snapshot.py", blob("review/gen_snapshot.py")),
            ("review/gen_fleet.py", blob("review/gen_fleet.py")),
            ("review/tests (honesty pinned)", f"{REPO_URL}/tree/main/review/tests"),
        ],
    },
    {
        "id": "walls",
        "q": "What can agents here verifiably NOT do?",
        "a": "The capability ledger keeps the honest list, each wall with its exact error text: direct api.github.com calls are proxy-blocked from session containers; branch deletion returns 403 on every path; some scheduled-session kinds cannot open PRs at all; sessions can be refused merging owner-gated PRs; Railway resource creation is policy-forbidden without the owner's go; and the deployed board runs on GitHub's anonymous 60-requests/hour ceiling until the owner mints a token. The ledger exists because the failure mode runs both ways — sessions also imagined walls that weren't there (a \"private\" repo that was public all along), so the discovery rule requires attempting once and recording the verbatim result before declaring anything impossible.",
        "evidence": [
            ("docs/CAPABILITIES.md (walls, verbatim errors, workarounds)", blob("docs/CAPABILITIES.md")),
        ],
    },
    {
        "id": "memory",
        "q": "Sessions are amnesiac — how does knowledge survive?",
        "a": "Nothing durable lives in a chat. Every session commits a card (its log), appends discoveries to the capability ledger, stamps decisions in a decision ledger, files ideas in a deduplicated backlog, and overwrites the heartbeat as its last act — so the next session reconstructs the entire state from the repo alone. This was tested for real: generation 1 wound down after the first day and generation 2 booted from main with no chat history, using committed succession docs. The strongest recorded finding from that handover: the orientation chain worked.",
        "evidence": [
            ("docs/succession/next-boot-2026-07-09.md", blob("docs/succession/next-boot-2026-07-09.md")),
            (".sessions/ (every session's card)", f"{REPO_URL}/tree/main/.sessions"),
            ("docs/CAPABILITIES.md (the discovery rule)", blob("docs/CAPABILITIES.md")),
        ],
    },
    {
        "id": "luck",
        "q": "Why believe this is safe-by-design rather than lucky-so-far?",
        "a": "Because the safety machinery has a track record of catching things, and that track record is inspectable. The gate leak was caught and is now regression-tested in both directions; the deploy-drift cell caught a silently stale service its first week; the scheduled healthcheck caught an upstream break on its second run ever; the time-bomb guard found 17 latent failures before they fired; overclaimed test results were caught pre-merge by the program's own review habits. None of that proves the absence of unknown failure modes — the honest claim is narrower: the failure modes that have occurred were caught by built machinery, documented with citations, and each produced a pinned test or a written rule. The problems page is the evidence that the reporting channel itself doesn't filter bad news.",
        "evidence": [
            ("/problems (this site)", "/problems"),
            ("tests/test_time_discipline.py (the meta-guard)", blob("tests/test_time_discipline.py")),
            ("docs/retro/ (every audit)", f"{REPO_URL}/tree/main/docs/retro"),
        ],
    },
    {
        "id": "weaknesses",
        "q": "What are the known weaknesses you have NOT fixed?",
        "a": "Honest list, current at this writing: the owner's attention is the scarcest resource and owner-gated asks queue for days; the fleet surfaces run tokenless on an anonymous rate ceiling; routine-fired (cron) sessions remain unreliable landers, so the self-scheduling chain is the only consistent unattended producer; the lane registry is parsed out of another repo's script internals (a generated lanes.json has been requested but not yet shipped); hand-kept lists keep drifting against globbable truth — the same failure shape found three times; and cross-repo visibility depends on lanes keeping their heartbeat grammar, which some don't (this site's fleet mirror shows exactly which). Each of these is tracked as a backlog item, an owner ask, or a standing flag rather than being quietly absorbed.",
        "evidence": [
            ("docs/ideas/backlog.md (the tracked gaps)", blob("docs/ideas/backlog.md")),
            ("control/status.md (standing flags, live)", blob("control/status.md")),
            ("/fleet (this site — which lanes' data is missing, labeled)", "/fleet"),
        ],
    },
    {
        "id": "why-fast",
        "q": "Where did the speed actually come from?",
        "a": "Not from skipping checks — the gate got harder while the pace held. Four mechanisms, each visible in the record: merge-is-deploy (a green required check is the whole distance to production); parallel lanes on a conflict-free bus (one writer per file, so parallel lanes never block each other); unattended chains that schedule their own successors and land one verified slice per wake; and paying discovery cost once (every wall's workaround is a committed fact the next session starts from). The growth page shows the test-count curve growing alongside the PR curve — the counterweight is the point.",
        "evidence": [
            ("/growth (this site)", "/growth"),
            ("docs/retro/gen1-final-retro-2026-07-09.md (the 46-PR day, honestly)", blob("docs/retro/gen1-final-retro-2026-07-09.md")),
        ],
    },
]


def overview_stats(snapshot_data: dict[str, Any]) -> list[dict[str, Any]]:
    totals = snapshot_data.get("totals") or {}
    tiles = []
    for key, label, sub in STAT_TILES:
        value = totals.get(key)
        if value is None:
            continue  # honest absence — no tile without a real number
        tiles.append({"key": key, "label": label, "sub": sub, "value": value})
    return tiles


# --------------------------------------------------------------------------- #
# ORDER 019 PR2 — /questions ledger filter/sort/search over the centralized
# listfilter core (review/listfilter.py, a byte-identical vendored copy of
# app/listfilter.py). The ledger records carry ``asked``/``title``/``url``/
# ``status``/``answer_url``/``answer_label`` (see data/questions.json + the
# template) — the dimensions read exactly those fields, defaulting the same
# way the template does (missing status renders as "open").
# --------------------------------------------------------------------------- #


def question_status(q: dict[str, Any]) -> str:
    """A ledger record's status, defaulting to ``open`` exactly like the
    template's ``q.status or "open"``."""
    return str(q.get("status") or "open")


def question_answer_state(q: dict[str, Any]) -> str:
    """``answered`` when an answer link exists, else ``pending`` — the same
    reading the template renders in its "Answered where" column."""
    return "answered" if q.get("answer_url") else "pending"


def unanswered_closed(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ledger records whose issue closed without a published answer link.

    The bake sync flips ``status`` to ``closed`` from the live issue state,
    but answer links stay hand-written — so a question can close without its
    promised published answer. These records are that broken promise, read
    straight off the committed ledger (no network, never fabricated)."""
    return [
        q
        for q in records
        if question_status(q) == "closed" and question_answer_state(q) == "pending"
    ]


QUESTIONS_FILTER_SPEC = listfilter.ListSpec(
    path="/questions",
    dimensions=(
        listfilter.Dimension(
            key="status", label="status",
            get=lambda q: [question_status(q)],
        ),
        listfilter.Dimension(
            key="answer", label="answer", values=("answered", "pending"),
            get=lambda q: [question_answer_state(q)],
        ),
    ),
    sorts=(
        # ``ledger`` keeps the committed file's own order — the default, so a
        # no-param /questions renders exactly as before.
        listfilter.SortOption("ledger", "ledger order"),
        listfilter.SortOption(
            "newest", "newest asked",
            sort_key=lambda q: str(q.get("asked") or ""), reverse=True,
        ),
        listfilter.SortOption(
            "oldest", "oldest asked",
            sort_key=lambda q: str(q.get("asked") or ""),
        ),
    ),
    search=lambda q: " ".join(
        str(q.get(k) or "") for k in ("title", "status", "answer_label")
    ),
)
